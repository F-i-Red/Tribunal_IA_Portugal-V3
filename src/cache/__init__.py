"""
Sistema de cache semântico e de hash para reduzir chamadas LLM.
"""

import hashlib
import json
import os
import pickle
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..utils.config import get_config


@dataclass
class CacheEntry:
    prompt_hash: str
    response: str
    model: str
    timestamp: float
    tokens_input: int
    tokens_output: int
    cost_usd: float


class SemanticCache:
    """
    Cache de respostas LLM por hash do prompt.
    Persiste em disco (JSON + pickle) para sobreviver reinícios.
    """

    def __init__(self, pasta_cache: Optional[Path] = None):
        cfg = get_config()
        self.pasta = pasta_cache or cfg.pasta_cache
        self.pasta.mkdir(parents=True, exist_ok=True)
        self._index: Dict[str, CacheEntry] = {}
        self._carregar()

    def _carregar(self):
        """Carrega índice do disco."""
        index_path = self.pasta / "cache_index.pkl"
        if index_path.exists():
            try:
                with open(index_path, "rb") as f:
                    self._index = pickle.load(f)
            except Exception:
                self._index = {}

    def _guardar(self):
        """Persiste índice no disco."""
        index_path = self.pasta / "cache_index.pkl"
        with open(index_path, "wb") as f:
            pickle.dump(self._index, f)

    def _hash(self, prompt: str, system: Optional[str] = None, model: str = "") -> str:
        """Gera hash determinístico do prompt."""
        texto = f"{model}:{system or ''}:{prompt}"
        return hashlib.sha256(texto.encode("utf-8")).hexdigest()[:16]

    def get(self, prompt: str, system: Optional[str] = None, model: str = "") -> Optional[CacheEntry]:
        """Procura no cache. Retorna None se não encontrar."""
        if not get_config().cache_enabled:
            return None
        h = self._hash(prompt, system, model)
        return self._index.get(h)

    def put(self, prompt: str, response: str, system: Optional[str] = None,
            model: str = "", tokens_input: int = 0, tokens_output: int = 0,
            cost_usd: float = 0.0):
        """Guarda resposta no cache."""
        if not get_config().cache_enabled:
            return
        h = self._hash(prompt, system, model)
        self._index[h] = CacheEntry(
            prompt_hash=h,
            response=response,
            model=model,
            timestamp=time.time(),
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            cost_usd=cost_usd,
        )
        self._guardar()

    def estatisticas(self) -> Dict:
        """Retorna estatísticas do cache."""
        total_hits = len(self._index)
        total_tokens_in = sum(e.tokens_input for e in self._index.values())
        total_tokens_out = sum(e.tokens_output for e in self._index.values())
        total_cost = sum(e.cost_usd for e in self._index.values())
        return {
            "entradas": total_hits,
            "tokens_input_total": total_tokens_in,
            "tokens_output_total": total_tokens_out,
            "custo_total_usd": round(total_cost, 4),
            "poupanca_estimada_usd": round(total_cost * 0.8, 4),  # 80% das chamadas evitadas
        }

    def limpar(self, max_idade_dias: int = 30):
        """Remove entradas antigas."""
        agora = time.time()
        limite = max_idade_dias * 86400
        removidas = 0
        for h in list(self._index.keys()):
            if agora - self._index[h].timestamp > limite:
                del self._index[h]
                removidas += 1
        if removidas:
            self._guardar()
        return removidas


_cache_instance: Optional[SemanticCache] = None


def get_cache() -> SemanticCache:
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = SemanticCache()
    return _cache_instance


def limpar_cache(dias: int = 30) -> int:
    return get_cache().limpar(dias)
