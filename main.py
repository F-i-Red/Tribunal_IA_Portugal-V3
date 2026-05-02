#!/usr/bin/env python3
"""
Tribunal IA Portugal — Sistema de Simulação Jurídica V2.1
Melhorias: RAG integrado, cache, paralelismo, modo económico.
"""

import argparse
import sys
import time
from pathlib import Path

from src.utils import ConfigError, get_config, get_logger
from src.pipeline.case_processor import CaseProcessor
from src.pipeline.instancias import (
    INSTANCIAS, listar_instancias_menu, detectar_instancia_por_keywords
)

BANNER = """
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║ 🏛️  TRIBUNAL IA PORTUGAL 🇵🇹                                          ║
║                                                                      ║
║  Simulador judicial de alta fidelidade — Direito Português           ║
║                                                                      ║
║  ⚠️  Fins exclusivamente educativos e de simulação                   ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
"""

DISCLAIMER = """
Este simulador não constitui parecer jurídico nem decisão judicial.
Para situações reais, consulte sempre um Advogado inscrito na
Ordem dos Advogados de Portugal (www.oa.pt).

Ao continuar, confirma que compreende esta limitação.
"""


def aceitar_disclaimer() -> bool:
    print(DISCLAIMER)
    r = input("Aceita as condições? (s/N): ").strip().lower()
    return r in ("s", "sim", "y", "yes")


def ler_caso() -> str:
    print("\n" + "─" * 70)
    print("📝 DESCRIÇÃO DO CASO")
    print("─" * 70)
    print("Descreve o caso jurídico com o máximo de detalhe possível.")
    print("Não precisas de saber termos jurídicos — usa linguagem comum.")
    print("(Termina com uma linha vazia)\n")
    lines = []
    while True:
        try:
            line = input("> ")
            if line.strip() == "" and lines:
                break
            if line.strip():
                lines.append(line)
        except (EOFError, KeyboardInterrupt):
            print("\n❌ Interrompido.")
            sys.exit(0)
    return "\n".join(lines)


def seleccionar_instancia(case_description: str) -> str:
    print("\n" + "═" * 70)
    print("🏛️  SELECÇÃO DO TRIBUNAL")
    print("═" * 70)
    print("\nAntes de avançar, é necessário saber qual o tipo de tribunal.")
    print("Podes escolher tu, ou deixar que o sistema analise o teu caso.\n")
    print("  [1] Deixar o sistema decidir pelo caso que descreveste (recomendado)")
    print("  [2] Escolher manualmente")

    while True:
        opc = input("\nOpção (1 ou 2): ").strip()
        if opc in ("1", ""):
            codigo = detectar_instancia_por_keywords(case_description)
            inst = INSTANCIAS[codigo]
            print(f"\n ✅ Tribunal identificado: {inst.nome}")
            print(f"    Matéria: {inst.materia}")
            print(f"    {inst.descricao}")
            confirmar = input("\n Confirmas? (s/N, ou 'trocar' para escolher manualmente): ").strip().lower()
            if confirmar in ("s", "sim", "y", "yes", ""):
                return codigo
            elif confirmar == "trocar":
                opc = "2"
            else:
                return codigo
        if opc == "2":
            print("\nTipos de tribunal disponíveis:")
            print(listar_instancias_menu())
            print("\n  [AUTO] Deixar o sistema decidir automaticamente")
            codigo_input = input("\nEscreve o código (ex: TIC, TC_CIVEL, TRAB) ou AUTO: ").strip().upper()
            if codigo_input in ("1", "", "AUTO", "2"):
                codigo = detectar_instancia_por_keywords(case_description)
                inst = INSTANCIAS[codigo]
                print(f"\n ✅ Tribunal identificado: {inst.nome}")
                return codigo
            if codigo_input in INSTANCIAS:
                inst = INSTANCIAS[codigo_input]
                print(f"\n ✅ {inst.nome}")
                print(f"    Matéria: {inst.materia}")
                print(f"    {inst.descricao}")
                confirmar = input("\n Confirmas este tribunal? (s/N): ").strip().lower()
                if confirmar in ("s", "sim", "y", "yes", ""):
                    return codigo_input
                continue
            print(f" ❌ Código '{codigo_input}' não reconhecido.")
            print(f"    Usa um dos códigos da lista acima (ex: TIC, TC_CIVEL, TRAB, AUTO)")


