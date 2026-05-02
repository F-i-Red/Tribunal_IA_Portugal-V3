"""
Testes do sistema de cache.
"""

import pytest
from src.cache import SemanticCache, get_cache


def test_cache_put_get(tmp_path):
    cache = SemanticCache(tmp_path)
    cache.put("prompt teste", "resposta teste", model="test-model")
    entry = cache.get("prompt teste", model="test-model")
    assert entry is not None
    assert entry.response == "resposta teste"


def test_cache_miss(tmp_path):
    cache = SemanticCache(tmp_path)
    entry = cache.get("prompt inexistente", model="test-model")
    assert entry is None


def test_cache_diferentes_modelos(tmp_path):
    cache = SemanticCache(tmp_path)
    cache.put("prompt", "resposta A", model="modelo-A")
    cache.put("prompt", "resposta B", model="modelo-B")
    assert cache.get("prompt", model="modelo-A").response == "resposta A"
    assert cache.get("prompt", model="modelo-B").response == "resposta B"


def test_cache_estatisticas(tmp_path):
    cache = SemanticCache(tmp_path)
    cache.put("p1", "r1", model="m", tokens_input=100, tokens_output=50, cost_usd=0.001)
    cache.put("p2", "r2", model="m", tokens_input=200, tokens_output=100, cost_usd=0.002)
    stats = cache.estatisticas()
    assert stats["entradas"] == 2
    assert stats["tokens_input_total"] == 300
