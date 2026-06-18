import os
import sys
from langchain_core.output_parsers import JsonOutputParser
from langchain_classic.output_parsers import OutputFixingParser
from utils.models_loader import ModelLoader
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
        pass

    def analyze_document(self):
        pass
