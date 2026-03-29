from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Korean RAG Knowledge Assistant"
    app_env: str = "local"
    db_path: str = "storage/app.db"
    raw_dir: str = "storage/raw"
    parsed_dir: str = "storage/parsed"
    index_dir: str = "storage/index"
    eval_report_dir: str = "storage/evals"

    chunk_size: int = 700
    chunk_overlap: int = 120
    min_retrieval_score: float = 0.2

    enable_dense_retrieval: bool = True
    dense_backend: str = "hash"
    dense_model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    dense_embedding_dim: int = 384
    embedding_batch_size: int = 32
    embedding_cache_enabled: bool = True
    hybrid_alpha: float = 0.65
    candidate_pool_size: int = 20

    generator_mode: str = "extractive"
    top_k_default: int = 5

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    def ensure_directories(self) -> None:
        for path_str in [self.raw_dir, self.parsed_dir, self.index_dir, self.eval_report_dir]:
            Path(path_str).mkdir(parents=True, exist_ok=True)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    return settings
