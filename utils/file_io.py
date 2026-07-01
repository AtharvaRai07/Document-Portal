import uuid
import hashlib
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Iterable, List, Optional, Dict, Any
from utils.config_loader import load_config
from utils.models_loader import ModelLoader
from logger.custom_logger import CustomLogger
from exception.custom_exception import CustomException

logger = CustomLogger().get_logger(__name__)

### Helper functions (File I\O + loading)

def _session_id(prefix: str = "session") -> str:
    return f"{prefix}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

def save_uploaded_file(uploaded_file: Iterable, target_dir: Path) -> List[Path]:
    """
    Save uploaded files and return local paths
    """
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        saved: List[Path] = []
        config = load_config()
        for uf in uploaded_file:
            name = getattr(uf, "name", "file")
            ext = Path(name).suffix.lower()
            if ext not in config.get("supported_extensions", []):
                logger.warning(f"Unsupported file extension: {ext}")
                raise CustomException(f"Unsupported file extension: {ext}")
                continue

            fname = f"f{uuid.uuid4().hex[:8]}{ext}"
            out = target_dir
            with open(out, 'wb') as f:
                if hasattr(uf, "file"):
                    f.write(uf.read())
                else:
                    f.write(uf.getbuffer())

            saved.append(out)
            logger.info(f"Saved uploaded file to {out}")

        return saved

    except Exception as e:
        logger.error(f"Error saving uploaded files: {e}")
        raise CustomException(f"Error saving uploaded files: {e}")
