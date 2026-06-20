import sys
import pandas as pd
from langchain_core.output_parsers import JsonOutputParser
from langchain_classic.output_parsers import OutputFixingParser

from models.models import *
from prompts.prompt_library import PROMPT_REGISTRY
from utils.models_loader import ModelLoader
from logger.custom_logger import CustomLogger
from exception.custom_exception import CustomException

logger = CustomLogger().get_logger(__name__)

class DocumentComparator:
    def __init__(self):
        self.loader = ModelLoader()
        self.llm = self.loader.load_llm_model()
        self.parser = JsonOutputParser(pydantic_object=SummaryResponse)
        self.fixing_parser = OutputFixingParser.from_llm(self.llm, self.parser)
        self.prompt = PROMPT_REGISTRY.get("document_comparison")
        self.chain = self.prompt | self.llm | self.fixing_parser

    def compare_documents(self):
        """
        Comapres two documents and returns a structured comparison.
        """
        pass

    def _format_response(self):
        """
        Formats the response from the LLM into a structured format.
        """
        pass
