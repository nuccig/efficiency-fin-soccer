import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from libs.pipeline import APIFootballExtractionPipeline


def main() -> None:
    # Para analytics, apenas S3 + Athena é suficiente
    # RDS desabilitado por padrão (enable_postgres=False)
    pipeline = APIFootballExtractionPipeline(
        enable_s3=True,
        enable_postgres=False,  # Não necessário para analytics
        enable_glue=True
    )
    pipeline.run()


if __name__ == "__main__":
    main()
