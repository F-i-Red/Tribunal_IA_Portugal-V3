# utils/brain.py
import os
import time
import urllib.request
import urllib.error
import json
from dotenv import load_dotenv

load_dotenv()

MODELOS_FALLBACK = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "google/gemma-3-27b-it:free",
    "mistralai/mistral-7b-instruct:free",
]

def _chamar_api(modelo, system_prompt, user_prompt, max_tokens, temperatura, chave):
    payload = json.dumps({
        "model": modelo,
        "max_tokens": max_tokens,
        "temperature": temperatura,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {chave}",
            "HTTP-Referer": "https://github.com/F-i-Red/Tribunal_IA_Portugal",
            "X-Title": "Tribunal IA Portugal",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if "choices" not in data or not data["choices"]:
                return None, None
            conteudo = data["choices"][0]["message"].get("content")
            if not conteudo or len(conteudo.strip()) < 20:
                return None, None
            return conteudo.strip(), None
    except urllib.error.HTTPError as e:
        corpo = e.read().decode("utf-8")
        try:
            erro = json.loads(corpo)
            msg = erro.get("error", {}).get("message", corpo[:200])
        except Exception:
            msg = corpo[:200]
        # Devolve o código de erro para decisão de retry
        return None, (e.code, msg)
    except Exception as e:
        return None, (0, str(e))


def consultar_ia(system_prompt, user_prompt, max_tokens=2048, temperatura=0.7):
    chave = os.getenv("OPENROUTER_API_KEY", "")
    if not chave or "xxx" in chave:
        raise ValueError(
            "\n❌ ERRO: OPENROUTER_API_KEY não configurada.\n"
            "   Abre o ficheiro .env e coloca a tua chave do OpenRouter.\n"
            "   Chave GRATUITA em: https://openrouter.ai/\n"
        )

    modelo_config = os.getenv("MODELO", "meta-llama/llama-3.3-70b-instruct:free")
    modelos = [modelo_config] + [m for m in MODELOS_FALLBACK if m != modelo_config]

    for tentativa, modelo in enumerate(modelos):
        # Pausa entre chamadas para não exceder o rate limit dos modelos gratuitos
        # Primeira chamada: sem pausa. Retries: pausa crescente.
        if tentativa > 0:
            pausa = 8 * tentativa  # 8s, 16s, 24s...
            print(f"  [⏳ Rate limit — a aguardar {pausa}s antes de tentar outro modelo...]")
            time.sleep(pausa)

        resultado, erro = _chamar_api(modelo, system_prompt, user_prompt, max_tokens, temperatura, chave)

        if resultado:
            return resultado

        if erro:
            codigo, msg = erro
            if codigo == 429:
                # Rate limit — espera mais e tenta o próximo modelo
                print(f"  [⚠️  Rate limit no modelo {modelo.split('/')[-1]} — a tentar alternativa...]")
                continue
            elif codigo == 404:
                # Modelo não existe — tenta o próximo sem esperar
                continue
            # Outro erro — tenta o próximo
            continue

    # Última tentativa: espera 30s e tenta o modelo principal outra vez
    print("  [⏳ A aguardar 30s para deixar o rate limit recuperar...]")
    time.sleep(30)
    resultado, _ = _chamar_api(modelos[0], system_prompt, user_prompt, max_tokens, temperatura, chave)
    if resultado:
        return resultado

    return "❌ Serviço temporariamente indisponível. Aguarda 1-2 minutos e tenta de novo."
