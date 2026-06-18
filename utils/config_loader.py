import yaml
import os
import sys

from logger.custom_logger import CustomLogger
from exception.custom_exception import CustomException

logger = CustomLogger().get_logger(__name__)


def load_config(config_path: str = "config/config.yaml") -> dict:
    try:
        logger.info(f"Loading config file from: {config_path}")

        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)

            logger.info(f"Config file loaded successfully: {config_path}")
            return config

    except Exception as e:
        logger.error("Failed to load the config file")
        raise CustomException(e, sys)

# if __name__== "__main__":
#     config = load_config()
#     logger.info(f"Loaded configuration: {config}")
