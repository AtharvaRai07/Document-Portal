import os
import sys
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores import FAISS
from langchain_classic.chains.history_aware_retriever import create_history_aware_retriever
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain

from utils.models_loader import ModelLoader
from prompts.prompt_library import PROMPT_REGISTRY
from utils.config_loader import load_config
from models.models import PromptType
from logger.custom_logger import CustomLogger
from exception.custom_exception import CustomException

logger = CustomLogger().get_logger(__name__)

class ConversationalRAG:
    def __init__(self, session_id: str, retriever):
        try:
            self.session_id = session_id
            self.config = load_config()
            self.retriever = retriever
            self.model_loader = ModelLoader()
            self.llm = self.model_loader.load_llm_model()
            self.contextualized_prompt: ChatPromptTemplate = PROMPT_REGISTRY[
                PromptType.CONTEXTUALIZE_QUESTION.value
            ]
            self.qa_prompt: ChatPromptTemplate = PROMPT_REGISTRY[
                PromptType.CONTEXT_QA.value
            ]

            self.history_aware_retriever = create_history_aware_retriever(
                self.llm, self.retriever, self.contextualized_prompt
            )
            logger.info(f"Created history-aware retriever for session_id: {session_id}")

            self.qa_chain = create_stuff_documents_chain(self.llm, self.qa_prompt)
            self.rag_chain = create_retrieval_chain(self.history_aware_retriever, self.qa_chain)
            logger.info(f"Created RAG chain for session_id: {session_id}")

            self.chain = RunnableWithMessageHistory(
                self.rag_chain,
                self._get_session_history,
                input_messages_key="input",
                history_messages_key="chat_history",
                output_messages_key="answer"
            )
            logger.info(f"Created Runnable with message history for session_id: {session_id}")

        except Exception as e:
            logger.error(f"Error initializing ConversationalRAG: {e} with session_id: {session_id}")
            raise CustomException(f"Error initializing ConversationalRAG: {e}", sys)

    def _load_llm(self):
        """LLM is already loaded in __init__, this method is kept for backward compatibility."""
        try:
            logger.info("Language model already loaded.")
            return self.llm

        except Exception as e:
            logger.error(f"Error accessing language model: {e}")
            raise CustomException(f"Error accessing language model: {e}", sys)

    def _get_session_history(self, session_id: str) -> BaseChatMessageHistory:
        try:
            # Create or retrieve chat history for the session
            # For now, using in-memory ChatMessageHistory. In production, use a persistent store.
            if not hasattr(self, '_session_histories'):
                self._session_histories = {}

            if session_id not in self._session_histories:
                self._session_histories[session_id] = ChatMessageHistory()

            return self._session_histories[session_id]

        except Exception as e:
            logger.error(f"Error retrieving session history: {e}")
            raise CustomException(f"Error retrieving session history: {e}", sys)


    def load_retriever(self, index_path: str):
        try:
            embeddings = self.model_loader.load_embedding_model()
            if not os.path.isdir(index_path):
                raise FileNotFoundError(f"Index path {index_path} does not exist or is not a directory.")

            vector_store = FAISS.load_local(index_path, embeddings)
            logger.info(f"Vector store loaded successfully from {index_path}.")

            retriever = vector_store.as_retriever(search_type=self.config['retriever']['search_type'], search_kwargs={"k": self.config['retriever']['top_k']})
            logger.info("Retriever created successfully")
            return retriever

        except Exception as e:
            logger.error(f"Error loading retriever: {e}")
            raise CustomException(f"Error loading retriever: {e}", sys)

    def invoke(self, user_input: str):
        try:
            response = self.chain.invoke(
                {"input": user_input},
                config={"configurable": {"session_id": self.session_id}}
            )
            answer = response.get("answer", "")
            if not answer:
                logger.warning(f"No answer generated for user input: {user_input}")

            logger.info(f"RAG chain invoked successfully for session_id: {self.session_id} with user_input: {user_input} and generated answer: {answer[:150]}...")
            return answer

        except Exception as e:
            logger.error(f"Error invoking ConversationalRAG: {e}")
            raise CustomException(f"Error invoking ConversationalRAG: {e}", sys)


