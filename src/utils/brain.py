"""
Interface com a API via OpenRouter.
Suporta todos os modelos do OpenRouter — gratuitos e pagos.
Muda apenas MODELO= no ficheiro .env para alternar entre modelos.
"""

import time
from dataclasses import dataclass
from typing import Dict, List, Optional

import httpx

from .config import get_config
from .logger import get_logger


@dataclass
class LLMResponse:
    content: str
    model: str
    tokens_input: int
    tokens_output: int
    duration_ms: float
    cost_usd: float


class CircuitBreakerOpen(Exception):
    pass


class TribunalBrain:
    def __init__(self):
        self.config = get_config()
        self.logger = get_logger()
        self._failures = 0
        self._failure_threshold = 8
        self._circuit_open = False
        self._last_failure_time: Optional[float] = None
        self._circuit_timeout = 30

    def _check_circuit(self):
        if self._circuit_open:
            elapsed = time.time() - (self._last_failure_time or 0)
            if elapsed > self._circuit_timeout:
                self._circuit_open = False
                self._failures = 0
                self.logger.info("Circuit breaker resetado")
            else:
                remaining = int(self._circuit_timeout - elapsed)
                raise CircuitBreakerOpen(
                    f"Demasiadas falhas consecutivas. "
                    f"Aguarda {remaining}s e tenta novamente."
                )

    def _record_success(self):
        self._failures = 0
        self._circuit_open = False

    def _record_failure(self, reason: str):
        self._failures += 1
        self._last_failure_time = time.time()
        self.logger.error(f"Falha API ({self._failures}/{self._failure_threshold}): {reason}")
        if self._failures >= self._failure_threshold:
            self._circuit_open = True

    def call(self, messages: List[Dict], system_prompt: Optional[str] = None,
             temperature: float = 0.3, max_tokens: int = 2000) -> LLMResponse:
        self._check_circuit()

        max_tentativas = 3
        ultimo_erro = None

        for tentativa in range(1, max_tentativas + 1):
            try:
                resultado = self._chamar_api(
                    messages, system_prompt, temperature, max_tokens
                )
                self._record_success()
                return resultado

            except httpx.HTTPStatusError as e:
                codigo = e.response.status_code
                corpo = e.response.text[:400]

                if codigo == 401:
                    raise RuntimeError(
                        "❌ Chave API inválida (401).\n"
                        "   Abre .env e verifica OPENROUTER_API_KEY."
                    )
                elif codigo == 402:
                    raise RuntimeError(
                        "❌ Sem créditos OpenRouter (402).\n"
                        "   Acede a https://openrouter.ai e adiciona créditos,\n"
                        "   ou muda para um modelo gratuito no .env:\n"
                        "   MODELO=google/gemini-2.0-flash-exp:free"
                    )
                elif codigo == 429:
                    espera = 20 * tentativa
                    self.logger.warning(f"Rate limit (429). Aguardando {espera}s...")
                    time.sleep(espera)
                    ultimo_erro = "Rate limit (429)"
                    continue
                elif codigo == 400:
                    raise RuntimeError(
                        f"❌ Modelo inválido ou pedido mal formado (400).\n"
                        f"   Modelo actual: {self.config.modelo}\n"
                        f"   Detalhe: {corpo}\n"
                        f"   Corre: python verificar.py  para ver modelos válidos."
                    )
                elif codigo == 503:
                    espera = 15 * tentativa
                    self.logger.warning(f"Serviço indisponível (503). Aguardando {espera}s...")
                    time.sleep(espera)
                    ultimo_erro = "Serviço indisponível (503)"
                    continue
                else:
                    self._record_failure(f"HTTP {codigo}: {corpo[:100]}")
                    ultimo_erro = f"HTTP {codigo}"
                    if tentativa < max_tentativas:
                        time.sleep(5 * tentativa)

            except httpx.ConnectError as e:
                self._record_failure(f"Ligação: {e}")
                ultimo_erro = "Sem ligação à internet"
                if tentativa < max_tentativas:
                    time.sleep(5 * tentativa)

            except httpx.TimeoutException:
                self._record_failure("Timeout")
                ultimo_erro = f"Timeout (>{self.config.request_timeout}s)"
                if tentativa < max_tentativas:
                    time.sleep(3)

        self._record_failure(f"Esgotadas {max_tentativas} tentativas: {ultimo_erro}")
        raise RuntimeError(
            f"❌ API falhou após {max_tentativas} tentativas: {ultimo_erro}\n"
            f"   Modelo: {self.config.modelo}\n"
            f"   Corre: python verificar.py  para diagnosticar."
        )

    def _chamar_api(self, messages: List[Dict], system_prompt: Optional[str],
                    temperature: float, max_tokens: int) -> LLMResponse:
        start = time.time()

        headers = {
            "Authorization": f"Bearer {self.config.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/F-i-Red/Tribunal_IA_Portugal",
            "X-Title": "Tribunal IA Portugal",
        }

        # System prompt como primeira mensagem com role "system"
        # (formato correcto para OpenRouter com qualquer modelo)
        msgs_completas = []
        if system_prompt:
            msgs_completas.append({
                "role": "system",
                "content": system_prompt
            })
        msgs_completas.extend(messages)

        payload: Dict = {
            "model": self.config.modelo,
            "messages": msgs_completas,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        with httpx.Client(timeout=self.config.request_timeout) as client:
            resp = client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        duration_ms = (time.time() - start) * 1000

        # Extrair conteúdo (robusto para diferentes formatos de resposta)
        try:
            content = data["choices"][0]["message"]["content"]
            # Alguns modelos gratuitos devolvem None no content
            if content is None:
                # Tentar campo alternativo "reasoning" ou "text"
                content = (
                    data["choices"][0]["message"].get("reasoning") or
                    data["choices"][0]["message"].get("text") or
                    data["choices"][0].get("text") or
                    "[Resposta vazia do modelo — tenta novamente ou muda de modelo]"
                )
        except (KeyError, IndexError, TypeError):
            content = "[Erro ao extrair resposta — tenta novamente]"
        
        # Garantir que é sempre string
        if not isinstance(content, str):
            content = str(content) if content else "[Resposta inválida]"

        usage = data.get("usage", {})
        tin = usage.get("prompt_tokens", 0)
        tout = usage.get("completion_tokens", 0)
        modelo_real = data.get("model", self.config.modelo)
        cost = self._custo(tin, tout, modelo_real)

        self.logger.log_api_call(modelo_real, tin, tout, duration_ms)
        return LLMResponse(content, modelo_real, tin, tout, duration_ms, cost)

    def stream(self, messages: list, system_prompt: str = None,
               temperature: float = 0.2, max_tokens: int = 2000):
        """
        Geração em streaming — devolve tokens à medida que chegam.
        Usa-se como gerador: for chunk in brain.stream(...): ...
        """
        msgs = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        msgs.extend(messages)

        headers = {
            "Authorization": f"Bearer {self.config.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/F-i-Red/Tribunal_IA_Portugal",
            "X-Title": "Tribunal IA Portugal",
        }
        payload = {
            "model": self.config.modelo,
            "messages": msgs,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        import json as _json
        with httpx.Client(timeout=self.config.request_timeout) as client:
            with client.stream(
                "POST",
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
            ) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    line = line.strip()
                    if not line or line == "data: [DONE]":
                        continue
                    if line.startswith("data: "):
                        try:
                            data = _json.loads(line[6:])
                            delta = data["choices"][0].get("delta", {})
                            chunk = delta.get("content") or ""
                            if chunk:
                                yield chunk
                        except Exception:
                            continue

    def _custo(self, tin: int, tout: int, modelo: str) -> float:
        """Custo estimado em USD por milhão de tokens."""
        # Modelos gratuitos
        if modelo.endswith(":free") or "free" in modelo:
            return 0.0

        # Tabela de preços (USD por milhão de tokens: input, output)
        tabela = {
            # Anthropic
            "anthropic/claude-haiku-4-5":        (1.0,   5.0),
            "anthropic/claude-sonnet-4.6":        (3.0,  15.0),
            "anthropic/claude-sonnet-4.5":        (3.0,  15.0),
            "anthropic/claude-opus-4.6":          (15.0, 75.0),
            # Google
            "google/gemini-2.0-flash-001":        (0.1,   0.4),
            "google/gemini-2.5-pro":              (1.25,  5.0),
            "google/gemma-3-27b-it":              (0.27,  0.27),
            # Mistral
            "mistralai/mistral-small-24b":        (0.1,   0.3),
            # OpenAI
            "openai/gpt-4.1-mini":               (0.4,   1.6),
            "openai/gpt-4.1":                    (2.0,   8.0),
            # DeepSeek
            "deepseek/deepseek-chat-v3-0324":    (0.27,  1.1),
        }
        ip, op = tabela.get(modelo, (1.0, 3.0))
        return (tin * ip + tout * op) / 1_000_000

    def reset(self):
        self._failures = 0
        self._circuit_open = False
        self._last_failure_time = None


_brain: Optional[TribunalBrain] = None


def get_brain() -> TribunalBrain:
    global _brain
    if _brain is None:
        _brain = TribunalBrain()
    return _brain


def reset_brain():
    global _brain
    _brain = None
