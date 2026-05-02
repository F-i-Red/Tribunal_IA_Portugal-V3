#!/usr/bin/env python3
"""
Gestor da base de conhecimento jurídica.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.rag import MotorRAG


def listar_fontes():
    rag = MotorRAG(Path("."))
    stats = rag.estatisticas()
    print("=" * 70)
    print("📚 BASE DE CONHECIMENTO JURÍDICA")
    print("=" * 70)
    print(f"Total de fragmentos: {stats['total_fragmentos']}")
    print(f"  - Leis: {stats['fragmentos_leis']}")
    print(f"  - Jurisprudência: {stats['fragmentos_jurisprudencia']}")
    print(f"  - Precedentes: {stats['fragmentos_precedentes']}")
    print(f"\nFontes indexadas:")
    for fonte in sorted(stats['fontes']):
        print(f"  • {fonte}")


def recarregar():
    print("🔄 A recarregar índice RAG...")
    rag = MotorRAG(Path("."))
    n = rag.recarregar()
    print(f"✅ {n} fragmentos reindexados.")


def pesquisar(consulta: str, n: int = 5):
    rag = MotorRAG(Path("."))
    resultados = rag.pesquisar(consulta, n_resultados=n)
    print(f"\n🔍 Resultados para: '{consulta}'")
    print("=" * 70)
    for i, r in enumerate(resultados, 1):
        print(f"\n{i}. [{r.tipo.upper()}] {r.fonte} (relevância: {r.relevancia})")
        print(f"   {r.conteudo[:300]}...")


def main():
    parser = argparse.ArgumentParser(description="Gestor da base de conhecimento")
    parser.add_argument("--listar", action="store_true", help="Listar fontes indexadas")
    parser.add_argument("--recarregar", action="store_true", help="Forçar reindexação")
    parser.add_argument("--pesquisar", type=str, help="Pesquisar na base")
    parser.add_argument("-n", type=int, default=5, help="Número de resultados")
    args = parser.parse_args()

    if args.listar:
        listar_fontes()
    elif args.recarregar:
        recarregar()
    elif args.pesquisar:
        pesquisar(args.pesquisar, args.n)
    else:
        listar_fontes()


if __name__ == "__main__":
    main()
