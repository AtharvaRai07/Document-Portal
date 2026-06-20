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

    def compare_documents(self, combined_docs: str) -> list[dict]:
        """
        Comapres two documents and returns a structured comparison.
        """
        inputs = {
            "combined_docs": combined_docs,
            "format_instructions": self.parser.get_format_instructions()
        }
        logger.info(f"Starting document comaprison with inputs: {inputs}")
        repsonse = self.chain.invoke(inputs)
        logger.info(f"Received response from LLM: {repsonse}")

        return self._format_response(repsonse)

    def _format_response(self, response: list[dict]) -> pd.DataFrame:
        """
        Formats the response from the LLM into a structured format.
        """
        try:
            df = pd.DataFrame(response)
            logger.info(f"Formatted response into DataFrame with shape: {df.shape}")
            return df
        except Exception as e:
            logger.error(f"Error formatting response: {e}")
            raise CustomException(f"Error formatting response: {e}", sys)

