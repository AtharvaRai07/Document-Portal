import sys
import os
from operator import itemgetter
from typing import List, Optional

from langchain_core.messages import BaseMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores import FAISS

from prompts.prompt_library import PROMPT_REGISTRY
from models.models import PromptType
from utils.config_loader import load_config
from utils.models_loader import ModelLoader
from logger.custom_logger import CustomLogger
from exception.custom_exception import CustomException

logger = CustomLogger().get_logger(__name__)

class ConversationalRAG:
    def __init__(self, session_id: str, retriever = None):
        try:
            self.session_id = session_id
            self.config = load_config()
            self.llm = self._load_llm()
            self.contextualize_prompt: ChatPromptTemplate = PROMPT_REGISTRY[
                PromptType.CONTEXTUALIZE_QUESTION.value
            ]
            self.qa_prompt: ChatPromptTemplate = PROMPT_REGISTRY[
                PromptType.CONTEXT_QA.value
            ]

            self.retriever = retriever
            self.chain = None
            if self.retriever is not None:
                self._build_lcel_chain()

            logger.info(f"ConversationalRAG initialized with session_id: {self.session_id}, retriever: {self.retriever is not None}")

        except Exception as e:
            logger.error(f"Error initializing ConversationalRAG: {e}")
            raise CustomException(f"Error initializing ConversationalRAG: {e}", sys)


    def load_retriever_from_faiss(self, index_path: str = None, index_name: str = None):
        try:
            if not os.path.isdir(index_path):
                raise FileNotFoundError(f"FAISS index directory not found: {index_path}")

            embeddings = ModelLoader().load_embedding_model()
            vectorstore = FAISS.load_local(index_path, embeddings, index_name=index_name, allow_dangerous_deserialization=True)

            self.retriever = vectorstore.as_retriever(search_type=self.config['retriever']['search_type'], search_kwargs={"k": self.config['retriever']['top_k']})
            self._build_lcel_chain()

            logger.info(f"FAISS retriever loaded from {index_path} with index name: {index_name}")

            return self.retriever

        except Exception as e:
            logger.error(f"Error loading FAISS retriever: {e}")
            raise CustomException(f"Error loading FAISS retriever: {e}", sys)


    def invoke(self, user_input: str, chat_history: Optional[List[BaseMessage]] = None):
        try:
            if self.chain is None:
                raise CustomException("LCEL chain is not built. Cannot invoke the model.", sys)

            chat_history = chat_history or []
            payload = {"input": user_input, "chat_history": chat_history}
            answer = self.chain.invoke(payload)

            if not answer:
                logger.warning("The model returned an empty response.")
                raise ValueError("The model returned an empty response. Please check the input and model configuration.")

            logger.info(f"Model invoked successfully with input: {user_input}. Response: {answer[:150]}...")

            return answer

        except Exception as e:
            logger.error(f"Error invoking ConversationalRAG: {e}")
            raise CustomException(f"Error invoking ConversationalRAG: {e}", sys)


    def _load_llm(self):
        try:
            llm = ModelLoader().load_llm_model()
            if not llm:
                raise ValueError("LLM model could not be loaded. Please check the model configuration.")
            logger.info(f"LLM model loaded successfully: {llm}")

            return llm

        except Exception as e:
            logger.error(f"Error loading LLM model: {e}")
            raise CustomException(f"Error loading LLM model: {e}", sys)


    @staticmethod
    def _format_docs(docs):
        return "\n\n".join(getattr(d, "page_content", str(d)) for d in docs)

    def _build_lcel_chain(self):
        try:
            if self.retriever is None:
                raise CustomException("Retriever is not set. Cannot build LCEL chain.", sys)

            question_rewriter = (
                {"input":itemgetter("input"), "chat_history": itemgetter("chat_history")}
                | self.contextualize_prompt
                | self.llm
                | StrOutputParser()
            )

            retrieve_docs = question_rewriter | self.retriever | self._format_docs

            self.chain = (
                {
                    "context": retrieve_docs,
                    "input": itemgetter("input"),
                    "chat_history": itemgetter("chat_history"),
                }
                | self.qa_prompt
                | self.llm
                | StrOutputParser()
            )

            logger.info("LCEL chain built successfully.")

        except Exception as e:
            logger.error(f"Error building LCEL chain: {e}")
            raise CustomException(f"Error building LCEL chain: {e}", sys)
