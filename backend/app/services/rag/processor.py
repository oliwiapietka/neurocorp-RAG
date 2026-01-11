import io
import base64
import logging
from typing import Optional, Tuple
from PIL import Image

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from langchain_core.messages import HumanMessage

from .factory import model_factory

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """
    Handles PDF parsing using Docling and generates 
    multimodal descriptions via Vision-LLM (VLM) captioning.
    """
    def __init__(self):
        # Docling Configuration
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True
        pipeline_options.images_scale = 2.0  # Better quality for VLM
        pipeline_options.generate_page_images = True

        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
        
        # Singleton Model Factory
        self.models = model_factory

    async def generate_caption(self, image: Image.Image, context_text: str = "") -> str:
        """
        Generates image caption using Groq Vision LLM with Contextual Retrieval.
        """
        try:
            # Convert Image to Base64
            buffered = io.BytesIO()
            image.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            img_url = f"data:image/jpeg;base64,{img_str}"

            # Contextual Prompting
            prompt_text = (
                "Analyze this image in detail. "
                "Focus on data, charts, and text visible in the image. "
            )
            if context_text:
                # Truncate context to avoid token overflow, keep last ~600 chars
                safe_ctx = context_text[-600:]
                prompt_text += f"\nCONTEXT FROM DOCUMENT: The surrounding text says: '...{safe_ctx}'. "
                prompt_text += "Use this context to interpret the image accurately."

            # Async Call to Groq via LangChain
            message = HumanMessage(
                content=[
                    {"type": "text", "text": prompt_text},
                    {"type": "image_url", "image_url": {"url": img_url}},
                ]
            )
            
            response = await self.models.vision_llm.ainvoke([message])
            return response.content

        except Exception as e:
            logger.error(f"VLM Caption Error: {e}")
            return "Image containing visual data."

    def process_element(self, element, doc) -> Tuple[Optional[Image.Image], Optional[int]]:
        """
        Extracts valid images/tables, filtering out noise (icons/logos).
        Returns: (PIL Image, Page Number)
        """
        el_type = str(type(element))
        is_image = "PictureItem" in el_type
        is_table = "TableItem" in el_type
        
        if is_image or is_table:
            try:
                pil_img = element.get_image(doc)
                if pil_img:
                    # Filter noise: tiny icons, logos
                    if pil_img.width < 120 or pil_img.height < 120:
                        return None, None
                    
                    p_no = 1
                    if element.prov and len(element.prov) > 0:
                        p_no = element.prov[0].page_no
                    
                    return pil_img.convert("RGB"), p_no
            except Exception as e:
                logger.warning(f" Failed to process graphic element: {e}")
        
        return None, None