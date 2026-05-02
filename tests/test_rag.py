"""
Testes do motor RAG.
"""

import pytest
from pathlib import Path
from src.rag import MotorRAG


def test_rag_indexacao(tmp_path):
    # Criar estrutura temporária
    leis = tmp_path / "data" / "leis"
    leis.mkdir(parents=True)
    (leis / "teste.txt").write_text("Artigo 1. O direito à vida é inviolável.\n\nArtigo 2. A liberdade é garantida.")

    rag = MotorRAG(tmp_path)
    n = rag.indexar(forcar=True)
    assert n > 0
    assert rag.tem_dados()


def test_rag_pesquisa(tmp_path):
    leis = tmp_path / "data" / "leis"
    leis.mkdir(parents=True)
    (leis / "teste.txt").write_text("Artigo 1. O direito à vida é inviolável.")

    rag = MotorRAG(tmp_path)
    rag.indexar(forcar=True)
    resultados = rag.pesquisar("direito à vida", n_resultados=3)
    assert len(resultados) > 0
    assert any("vida" in r.conteudo.lower() for r in resultados)


def test_rag_formatar_contexto(tmp_path):
    leis = tmp_path / "data" / "leis"
    leis.mkdir(parents=True)
    (leis / "teste.txt").write_text("Artigo 1. Teste.")

    rag = MotorRAG(tmp_path)
    rag.indexar(forcar=True)
    frags = rag.pesquisar("teste")
    ctx = rag.formatar_contexto(frags)
    assert "CONTEXTO JURÍDICO" in ctx


def test_rag_persistencia(tmp_path):
    leis = tmp_path / "data" / "leis"
    leis.mkdir(parents=True)
    (leis / "teste.txt").write_text("Artigo 1. Persistência.")

    rag1 = MotorRAG(tmp_path)
    n1 = rag1.indexar(forcar=True)

    # Novo objeto — deve carregar do cache
    rag2 = MotorRAG(tmp_path)
    n2 = rag2.indexar()
    assert n1 == n2
    assert rag2.tem_dados()
