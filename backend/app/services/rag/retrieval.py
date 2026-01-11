import asyncio
import logging
from typing import List, Dict, Any
import torch
from qdrant_client import models

from app.core.config import settings
from .vector_store import VectorStoreService
from .models.embeddings import EmbeddingService

logger = logging.getLogger(__name__)

class RetrievalService:
    """
    Handles Hybrid Search (Dense+Sparse) and Multimodal Search (CLIP+Text).
    Implements Reciprocal Rank Fusion (RRF) and Cross-Encoder Reranking 
    to provide highly accurate context retrieval for the RAG pipeline.
    """
    def __init__(self, 
                 vector_store: VectorStoreService, 
                 embedding_service: EmbeddingService,
                 model_factory,
                 executor):
        self.vector_store = vector_store
        self.embedder = embedding_service
        self.models = model_factory
        self.executor = executor

    # TEXT SEARCH (Hybrid: Dense + Sparse + RRF + Rerank)
    async def search_text(self, query: str, session_id: str) -> List[Dict[str, Any]]:
        # Embed Query (Parallel Dense & Sparse)
        d_vec, s_res = await asyncio.gather(
            self.embedder.get_embeddings(query, mode="text"),
            self.embedder.get_sparse_embedding([query])
        )

        # Prepare Prefetch (Search Strategy)
        prefetch = [
            models.Prefetch(
                query=d_vec, 
                using="dense", 
                limit=settings.TEXT_RETRIEVAL_WINDOW
            )
        ]
        
        # Add Sparse if available
        if s_res and len(s_res) > 0:
            s_vec = models.SparseVector(
                indices=s_res[0].indices.tolist(), 
                values=s_res[0].values.tolist()
            )
            prefetch.append(models.Prefetch(
                query=s_vec, 
                using="sparse", 
                limit=settings.TEXT_RETRIEVAL_WINDOW
            ))

        # Query DB with RRF Fusion
        points = await self.vector_store.query_hybrid(
            self.vector_store.text_collection, 
            prefetch, 
            session_id, 
            settings.TEXT_RETRIEVAL_WINDOW
        )

        # Map Results
        raw_results = [{
            "text": p.payload.get("text", ""),
            "page_no": p.payload.get("page_no", 1),
            "original_name": p.payload.get("original_name"),
            "filename": p.payload.get("filename"),
            "related_images": p.payload.get("related_images", []),
            "vector_score": p.score, # RRF score from Qdrant
            "id": p.id
        } for p in points]

        # Cross-Encoder Reranking
        return await self._rerank(query, raw_results, text_key="text")

    # VISION SEARCH (Multimodal: CLIP + Text + RRF + Visual Guardrail)
    async def search_vision(self, query: str, session_id: str, limit: int = 3) -> List[Dict[str, Any]]:
        # Embed Query (Parallel CLIP & Dense)
        clip_vec, text_vec = await asyncio.gather(
            self.embedder.get_embeddings(query, mode="vision"),
            self.embedder.get_embeddings(query, mode="text")
        )

        # Prefetch (Visual vector + Semantic Text vector)
        prefetch = [
            models.Prefetch(query=clip_vec, using="image", limit=settings.VISION_LIMIT_IMAGE),
            models.Prefetch(query=text_vec, using="text", limit=settings.VISION_LIMIT_TEXT),
        ]

        # Query DB with RRF Fusion
        points = await self.vector_store.query_hybrid(
            self.vector_store.vision_collection, 
            prefetch, 
            session_id, 
            settings.VISION_RETRIEVAL_WINDOW
        )

        if not points:
            return []
        
        raw_data = []
        pairs_caption = [] # Is visual match
        pairs_context = [] # Is textual context match

        for p in points:
            caption = p.payload.get('caption', '').strip()
            context = p.payload.get('context_info', '').strip()
            
            raw_data.append({
                "uuid_name": p.payload["uuid_name"],
                "caption": caption,
                "context_info": context,
                "original_doc": p.payload.get("original_doc"),
                "page_no": p.payload.get("page_no"),
            })

            pairs_caption.append([query, caption])
            pairs_context.append([query, context])

        # Dual Inference
        try:
            def _dual_score():
                scores_cap = self.models.reranker.predict(
                    pairs_caption, activation_fct=torch.nn.Sigmoid(),
                    batch_size=settings.RERANK_BATCH_SIZE, show_progress_bar=False
                )
                scores_ctx = self.models.reranker.predict(
                    pairs_context, activation_fct=torch.nn.Sigmoid(),
                    batch_size=settings.RERANK_BATCH_SIZE, show_progress_bar=False
                )
                return scores_cap, scores_ctx

            scores_visual, scores_context = await asyncio.get_running_loop().run_in_executor(
                self.executor, _dual_score
            )

            # Fusion & Filter
            final_results = []
            VISUAL_THRESHOLD = 0.15 
            WEIGHT_VISUAL = 0.65     
            WEIGHT_CONTEXT = 0.35    

            for i, data in enumerate(raw_data):
                s_vis = float(scores_visual[i])
                s_ctx = float(scores_context[i])

                if s_vis < VISUAL_THRESHOLD:
                    continue 

                final_score = (s_vis * WEIGHT_VISUAL) + (s_ctx * WEIGHT_CONTEXT)
                data["rerank_score"] = final_score
                
                final_results.append(data)

            final_results.sort(key=lambda x: x["rerank_score"], reverse=True)
            return final_results[:limit]

        except Exception as e:
            logger.error(f"Vision Rerank failed: {e}")
            return []

    # HELPER: GENERIC RERANKER
    async def _rerank(self, query: str, results: List[Dict], text_key: str = "text") -> List[Dict]:
        if not results: return []
        
        # Deduplication
        seen = set()
        unique_results = []
        pairs = []

        for r in results:
            content = (r.get(text_key) or "").strip()
            if not content: continue
            h = hash(content)
            if h not in seen:
                seen.add(h)
                unique_results.append(r)
                pairs.append([query, content])

        if not pairs: return []

        try:
            scores = await asyncio.get_running_loop().run_in_executor(
                self.executor,
                lambda: self.models.reranker.predict(
                    pairs, 
                    activation_fct=torch.nn.Sigmoid(),
                    batch_size=settings.RERANK_BATCH_SIZE, 
                    show_progress_bar=False
                )
            )
            for i, score in enumerate(scores):
                unique_results[i]["rerank_score"] = float(score)
            
            unique_results.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)
            return unique_results
        
        except Exception as e:
            logger.error(f"Rerank failed: {e}")
            # Fallback to vector score if Cross-Encoder fails
            results.sort(key=lambda x: x.get("vector_score", 0), reverse=True)
            return results

    async def get_image_metadata(self, uuid_name: str):
        p = await self.vector_store.scroll_by_id(self.vector_store.vision_collection, "uuid_name", uuid_name)
        if p:
            return {
                "caption": p.payload.get("caption"),
                "original_doc": p.payload.get("original_doc"),
                "page_no": p.payload.get("page_no")
            }
        return {"caption": "N/A", "original_doc": "N/A"}
    
    async def score_layout_images(self, query: str, image_uuids: List[str]) -> Dict[str, float]:
        """
        Verifies if images found through document layout proximity (spatial search) 
        actually match the user's query. Returns a mapping of {uuid: score}.
        """
        if not image_uuids: return {}

        # get metadata for all UUIDs at once
        try:
            points_result = await self.vector_store.client.scroll(
                collection_name=self.vector_store.vision_collection,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="uuid_name", 
                            match=models.MatchAny(any=image_uuids)
                        )
                    ]
                ),
                limit=len(image_uuids),
                with_payload=True,
                with_vectors=False
            )
            points = points_result[0]
        except Exception as e:
            logger.error(f"Layout Verification Scroll Error: {e}")
            return {}

        if not points: return {}

        pairs = []
        uuid_map = []

        for p in points:
            caption = p.payload.get("caption", "")
            if caption:
                pairs.append([query, caption])
                uuid_map.append(p.payload["uuid_name"])

        if not pairs: return {}

        # Batch Inference
        try:
            scores = await asyncio.get_running_loop().run_in_executor(
                self.executor,
                lambda: self.models.reranker.predict(
                    pairs, activation_fct=torch.nn.Sigmoid(),
                    batch_size=settings.RERANK_BATCH_SIZE, show_progress_bar=False
                )
            )
        except Exception as e:
            logger.error(f"Layout Rerank Error: {e}")
            return {}

        results = {}
        for i, uuid in enumerate(uuid_map):
            results[uuid] = float(scores[i])

        return results