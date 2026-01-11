import os
import uuid
import asyncio
import logging
import concurrent.futures
from typing import List, Dict
from urllib.parse import quote

from qdrant_client import models

from app.core.config import settings
from .processor import DocumentProcessor
from .vector_store import VectorStoreService
from .storage import StorageService
from .models.embeddings import EmbeddingService

logger = logging.getLogger(__name__)

class IngestionPipeline:
    """
    Orchestrates the document processing lifecycle: parsing PDFs, 
    extracting visual elements, generating multimodal captions, 
    and indexing both text and images into VectorDB.
    """
    def __init__(self, 
                 vector_store: VectorStoreService, 
                 storage: StorageService, 
                 embedding_service: EmbeddingService,
                 processor: DocumentProcessor,
                 executor: concurrent.futures.ThreadPoolExecutor):
        
        self.vector_store = vector_store
        self.storage = storage
        self.embedder = embedding_service
        self.processor = processor
        self.executor = executor
        
        self.semaphore = asyncio.Semaphore(settings.INGESTION_SEMAPHORE)

    async def run(self, file_data: List[Dict], target_id: str) -> Dict[str, int]:
        """
        Main entry point for batch document ingestion.
        
        Args:
            file_data: List of file metadata (safe_name, original_name).
            target_id: The session or user ID for multi-tenancy filtering.
        """        
        tasks = []
        for d in file_data:
            async def _sem_task(doc):
                async with self.semaphore:
                    return await self._process_single_file(doc, target_id)
            tasks.append(_sem_task(d))
        
        res = await asyncio.gather(*tasks)
        return {
            "chunks_added": sum(r["chunks"] for r in res),
            "images_added": sum(r["images"] for r in res)
        }

    async def _process_single_file(self, file_meta: Dict, target_id: str) -> Dict[str, int]:
        """
        Processes an individual file through extraction, VLM analysis, and ingestion.
        """
        safe_name = str(file_meta.get("safe_name", ""))
        orig_name = str(file_meta.get("original_name", "Document")).strip("{} ")
        temp_path = settings.UPLOAD_DIR / f"{uuid.uuid4()}_{safe_name}"
        
        raw_text_pages = []
        vision_elements = []
        page_to_images = {}

        try:
            # Download
            await self.storage.download_file(safe_name, temp_path)

            # Extract
            def _extract_task():
                res = self.processor.converter.convert(temp_path)
                return list(res.document.iterate_items()), res.document
            
            doc_items, doc_obj = await asyncio.get_running_loop().run_in_executor(
                self.executor, _extract_task
            )

            # Analyze Structure & Context
            current_page_text = ""
            last_page = 1
            last_hd = f"Document: {orig_name}"
            context_buf = []

            for element, _ in doc_items:
                p_no = element.prov[0].page_no if element.prov else last_page
                
                # Flush text on page change
                if p_no != last_page:
                    if current_page_text.strip():
                        raw_text_pages.append({"text": current_page_text, "p_no": last_page})
                    current_page_text, context_buf = "", []
                    last_page = p_no

                if "Heading" in str(type(element)): 
                    last_hd = element.text.strip()

                # Process Vision
                pil_img, _ = self.processor.process_element(element, doc_obj)
                
                if pil_img:
                    img_uuid = f"crop_{uuid.uuid4()}.jpg"
                    
                    # Context Window Logic
                    raw_context = " ".join(context_buf[-3:])
                    surrounding_text = raw_context[-settings.MAX_CONTEXT_LEN:] if len(raw_context) > settings.MAX_CONTEXT_LEN else raw_context
                    if len(surrounding_text) == settings.MAX_CONTEXT_LEN and " " in surrounding_text:
                        surrounding_text = surrounding_text.split(" ", 1)[1]

                    ctx_full = f"Section Header: {last_hd}. Surrounding Text: ...{surrounding_text}"
                    
                    try:
                        caption = await self.processor.generate_caption(pil_img, context_text=ctx_full)
                    except Exception as e:
                        logger.warning(f"VLM Caption failed: {e}")
                        caption = "Image extracted from document."

                    vision_elements.append({
                        "img": pil_img, "caption": caption, "p_no": p_no, 
                        "ctx": ctx_full, "uuid": img_uuid
                    })
                    
                    if p_no not in page_to_images: page_to_images[p_no] = []
                    page_to_images[p_no].append(img_uuid)
                
                # Accumulate Text
                if hasattr(element, 'text') and element.text.strip():
                    txt = element.text.strip()
                    if pil_img: txt = f"[Text from graphic]: {txt}"
                    current_page_text += txt + "\n\n"
                    context_buf.append(txt)
                    if len(context_buf) > 10: context_buf.pop(0)

            if current_page_text.strip():
                raw_text_pages.append({"text": current_page_text, "p_no": last_page})

            # Ingest Parallel
            results = await asyncio.gather(
                self._ingest_text(raw_text_pages, orig_name, safe_name, target_id, page_to_images),
                self._ingest_vision(vision_elements, orig_name, target_id)
            )
            return {"chunks": results[0], "images": results[1]}

        except Exception as e:
            logger.exception(f"Ingestion Pipeline Error ({orig_name}): {e}")
            return {"chunks": 0, "images": 0}
        finally:
            if os.path.exists(temp_path): os.remove(temp_path)

    async def _ingest_text(self, pages: List[Dict], orig_name, safe_name, target_id, page_to_images) -> int:
        """
        Chunks text, links spatial visual references, and performs hybrid vector indexing.
        """
        prepared_points_data = []
        texts_to_embed = []
        
        full_text = ""
        page_map = [] 
        current_idx = 0
        
        # Merge & Map
        for pg in pages:
            text = pg["text"]
            full_text += text + "\n\n"
            end_idx = current_idx + len(text) + 2
            page_map.append({"start": current_idx, "end": end_idx, "p_no": pg["p_no"]})
            current_idx = end_idx

        chunks = self.embedder.split_text(full_text)

        for chunk_text in chunks:
            # Reverse map chunk to page
            found_p_no = 1
            chunk_start = full_text.find(chunk_text[:100])
            if chunk_start != -1:
                for pm in page_map:
                    if pm["start"] <= chunk_start < pm["end"]:
                        found_p_no = pm["p_no"]
                        break
            
            # Link nearby images
            nearby = []
            for p in [found_p_no - 1, found_p_no, found_p_no + 1]:
                nearby.extend(page_to_images.get(p, []))
            nearby = list(set(nearby))

            search_text = f"Document: {orig_name} | Page: {found_p_no}\n\n{chunk_text}"
            if nearby:
                img_refs = ", ".join([f"[IMG:{u[:8]}]" for u in nearby])
                search_text += f"\n\n[Related images: {img_refs}]"

            payload = {
                "text": chunk_text, "search_text_dump": search_text,
                "page_no": found_p_no, "session_id": target_id,
                "original_name": orig_name, "filename": quote(safe_name),
                "related_images": nearby, "type": "text_chunk"
            }
            prepared_points_data.append(payload)
            texts_to_embed.append(search_text)

        if not prepared_points_data: return 0

        # Batch Embed & Upsert
        all_points = []
        batch_size = settings.TEXT_BATCH_SIZE
        
        for i in range(0, len(texts_to_embed), batch_size):
            b_txt = texts_to_embed[i : i + batch_size]
            b_pay = prepared_points_data[i : i + batch_size]

            # Parallel Embeddings
            d_vecs, s_vecs = await asyncio.gather(
                self.embedder.get_embeddings(b_txt, mode="text"),
                self.embedder.get_sparse_embedding(b_txt)
            )

            for j, p_data in enumerate(b_pay):
                all_points.append(models.PointStruct(
                    id=str(uuid.uuid4()),
                    vector={
                        "dense": d_vecs[j],
                        "sparse": models.SparseVector(
                            indices=s_vecs[j].indices.tolist(), 
                            values=s_vecs[j].values.tolist()
                        )
                    },
                    payload=p_data
                ))

        await self.vector_store.upsert(self.vector_store.text_collection, all_points)
        return len(all_points)

    async def _ingest_vision(self, elements: List[Dict], orig_name, target_id) -> int:
        """
        Uploads visual crops to storage and indexes visual + textual features for images.
        """
        if not elements: return 0
        all_points = []
        
        # Batch Generator Helper
        def _batches(l, n):
            for i in range(0, len(l), n): yield l[i:i + n]

        for batch in _batches(elements, settings.VISION_BATCH_SIZE):
            imgs = [el["img"] for el in batch]
            caps = [el["caption"] for el in batch]
            
            # Parallel Embeddings
            i_vecs, c_vecs = await asyncio.gather(
                self.embedder.get_embeddings(imgs, mode="vision"),
                self.embedder.get_embeddings(caps, mode="text")
            )
            
            # Parallel Storage Upload
            upload_tasks = [
                self.storage.upload_image(el["img"], el["uuid"], {"doc": orig_name}) 
                for el in batch
            ]
            await asyncio.gather(*upload_tasks)

            # Build Points
            for i, el in enumerate(batch):
                all_points.append(models.PointStruct(
                    id=str(uuid.uuid4()),
                    vector={"image": i_vecs[i], "text": c_vecs[i]},
                    payload={
                        "uuid_name": el["uuid"], "caption": el["caption"],
                        "page_no": el["p_no"], "original_doc": orig_name,
                        "session_id": target_id, "context_info": el["ctx"], 
                        "type": "vision_element"
                    }
                ))
            
            await self.vector_store.upsert(self.vector_store.vision_collection, all_points[-len(batch):])

        return len(all_points)