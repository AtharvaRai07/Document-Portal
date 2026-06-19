import os
import sys
from langchain_core.output_parsers import JsonOutputParser
from langchain_classic.output_parsers import OutputFixingParser
from utils.models_loader import ModelLoader
from prompts.prompt_library import PROMPT_REGISTRY
from models.models import *

from logger.custom_logger import CustomLogger
from exception.custom_exception import CustomException

logger = CustomLogger().get_logger(__file__)

class DocumentAnalyzer:
    """
    Analyzes documents using a pre-trained language model.
    Automatically logs all the action and supports section-based organization.
    """

    def __init__(self):
        try:
            self.loader = ModelLoader()
            self.llm = self.loader.load_llm_model()

            self.parser = JsonOutputParser(pydantic_object=MetaData)
            self.fixing_parser = OutputFixingParser.from_llm(self.llm, self.parser)

            self.prompt = PROMPT_REGISTRY.get("document_analysis")

            logger.info("DocumentAnalyzer initialized successfully with LLM and parsers.")

        except Exception as e:
            logger.error(f"Error initializing DocumentAnalyzer: {e}")
            raise CustomException(f"Error initializing DocumentAnalyzer: {e}", sys)

    def analyze_document(self, document_text: str) -> dict:
        """
        Analyzes the document using the pre-trained language model and returns structured metadata.
        """
        try:
            chain = self.prompt | self.llm | self.fixing_parser
            logger.info("Metadata analysis chain initialized successfully.")

            response = chain.invoke({
                "format_instructions": self.parser.get_format_instructions(),
                "document_text": document_text
            })

            logger.info("Metadata extraction completed successfully.", keys=list(response.keys()))
            return response

        except Exception as e:
            logger.error(f"Error analyzing document: {e}")
            raise CustomException(f"Error analyzing document: {e}", sys)
