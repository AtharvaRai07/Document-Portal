import os
import sys
from dotenv import load_dotenv
from utils.config_loader import load_config
from langchain_groq import ChatGroq
from langchain_cohere import CohereEmbeddings

from logger.custom_logger import CustomLogger
from exception.custom_exception import CustomException

logger = CustomLogger().get_logger(__name__)

class ModelLoader:
    def __init__(self):
        load_dotenv()
        self._validate_env()
        self.config = load_config()
        logger.info("Configuration loaded successfully", config_keys=list(self.config.keys()))

    def _validate_env(self):
        """
        Validates the necessary enviroment variables.
        """
        required_vars = ["COHERE_API_KEY", "GROQ_API_KEY"]
        self.api_keys = {key : os.getenv(key) for key in required_vars}
        missing_vars = [k for k, v in self.api_keys.items() if not v]

        if missing_vars:
            logger.error("Missing required environment variables", missing_vars=missing_vars)
            raise CustomException(f"Missing required environment variables: {', '.join(missing_vars)}", sys)

        logger.info("All required environment variables are present", api_keys=list(self.api_keys.keys()))

    def load_embedding_model(self):
        """
        Loads and returns the embedding model based on the configuration.
        """
        try:
            logger.info("Loading embedding model", model_name=self.config.get("embedding_model"))
            model_name = self.config["embedding_model"]['model_name']

            logger.info("Succesfully loaded the embedding model")
            return CohereEmbeddings(model=model_name)
        except Exception as e:
            logger.error("Failed to load embedding model", error=str(e))
            raise CustomException(e, sys)

    def load_llm_model(self):
        """
        Load ans return the LLM Model
        """
        """Load LLM dynamically based on provider in config"""

        llm_block = self.config['llm']
        provider_key = os.getenv('LLM_Provider', 'groq')

        logger.info("Loading LLM model...")

        if provider_key not in llm_block:
            logger.error("LLM provider not found in config", provider_key=provider_key)
            raise ValueError(f"LLM provider '{provider_key}' not found in config")

        llm_config = llm_block[provider_key]
        provider = llm_config["provider"]
        model_name = llm_config["model_name"]
        temperature = llm_config["temperature"]

        logger.info("Loading LLM", provider=provider, model_name=model_name, temperature=temperature)

        if provider == "groq":
            llm = ChatGroq(
                model=model_name,
                temperature=temperature,
            )
            return llm

if __name__ == "__main__":
    try:
        model_loader = ModelLoader()

        embeddings = model_loader.load_embedding_model()
        print("Embedding model loaded successfully:", embeddings)

        llm = model_loader.load_llm_model()
        print("LLM model loaded successfully:", llm)

    except Exception as e:
        logger.error("An error occurred while loading models", error=str(e))
        raise CustomException(e, sys)
