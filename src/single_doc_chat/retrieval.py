import os
import sys
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_community.vectorstores import FAISS
from langchain_classic.chains.history_aware_retriever import create_history_aware_retriever
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain

from utils.models_loader import ModelLoader
from prompts.prompt_library import PROMPT_REGISTRY
from models.models import PromptTyepe
from logger.custom_logger import CustomLogger
from exception.custom_exception import CustomException

logger = CustomLogger().get_logger(__name__)

class ConversationalRAG:
    def __init__(self, session_id: str, retriever):
        try:
            pass

        except Exception as e:
            logger.error(f"Error initializing ConversationalRAG: {e} with session_id: {session_id}")
            raise CustomException(f"Error initializing ConversationalRAG: {e}", sys)

    def _load_llm(self):
        try:
            pass

        except Exception as e:
            logger.error(f"Error loading language model: {e}")
            raise CustomException(f"Error loading language model: {e}", sys)

    def _get_session_history(self, session_id: str):
        try:
            pass

        except Exception as e:
            logger.error(f"Error retrieving session history: {e}")
            raise CustomException(f"Error retrieving session history: {e}", sys)


    def load_retriever(self):
        try:
            pass

        except Exception as e:
            logger.error(f"Error loading retriever: {e}")
            raise CustomException(f"Error loading retriever: {e}", sys)

    def invoke(self):
        try:
            pass

        except Exception as e:
            logger.error(f"Error invoking ConversationalRAG: {e}")
            raise CustomException(f"Error invoking ConversationalRAG: {e}", sys)


