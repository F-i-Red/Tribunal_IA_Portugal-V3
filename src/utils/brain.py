"""
Interface com API via OpenRouter + cache semântico + paralelismo.
Suporte completo a modelos gratuitos (:free).
"""

import asyncio
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

import httpx

from .config import get_config
from .logger import get_logger
from ..cache import get_cache


@dataclass
class LLMResponse:
    content: str
    model: str
    tokens_input: int
    tokens_output: int
    duration_ms: float
    cost_usd: float
    cached: bool = False


class CircuitBreakerOpen(Exception):
    pass


class TribunalBrain:
    def __init__(self):
        self.config = get_config()
        self.logger = get_logger()
        self.cache = get_cache()
        self._failures = 0
        self._failure_threshold = 8
        self._circuit_open = False
        self._last_failure_time: Optional[float] = None
        self._circuit_timeout = 30
        self._total_cost = 0.0
        self._total_calls = 0

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

    def _is_free_model(self, modelo: str) -> bool:
        """Detecta se é um modelo gratuito."""
        return modelo.endswith(":free") or "free" in modelo.lower()

    def call(self, messages: List[Dict], system_prompt: Optional[str] = None,
             temperature: float = 0.3, max_tokens: int = 2000,
             usar_cache: bool = True) -> LLMResponse:
        self._check_circuit()

        # Tentar cache primeiro
        prompt_text = messages[0].get("content", "") if messages else ""
        if usar_cache and self.config.cache_enabled:
            cached = self.cache.get(prompt_text, system_prompt, self.config.modelo)
            if cached:
                self.logger.info("Cache hit — resposta recuperada")
                return LLMResponse(
                    content=cached.response,
                    model=cached.model,
                    tokens_input=cached.tokens_input,
                    tokens_output=cached.tokens_output,
                    duration_ms=0.0,
                    cost_usd=0.0,
                    cached=True,
                )

        max_tentativas = self.config.max_retries
        # Modelos free precisam de mais retries devido a rate limits
        if self._is_free_model(self.config.modelo):
            max_tentativas = max(max_tentativas, 5)

        ultimo_erro = None

        for tentativa in range(1, max_tentativas + 1):
            try:
                resultado = self._chamar_api(
                    messages, system_prompt, temperature, max_tokens
                )
                self._record_success()
                self._total_cost += resultado.cost_usd
                self._total_calls += 1

                # Guardar no cache
                if usar_cache and self.config.cache_enabled:
                    self.cache.put(
                        prompt_text, resultado.content, system_prompt,
                        self.config.modelo, resultado.tokens_input,
                        resultado.tokens_output, resultado.cost_usd
                    )

                return resultado

            except httpx.HTTPStatusError as e:
                codigo = e.response.status_code
                corpo = e.response.text[:400]

                if codigo == 401:
                    raise RuntimeError("❌ Chave API inválida (401). Verifica .env")
                elif codigo == 402:
                    raise RuntimeError("❌ Sem créditos OpenRouter (402).")
                elif codigo == 429:
                    # Rate limit — modelos free são mais restritos
                    espera = 30 * tentativa if self._is_free_model(self.config.modelo) else 20 * tentativa
                    self.logger.warning(f"Rate limit (429). Aguardando {espera}s...")
                    time.sleep(espera)
                    ultimo_erro = "Rate limit (429)"
                    continue
                elif codigo == 400:
                    raise RuntimeError(f"❌ Modelo inválido (400): {self.config.modelo}")
                elif codigo == 503:
                    espera = 20 * tentativa if self._is_free_model(self.config.modelo) else 15 * tentativa
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
        raise RuntimeError(f"❌ API falhou após {max_tentativas} tentativas: {ultimo_erro}")

    async def call_async(self, messages: List[Dict], system_prompt: Optional[str] = None,
                         temperature: float = 0.3, max_tokens: int = 2000) -> LLMResponse:
        """Versão assíncrona para paralelismo."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.call, messages, system_prompt, temperature, max_tokens, False
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

        msgs_completas = []
        if system_prompt:
            msgs_completas.append({"role": "system", "content": system_prompt})
        msgs_completas.extend(messages)

        payload = {
            "model": self.config.modelo,
            "messages": msgs_completas,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        # Modelos free podem precisar de mais tempo
        timeout = self.config.request_timeout
        if self._is_free_model(self.config.modelo):
            timeout = max(timeout, 180)

        with httpx.Client(timeout=timeout) as client:
            resp = client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers, json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        duration_ms = (time.time() - start) * 1000

        try:
            content = data["choices"][0]["message"]["content"]
            if content is None:
                content = (
                    data["choices"][0]["message"].get("reasoning") or
                    data["choices"][0]["message"].get("text") or
                    "[Resposta vazia do modelo]"
                )
        except (KeyError, IndexError, TypeError):
            content = "[Erro ao extrair resposta]"

        if not isinstance(content, str):
            content = str(content) if content else "[Resposta inválida]"

        usage = data.get("usage", {})
        tin = usage.get("prompt_tokens", 0)
        tout = usage.get("completion_tokens", 0)
        modelo_real = data.get("model", self.config.modelo)
        cost = self._custo(tin, tout, modelo_real)

        self.logger.log_api_call(modelo_real, tin, tout, duration_ms)
        return LLMResponse(content, modelo_real, tin, tout, duration_ms, cost, cached=False)

    def _custo(self, tin: int, tout: int, modelo: str) -> float:
        if self._is_free_model(modelo):
            return 0.0

        # Tabela de custos por 1M tokens (input, output)
        tabela = {
            # Anthropic
            "anthropic/claude-haiku-4-5": (1.0, 5.0),
            "anthropic/claude-sonnet-4.6": (3.0, 15.0),
            "anthropic/claude-sonnet-4.5": (3.0, 15.0),
            "anthropic/claude-opus-4.6": (15.0, 75.0),
            # Google
            "google/gemini-2.0-flash-001": (0.1, 0.4),
            "google/gemini-2.0-flash-lite-001": (0.075, 0.3),
            "google/gemini-2.5-flash": (0.15, 0.6),
            "google/gemini-2.5-pro": (1.25, 5.0),
            "google/gemma-3-27b-it": (0.27, 0.27),
            "google/gemma-3-12b-it": (0.15, 0.15),
            # Mistral
            "mistralai/mistral-small-24b": (0.1, 0.3),
            "mistralai/mistral-small-3.1-24b-instruct": (0.1, 0.3),
            # OpenAI
            "openai/gpt-4.1-mini": (0.4, 1.6),
            "openai/gpt-4.1": (2.0, 8.0),
            "openai/gpt-4.1-nano": (0.1, 0.4),
            # DeepSeek
            "deepseek/deepseek-chat-v3-0324": (0.27, 1.1),
            "deepseek/deepseek-chat-v3.1": (0.27, 1.1),
            "deepseek/deepseek-r1": (0.55, 2.19),
            "deepseek/deepseek-r1-0528": (0.55, 2.19),
            # Meta
            "meta-llama/llama-3.3-70b-instruct": (0.12, 0.3),
            "meta-llama/llama-3.1-8b-instruct": (0.02, 0.05),
            # Qwen
            "qwen/qwen3-235b-a22b": (0.8, 2.0),
            "qwen/qwen3-30b-a3b": (0.15, 0.6),
            # MiniMax
            "minimax/minimax-m2.5": (0.28, 1.2),
            # NVIDIA
            "nvidia/nemotron-3-super-120b-a12b": (0.5, 1.5),
        }
        ip, op = tabela.get(modelo, (1.0, 3.0))
        return (tin * ip + tout * op) / 1_000_000

    def get_cost_stats(self) -> Dict:
        return {
            "total_calls": self._total_calls,
            "total_cost_usd": round(self._total_cost, 4),
            "total_cost_eur": round(self._total_cost * 0.92, 4),
        }

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
