# utils/loader.py
# Carrega documentos de lei (.txt e .pdf) da pasta data/leis/

import os

def carregar_documentos(pasta="data/leis/"):
    """Lê todos os ficheiros .txt e .pdf da pasta e devolve o texto concatenado."""
    if not os.path.exists(pasta):
        os.makedirs(pasta, exist_ok=True)
        return ""

    textos = []
    ficheiros_lidos = 0

    for ficheiro in sorted(os.listdir(pasta)):
        caminho = os.path.join(pasta, ficheiro)
        if ficheiro.endswith(".txt"):
            try:
                with open(caminho, "r", encoding="utf-8") as f:
                    conteudo = f.read().strip()
                    if conteudo:
                        textos.append(f"=== {ficheiro} ===\n{conteudo}")
                        ficheiros_lidos += 1
            except Exception as e:
                print(f"  [AVISO] Nao foi possivel ler {ficheiro}: {e}")
        elif ficheiro.endswith(".pdf"):
            try:
                from pypdf import PdfReader
                reader = PdfReader(caminho)
                conteudo = "\n".join(p.extract_text() or "" for p in reader.pages).strip()
                if conteudo:
                    textos.append(f"=== {ficheiro} ===\n{conteudo}")
                    ficheiros_lidos += 1
            except Exception as e:
                print(f"  [AVISO] Nao foi possivel ler PDF {ficheiro}: {e}")

    if ficheiros_lidos > 0:
        print(f"  [RAG] {ficheiros_lidos} documento(s) carregado(s) de '{pasta}'.")
    else:
        print(f"  [RAG] Nenhum documento encontrado em '{pasta}'. O bot usara conhecimento geral.")

    return "\n\n".join(textos)


def resumir_para_contexto(texto_completo: str, max_chars: int = 8000) -> str:
    """Limita o contexto legislativo para nao exceder o limite da API."""
    if len(texto_completo) <= max_chars:
        return texto_completo
    return texto_completo[:max_chars] + "\n\n[...texto truncado por dimensao...]"
