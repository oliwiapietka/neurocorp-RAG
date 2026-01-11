import logging
import asyncio
from typing import List, Optional, Dict

from fastapi import UploadFile

from app.database.session_db import session_repo
from app.schemas.chat import SourceMetadata, ChatResponse, ImageResult
from app.services.rag.engine import RAGEngine

logger = logging.getLogger(__name__)

class ChatOrchestrator:
    """
    Main controller for the chat lifecycle, managing the flow between user input,
    document retrieval (RAG), external web searching, and response generation.

    This class serves as the 'brain' of the application, deciding whether to 
    rely on internal document storage or trigger a web search fallback based 
    on the quality of retrieved data.
    """
    def __init__(self, rag_engine: RAGEngine, agent_service, web_search_service=None):
        self.rag = rag_engine
        self.agent = agent_service
        self.web_search = web_search_service

    async def process_chat(self, session_id: str, message: str, files: Optional[List[UploadFile]] = None) -> ChatResponse:
        """
        Processes a single chat turn: handling file uploads, performing multimodal search,
        orchestrating fallback logic and generating the final AI response.

        Args:
            session_id: Unique identifier for the current conversation.
            message: The raw text input from the user.
            files: Optional list of files to be indexed into the session context.

        Returns:
            A ChatResponse object containing the generated text, UI citations, 
            and relevant images.
        """
        if not session_id or session_id in ["null", "undefined"]:
            return ChatResponse(response="Session error. Please refresh the page.", citations=[], images=[])

        try:
            history = await session_repo.get_history(session_id, limit=3)

            # files uploaded
            if files:
                save_tasks = [self.rag.storage.save_upload_file(f) for f in files]
                safe_names = await asyncio.gather(*save_tasks)
                formatted_files = [
                    {"safe_name": sn, "original_name": f.filename} 
                    for sn, f in zip(safe_names, files)
                ]
                await self.rag.index_documents(formatted_files, session_id)

            # query rewrite
            search_query = await self.agent.rewrite_query(message, history)

            # myltimodal search
            text_results, vision_results = await asyncio.gather(
                self.rag.search(search_query, session_id),
                self.rag.search_vision(search_query, session_id)
            )

            # Filter and rank results to ensure high quality
            final_text_results = self._apply_safety_net_strategy(text_results)

            # check score
            top_score = final_text_results[0].get("rerank_score", 0) if final_text_results else 0
            
            citations = []
            images_list_dict = []
            source_type = "db"
            final_context = []

            # routing
            is_db_sufficient = top_score > 0.15 or len(vision_results) > 0

            if not is_db_sufficient and self.web_search:
                logger.info(f" Weak DB context (Score: {top_score:.3f}). Fallback to Web Search.")
                web_raw = await self.web_search.search(search_query)
                citations = self._map_citations(web_raw, "web")
                final_context = [{"text": c.snippet, "id": c.id, "source": c.filename} for c in citations]
                source_type = "web"
            else:
                # citations
                citations = self._map_citations(final_text_results, "db")
                
                # context for llm
                final_context = [
                    {
                        "text": res.get("text", ""),
                        "id": res.get("filename", "unknown"),
                        "source": res.get("original_name", "doc"),
                        "page": res.get("page_no", 1)
                    } 
                    for res in final_text_results
                ]
                
                # aggregate related images
                images_list_dict = await self._resolve_images(search_query, final_text_results, vision_results)

            # generate res
            ai_text = await self.agent.generate_response(
                user_query=message, 
                context_list=final_context,
                image_list=images_list_dict, 
                history=history, 
                source_type=source_type
            )

            await session_repo.add_message(session_id, "user", message)
            await session_repo.add_message(session_id, "ai", ai_text, citations=[c.model_dump() for c in citations])

            return ChatResponse(
                response=ai_text, 
                citations=citations, 
                images=[ImageResult(**img) for img in images_list_dict]
            )

        except Exception as e:
            logger.error(f" Orchestrator Error: {e}", exc_info=True)
            return ChatResponse(response="A system error occurred.", citations=[], images=[])
        
    def _apply_safety_net_strategy(self, results: List[Dict]) -> List[Dict]:
        """
        Filters results returned by the RAGEngine.
        Strategy: Retain the TOP 15 results (unless they are noise), 
        and keep additional results only if they exceed the minimum score threshold.
        """
        if not results: return []
        
        filtered = []
        ALWAYS_KEEP = 15
        MIN_SCORE_EXTRA = 0.01
        HARD_CUTOFF = 0.000001

        for i, res in enumerate(results):
            score = res.get("rerank_score", 0)
            
            if score < HARD_CUTOFF: continue

            if i < ALWAYS_KEEP:
                filtered.append(res)
            elif score > MIN_SCORE_EXTRA:
                filtered.append(res)
            
            if len(filtered) >= 25: break
        
        return filtered

    async def _resolve_images(self, query: str, text_hits: List[Dict], vision_hits: List[Dict]) -> List[Dict]:
        images_map = {}
        layout_candidates = set()

        # Semantic Hits
        for img in vision_hits:
            if img.get("rerank_score", 0) > 0.15:
                images_map[img["uuid_name"]] = {
                    "uuid_name": img["uuid_name"],
                    "original_doc": img.get("original_doc"),
                    "score": img.get("rerank_score"),
                    "caption": img.get("caption", ""),
                    "context_info": img.get("context_info", ""),
                    "reason": "semantic_match"
                }

        TOP_LAYOUT_CHECK = 3

        for hit in text_hits[:TOP_LAYOUT_CHECK]:
            for img_uuid in hit.get("related_images", []):
                if img_uuid not in images_map:
                    layout_candidates.add(img_uuid)

        # verify layout candidates
        if layout_candidates:
            verified_scores = await self.rag.retrieval.score_layout_images(query, list(layout_candidates))
            
            for uuid, score in verified_scores.items():
                if score > 0.35:
                    meta = await self.rag.get_image_metadata(uuid)
                    
                    images_map[uuid] = {
                        "uuid_name": uuid,
                        "original_doc": meta.get("original_doc"),
                        "caption": meta.get("caption", "context"),
                        "score": round(score, 3),
                        "reason": "layout_relation_verified"
                    }
                else:
                    logger.info(f" Discarded layout image {uuid} (Score: {score:.3f}) - visual mismatch.")

        # final sorting by score
        final_list = list(images_map.values())
        final_list.sort(key=lambda x: x["score"], reverse=True)
        
        return final_list

    def _map_citations(self, results: list, source_type: str) -> list:
        """
        Formats search results into a standardized citation structure for the UI.
        Handles both database documents and web search results.
        """
        citations = []
        seen = set()
        cid = 1
        
        for res in results:
            if source_type == "db":
                name = res.get("original_name", "document")
                uuid = res.get("filename", "unknown")
                key = (name, uuid)
                
                if key in seen: continue
                seen.add(key)
                
                citations.append(SourceMetadata(
                    id=cid,
                    filename=name,
                    uuid_name=uuid,
                    page=res.get("page_no", 1),
                    snippet=res.get("text", "")[:300],
                    type="db",
                    is_global=False,
                    url=f"/api/files/{uuid}"
                ))
            else:
                url = res.get("url") or res.get("link", "")
                if not url:
                    continue
                if url in seen: 
                    continue
                seen.add(url)
                snippet = (res.get("content") or "").strip()
                citations.append(SourceMetadata(
                    id=cid,
                    filename=res.get("title", "Web"),
                    uuid_name=f"web:{cid}",
                    page=0,
                    snippet=snippet[:300],
                    type="web",
                    is_global=False,
                    url=url
                ))
            cid += 1
        return citations