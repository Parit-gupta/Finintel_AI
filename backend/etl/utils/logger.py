import logging
from pathlib import Path

log_directory = Path("backend/etl/logs")
log_directory.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=log_directory / "etl.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("FinIntelAI")