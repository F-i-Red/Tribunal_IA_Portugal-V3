"""
Configuração centralizada com validação de segurança.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class Config:
    openrouter_api_key: str
    modelo: str = "anthropic/claude-haiku-4-5"
    max_retries: int = 3
    retry_backoff_factor: float = 2.0
    request_timeout: int = 120
    pasta_leis: Path = field(default_factory=lambda: Path("data/leis"))
    pasta_precedentes: Path = field(default_factory=lambda: Path("data/precedentes"))
    guardar_atas: bool = True
    pasta_atas: Path = field(default_factory=lambda: Path("output_atas"))
    log_level: str = "INFO"
    anonimizar_entidades: bool = True
    chroma_db_path: Path = field(default_factory=lambda: Path("data/chroma_db"))
    watermark_atas: bool = True
    cache_enabled: bool = True
    pasta_cache: Path = field(default_factory=lambda: Path("src/cache"))
    modo_economico: bool = False  # Novo: reduz chamadas LLM
    paralelismo: bool = True      # Novo: sentenças em paralelo

    @classmethod
    def from_env(cls) -> "Config":
        load_dotenv()
        api_key = os.getenv("OPENROUTER_API_KEY", "").strip()

        if not api_key:
            raise ConfigError("❌ OPENROUTER_API_KEY não definida.")
        if "sua_chave" in api_key.lower() or "xxxx" in api_key.lower():
            raise ConfigError("❌ Substitui o placeholder pela chave real.")

        pasta_atas = Path(os.getenv("PASTA_ATAS", "output_atas"))
        pasta_atas.mkdir(parents=True, exist_ok=True)

        return cls(
            openrouter_api_key=api_key,
            modelo=os.getenv("MODELO", "anthropic/claude-haiku-4-5"),
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
            request_timeout=int(os.getenv("REQUEST_TIMEOUT", "120")),
            pasta_leis=Path(os.getenv("PASTA_LEIS", "data/leis")),
            guardar_atas=os.getenv("GUARDAR_ATAS", "true").lower() == "true",
            pasta_atas=pasta_atas,
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            anonimizar_entidades=os.getenv("ANONIMIZAR_ENTIDADES", "true").lower() == "true",
            cache_enabled=os.getenv("CACHE_ENABLED", "true").lower() == "true",
            modo_economico=os.getenv("MODO_ECONOMICO", "false").lower() == "true",
            paralelismo=os.getenv("PARALELISMO", "true").lower() == "true",
        )

    def validate_directories(self) -> None:
        for path in [self.pasta_leis, self.pasta_precedentes, self.pasta_cache, self.chroma_db_path]:
            path.mkdir(parents=True, exist_ok=True)


_config: Optional["Config"] = None


def get_config() -> Config:
    global _config
    if _config is None:
        _config = Config.from_env()
        _config.validate_directories()
    return _config
