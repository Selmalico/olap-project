from abc import ABC, abstractmethod
from anthropic import Anthropic
from config import settings
from tools.duckdb_executor import get_schema_info

client = Anthropic(api_key=settings.anthropic_api_key)


class BaseAgent(ABC):
    name: str = "base"
    description: str = ""

    def call_llm(self, system: str, messages: list) -> str:
        response = client.messages.create(
            model=settings.model,
            max_tokens=settings.max_tokens,
            system=system,
            messages=messages
        )
        return response.content[0].text

    def schema_context(self) -> str:
        info = get_schema_info()
        return (
            f"Database: DuckDB reading Parquet directly from S3.\n"
            f"Main table path: read_parquet('{info['s3_path']}')\n"
            f"ALWAYS use this exact FROM clause: FROM read_parquet('{info['s3_path']}') AS f\n"
            f"Dimensions: {', '.join(info['dimensions'])}\n"
            f"Measures: {', '.join(info['measures'])}\n"
            f"Date range: {info['date_range']}\n"
            f"Total rows: {info['total_rows']}"
        )

    @abstractmethod
    def run(self, query: str, params: dict) -> dict:
        pass
