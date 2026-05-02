#!/usr/bin/env python3
"""
Verificador do sistema Tribunal IA Portugal V2.1
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.utils import get_config, get_brain, get_logger
from src.rag import MotorRAG
from src.cache import get_cache


def verificar_env():
    print("=" * 70)
    print("🔐 1. VERIFICAÇÃO DO FICHEIRO .env")
    print("=" * 70)

    env_path = Path(".env")
    if not env_path.exists():
        print("❌ .env NÃO ENCONTRADO")
        print("   Cria um ficheiro .env com: OPENROUTER_API_KEY=sua_chave")
        return False

    try:
        cfg = get_config()
        print(f"✅ .env encontrado")
        print(f"   Modelo: {cfg.modelo}")
        print(f"   Max retries: {cfg.max_retries}")
        print(f"   Cache: {'ativado' if cfg.cache_enabled else 'desativado'}")
        print(f"   Paralelismo: {'ativado' if cfg.paralelismo else 'desativado'}")
        print(f"   Modo económico: {'ativado' if cfg.modo_economico else 'desativado'}")
        return True
    except Exception as e:
        print(f"❌ Erro ao ler .env: {e}")
        return False


def verificar_chave():
    print("\n" + "=" * 70)
    print("🌐 2. VERIFICAÇÃO DA CHAVE API")
    print("=" * 70)

    try:
        brain = get_brain()
        print("✅ Chave API carregada")
        print(f"   Circuit breaker: {'ABERTO' if brain._circuit_open else 'FECHADO'}")
        print(f"   Falhas: {brain._failures}/{brain._failure_threshold}")
        return True
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False


def verificar_rag():
    print("\n" + "=" * 70)
    print("📚 3. VERIFICAÇÃO DO RAG")
    print("=" * 70)

    try:
        rag = MotorRAG(Path("."))
        n = rag.indexar()
        stats = rag.estatisticas()
        print(f"✅ RAG indexado: {n} fragmentos")
        print(f"   Leis: {stats['fragmentos_leis']}")
        print(f"   Jurisprudência: {stats['fragmentos_jurisprudencia']}")
        print(f"   Precedentes: {stats['fragmentos_precedentes']}")
        print(f"   Fontes: {', '.join(stats['fontes'][:5])}")
        if stats['fontes']:
            print(f"   (e outras...)")

        # Teste de pesquisa
        resultados = rag.pesquisar("homicídio", n_resultados=3)
        print(f"   Teste pesquisa 'homicídio': {len(resultados)} resultados")
        return True
    except Exception as e:
        print(f"❌ Erro no RAG: {e}")
        return False


def verificar_cache():
    print("\n" + "=" * 70)
    print("💾 4. VERIFICAÇÃO DO CACHE")
    print("=" * 70)

    try:
        cache = get_cache()
        stats = cache.estatisticas()
        print(f"✅ Cache operacional")
        print(f"   Entradas: {stats['entradas']}")
        print(f"   Tokens input total: {stats['tokens_input_total']}")
        print(f"   Tokens output total: {stats['tokens_output_total']}")
        print(f"   Custo total: ${stats['custo_total_usd']}")
        print(f"   Poupança estimada: ${stats['poupanca_estimada_usd']}")
        return True
    except Exception as e:
        print(f"❌ Erro no cache: {e}")
        return False


def verificar_modelos():
    print("\n" + "=" * 70)
    print("🤖 MODELOS RECOMENDADOS")
    print("=" * 70)
    modelos = [
        ("anthropic/claude-haiku-4-5", "Rápido, económico, bom para testes"),
        ("anthropic/claude-sonnet-4.6", "Equilibrado, recomendado para produção"),
        ("google/gemini-2.0-flash-001", "Muito barato, boa qualidade"),
        ("google/gemini-2.5-pro", "Bom equilíbrio qualidade/custo"),
        ("mistralai/mistral-small-24b", "Económico, open-weight"),
        ("deepseek/deepseek-chat-v3-0324", "Muito barato, qualidade razoável"),
    ]
    for m, desc in modelos:
        print(f"   • {m:<45} — {desc}")
    print("\n   Para usar: export MODELO='nome-do-modelo' ou edita .env")


def main():
    print("\n" + "=" * 70)
    print("🏛️  TRIBUNAL IA PORTUGAL — VERIFICADOR DE SISTEMA V2.1")
    print("=" * 70)

    checks = [
        ("Ambiente", verificar_env),
        ("Chave API", verificar_chave),
        ("RAG", verificar_rag),
        ("Cache", verificar_cache),
    ]

    resultados = []
    for nome, fn in checks:
        try:
            ok = fn()
            resultados.append((nome, ok))
        except Exception as e:
            print(f"\n❌ Erro inesperado em {nome}: {e}")
            resultados.append((nome, False))

    print("\n" + "=" * 70)
    print("📊 RESUMO")
    print("=" * 70)
    for nome, ok in resultados:
        status = "✅ OK" if ok else "❌ FALHA"
        print(f"   {status} — {nome}")

    verificar_modelos()

    total_ok = sum(1 for _, ok in resultados if ok)
    print(f"\n{'=' * 70}")
    print(f"Resultado: {total_ok}/{len(resultados)} verificações passaram")

    if total_ok == len(resultados):
        print("🎉 Sistema pronto a usar!")
    else:
        print("⚠️  Corrige os erros acima antes de continuar.")
        sys.exit(1)


if __name__ == "__main__":
    main()
