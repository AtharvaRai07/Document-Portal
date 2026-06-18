import os
import sys
import fitz
import uuid
from datetime import datetime
from logger.custom_logger import CustomLogger
from exception.custom_exception import CustomException

logger = CustomLogger().get_logger(__file__)

class DocumentHandler:
    """
    Handles PDF saving and reading operations.
    Automatically logs all the action and supports section-based organization.
    """

    def __init__(self):
        pass

    def save_pdf(self):
        pass

    def read_pdf(self):
        pass



