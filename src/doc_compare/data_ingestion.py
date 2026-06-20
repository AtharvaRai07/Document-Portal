import sys
from pathlib import Path
import fitz

from logger.custom_logger import CustomLogger
from exception.custom_exception import CustomException

class DocumentComparator:
    def __init__(self):
        pass
   
    def delete_existing_files(self):
        """
        Delete existing files at the specified paths
        """
        pass

    def save_uploaded_file(self):
        """
        Saves the uploaded file to the specified path
        """
        pass

    def read_pdf(self):
        """
        Reads the PDF file and extracts text content
        """
        pass
