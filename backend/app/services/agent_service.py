import logging
from typing import List, Dict, Any, AsyncGenerator
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.language_models import BaseChatModel
from app.core.config import settings

logger = logging.getLogger(__name__)

class AgentService:
    def __init__(self):
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY must be set in .env")

        self.llm: BaseChatModel = ChatGroq(
            temperature=0.1, # Low temperature = higher precision
            model_name=settings.MODEL_NAME,
            api_key=settings.GROQ_API_KEY.get_secret_value(),
            request_timeout=45.0,
            max_retries=3
        )

    def _build_prompt(self, user_query: str, context_list: List[Dict[str, Any]], 
                  image_list: List[Dict[str, Any]] = None, 
                  history: List[Dict[str, Any]] = None,
                  source_type: str = "db") -> List[Any]:
    

        persona = "Senior Analyst" if source_type == "db" else "Research Assistant"
        
        system_instruction = f"""You are a {persona} at NeuroCorp. Your operating system is Multimodal-RAG-v2.

    FORMATTING RULES (For "cleaner" responses):
    - Use **bold** for key concepts.
    - If listing several facts, use bullet points.
    - Maintain double line breaks between paragraphs.
    - If you have no textual data, start with: "Documentation analysis did not reveal textual mentions, however, significant visual resources were found:"

    MULTIMODAL RULES:
    1. Knowledge comes from the sections: <context> (text) and <images> (image descriptions).
    2. If there is a description in <images> matching the question, you ARE OBLIGATED to reference that image.
    3. If the <images> list contains the text "No images available", NEVER insert any image, even if you see one in the conversation history.
    4. Ignore images from previous messages (history) unless their identifiers are repeated in the current <images> section.
    5. IMAGE FORMAT: ![short description](UUID). 
    - In the 'UUID' placeholder, insert the specific identifier (e.g., crop_550.jpg) from the <images> section.
    - NEVER use curly braces {{}} or the word 'uuid' in parentheses. Use the raw identifier.

    CITATION AND LOGIC RULES:
    - If a document contains keywords but provides no substantive answer - OMIT IT.
    - After every sentence, add the document number in square brackets, e.g., [1].
    - If the same information is in multiple sources, list them all: [1, 2].
    - Promote source diversity in your response.
    - Do not write the document name/location; provide the answer itself.
    """

        # BUILDING DATA BLOCKS
        images_str = "AVAILABLE VISUAL RESOURCES (Use UUID as a link in format ![description](UUID)):\n"
        if image_list:
            for img in image_list:
                uuid_val = img.get('uuid_name', 'no_id')
                caption = img.get('caption')
                ctx = img.get('context_info', 'No context')
                images_str += f"- UUID: {uuid_val} | Description: {caption} | Location: {ctx}\n"
        else:
            images_str += "No images available.\n"

        context_str = ""
        if context_list:
            for i, ctx in enumerate(context_list, 1):
                content = ctx.get('text') or ctx.get('snippet') or ""
                # Add filename
                source_name = ctx.get('original_name') or ctx.get('source') or f"Document {i}"
                context_str += f"<doc id='{i}' source='{source_name}'>\n{content}\n</doc>\n\n"
        else:
            context_str = "NO TEXTUAL DATA AVAILABLE."

        # ASSEMBLING MESSAGES
        messages = [SystemMessage(content=system_instruction)]

        if history:
            # Pass history so rewrite_query makes sense
            for msg in history[-6:]:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "ai":
                    messages.append(AIMessage(content=msg["content"]))

        # Final message with injected context
        user_input_with_context = f"""
    <images>
    {images_str}
    </images>

    <context>
    {context_str}
    </context>

    USER QUESTION: {user_query}
    """
        messages.append(HumanMessage(content=user_input_with_context))

        return messages

    async def generate_response(self, user_query: str, context_list: List[Dict[str, Any]], 
                                image_list: List[Dict[str, Any]] = None, 
                                history: List[Dict[str, Any]] = None,
                                source_type: str = "db") -> str:
        """Full textual response."""
        try:
            messages = self._build_prompt(user_query, context_list, image_list, history, source_type)
            response = await self.llm.ainvoke(messages)
            return str(response.content)
        except Exception as e:
            logger.error(f" Agent Invoke Error: {e}")
            return "I'm sorry, an error occurred while generating the response."

    async def grade_relevance(self, user_query: str, context_list: List[Dict[str, Any]]) -> bool:
        """LLM Grader: Decides if textual documents are useful."""
        if not context_list: return False
        
        ctx_sample = "\n".join([c.get('text', '')[:200] for c in context_list[:3]])
        prompt = (
            "You are a RAG judge. Does the text below contain the answer to the question? "
            "Return ONLY 'YES' or 'NO'."
        )
        
        try:
            res = await self.llm.ainvoke([
                SystemMessage(content=prompt),
                HumanMessage(content=f"Q: {user_query}\nCTX: {ctx_sample}")
            ])
            return "YES" in str(res.content).upper()
        except:
            return True  

    async def rewrite_query(self, user_query: str, history: List[Dict[str, Any]]) -> str:
        """
        Transforms an imprecise user question into a standalone 
        search query based on the conversation context.
        """
        # If no history, there's no context to pull from - return original
        if not history:
            return user_query
        
        # Prepare short history for the LLM (last 3 exchanges)
        context_history = ""
        for msg in history[-3:]:
            role = "User" if msg["role"] == "user" else "AI"
            context_history += f"{role}: {msg['content']}\n"

        # Prompt for Rewriter
        system_prompt = """You are a Query Rewriting expert in a RAG system. 
Your task is to transform the user's last question into a precise, standalone search query for a vector database.

RULES:
1. Return ONLY the query, MAX 15 words.
2. Never add explanations like "because...", "no information found..." or meta-comments.
- If the question refers to previous topics (e.g., "how much?", "why him?", "when was that?"), supplement it with missing proper names and facts from the history.
- If the question is already precise, return it unchanged.
- If the user changes the topic drastically (unrelated topics), your query should focus solely on the new topic, ignoring history.
- Use only keywords/phrases.
"""

        user_prompt = f"""CONVERSATION HISTORY:
{context_history}

USER'S LAST QUESTION: {user_query}

MODIFIED QUERY:"""

        try:
            # LLM Call (temperature 0 for stability)
            response = await self.llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])
            
            rewritten_query = str(response.content).strip()
            
            # log
            if rewritten_query.lower() != user_query.lower():
                logger.info(f" Query Rewrite: '{user_query}' -> '{rewritten_query}'")
            
            return rewritten_query

        except Exception as e:
            logger.error(f" Error during rewrite_query: {e}")
            return user_query

agent_service = AgentService()