def fase_instrucao(processor: CaseProcessor, case_description: str,
                   instancia_codigo: str) -> dict:
    inst = INSTANCIAS[instancia_codigo]
    print("\n" + "═" * 70)
    print(f"🔍 FASE DE INSTRUÇÃO — {inst.nome.upper()}")
    print("═" * 70)
    print(f"O {inst.termo_mp} e o Juiz de Instrução analisam o caso.")
    print("Para fundamentar o processo, precisam de esclarecimentos adicionais.\n")
    print("⏳ A gerar perguntas de instrução...")

    try:
        perguntas = processor.gerar_perguntas_instrucao(case_description, instancia_codigo)
        print(f"\n ✅ {len(perguntas.get('perguntas', []))} perguntas geradas.\n")
        print(perguntas.get("introducao", ""))
        print()

        respostas = {}
        for p in perguntas.get("perguntas", []):
            print(f"\n  [{p['categoria']}] {p['texto']}")
            print(f"     Importância: {p['importancia']}")
            if p.get("aceita_documentos"):
                print("     (Podes mencionar documentos/provas que tenhas)")

            resp = input("\n  ➜ Resposta (Enter para ignorar): ").strip()
            respostas[p["id"]] = {
                "pergunta": p["texto"],
                "categoria": p["categoria"],
                "resposta": resp if resp else "Sem resposta",
            }

        materiais = []
        while True:
            m = input("\n📎 Queres adicionar algum material/documento? (descrição ou Enter para terminar): ").strip()
            if not m:
                break
            materiais.append({"descricao": m, "tipo": "material"})

        return {"respostas": respostas, "materiais": materiais}

    except Exception as e:
        print(f"\n ⚠️ Não foi possível gerar perguntas: {e}")
        print("O processo continua com os dados originais.")
        return {"respostas": {}, "materiais": []}


def executar_processo(case_description: str, instancia_codigo: str,
                      dados_instrucao: dict = None, modo_economico: bool = False):
    cfg = get_config()
    print("\n" + "═" * 70)
    print("⚖️  PROCESSO JUDICIAL EM CURSO")
    print("═" * 70)

    if modo_economico:
        print("💰 Modo ECONÓMICO ativado — usa menos agentes e modelos mais baratos.")
        # Override temporário
        old_model = cfg.modelo
        cfg.__dict__["modelo"] = "google/gemini-2.0-flash-001"
        cfg.__dict__["modo_economico"] = True

    processor = CaseProcessor()
    start = time.time()

    try:
        result = processor.process(
            case_description=case_description,
            instancia_codigo=instancia_codigo,
            dados_instrucao=dados_instrucao,
        )
    finally:
        if modo_economico:
            cfg.__dict__["modelo"] = old_model
            cfg.__dict__["modo_economico"] = False

    elapsed = time.time() - start

    print("\n" + "═" * 70)
    print("✅ PROCESSO CONCLUÍDO")
    print("═" * 70)
    print(f"ID do caso: {result.case_id}")
    print(f"Trace ID:   {result.trace_id}")
    print(f"Instância:  {result.instancia_nome}")
    print(f"Tempo:      {elapsed:.1f}s")
    print(f"Custo:      ${result.custo_total_usd:.4f}")

    if result.contexto_rag:
        print(f"RAG:        {len(result.contexto_rag)} chars de contexto jurídico recuperado")

    if result.dados_instrucao and result.dados_instrucao.get("respostas"):
        n = sum(1 for v in result.dados_instrucao["respostas"].values() if v["resposta"] != "Sem resposta")
        print(f"Instrução:  {n} respostas fornecidas")

    print(f"\n📄 Ata guardada em: output_atas/{result.case_id}.txt")
    print("\n" + "─" * 70)
    print("RESUMO DAS TRÊS SENTENÇAS")
    print("─" * 70)

    def extrair_dispositivo(texto: str) -> str:
        import re
        m = re.search(r"(?:CONDENA|ABSOLVE|JULGA\s+(?:PROCEDENTE|IMPROCEDENTE)|ARQUIVA|PRONUNCIA)[^.]*\.",
                      texto, re.IGNORECASE)
        return m.group(0).strip() if m else texto[:150] + "..."

    print(f"\n🔴 Rigoroso:    {extrair_dispositivo(result.sentenca_rigorosa)}")
    print(f"🟢 Garantista:  {extrair_dispositivo(result.sentenca_garantista)}")
    print(f"🔵 Equilibrado: {extrair_dispositivo(result.sentenca_equilibrada)}")

    return result


def main():
    parser = argparse.ArgumentParser(description="Tribunal IA Portugal")
    parser.add_argument("--modo-economico", action="store_true",
                        help="Usa menos agentes e modelos mais baratos")
    parser.add_argument("--instancia", "-i", type=str, default=None,
                        help="Código da instância (TIC, TC_CIVEL, TRAB, etc.)")
    parser.add_argument("--sem-instrucao", action="store_true",
                        help="Ignora fase de instrução")
    parser.add_argument("--sem-disclaimer", action="store_true",
                        help="Ignora disclaimer interativo")
    args = parser.parse_args()

    print(BANNER)

    try:
        cfg = get_config()
    except ConfigError as e:
        print(f"\n❌ ERRO DE CONFIGURAÇÃO: {e}")
        print("\nCria um ficheiro .env na raiz do projeto com:")
        print('  OPENROUTER_API_KEY="sua_chave_aqui"')
        print("\nObtém chave gratuita em: https://openrouter.ai/keys")
        sys.exit(1)

    if not args.sem_disclaimer:
        if not aceitar_disclaimer():
            print("\n❌ Processo cancelado.")
            sys.exit(0)

    case_description = ler_caso()
    if not case_description.strip():
        print("\n❌ Descrição vazia.")
        sys.exit(0)

    instancia = args.instancia or seleccionar_instancia(case_description)

    dados_instrucao = None
    if not args.sem_instrucao:
        processor = CaseProcessor()
        dados_instrucao = fase_instrucao(processor, case_description, instancia)

    executar_processo(case_description, instancia, dados_instrucao, args.modo_economico)


if __name__ == "__main__":
    main()
