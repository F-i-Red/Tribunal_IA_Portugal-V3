"""
Logger estruturado em JSON + tracking de custos por caso.
"""

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional


class TribunalLogger:
    def __init__(self, level: str = "INFO"):
        self._logger = logging.getLogger("tribunal_ia")
        self._logger.setLevel(getattr(logging, level, logging.INFO))
        self._trace_id = "no-trace"
        self._case_id = "no-case"
        self._agent = "system"
        self._cost_log: List[Dict] = []

        if not self._logger.handlers:
            os.makedirs("logs", exist_ok=True)
            fh = logging.FileHandler("logs/tribunal.log", encoding="utf-8")
            fh.setFormatter(logging.Formatter("%(message)s"))
            self._logger.addHandler(fh)
            ch = logging.StreamHandler()
            ch.setLevel(logging.CRITICAL)
            self._logger.addHandler(ch)

    def _log(self, level: str, message: str, **extra):
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "agent": self._agent,
            "trace_id": self._trace_id,
            "case_id": self._case_id,
            "message": message,
            **extra,
        }
        getattr(self._logger, level.lower())(json.dumps(record, ensure_ascii=False))

    def info(self, msg: str, **kw): self._log("INFO", msg, **kw)
    def error(self, msg: str, **kw): self._log("ERROR", msg, **kw)
    def warning(self, msg: str, **kw): self._log("WARNING", msg, **kw)

    def start_case(self, description: str) -> str:
        self._trace_id = uuid.uuid4().hex[:8]
        self._case_id = f"case_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        self._cost_log = []
        self._log("INFO", "Novo caso iniciado", event="case_started",
                  case_description_hash=hash(description))
        return self._trace_id

    def set_agent(self, agent: str):
        self._agent = agent

    def log_anonymization(self, entities_found: int, entity_types: List[str]):
        self._log("INFO", "Anonimização aplicada", event="anonymization",
                  entities_found=entities_found, entity_types=entity_types)

    def log_api_call(self, model: str, tokens_input: int, tokens_output: int, duration_ms: float):
        cost = self._estimate_cost(tokens_input, tokens_output, model)
        entry = {
            "model": model,
            "tokens_input": tokens_input,
            "tokens_output": tokens_output,
            "duration_ms": round(duration_ms, 1),
            "cost_usd": round(cost, 6),
        }
        self._cost_log.append(entry)
        self._log("INFO", "Chamada API concluída", event="api_call", **entry)

    def log_cost_summary(self):
        total = sum(e["cost_usd"] for e in self._cost_log)
        self._log("INFO", "Resumo de custos do caso", event="cost_summary",
                  total_calls=len(self._cost_log),
                  total_cost_usd=round(total, 4),
                  total_cost_eur=round(total * 0.92, 4))

    def _estimate_cost(self, tin: int, tout: int, model: str) -> float:
        if "free" in model:
            return 0.0
        # Fallback estimativa
        return (tin + tout) * 0.001 / 1000  # ~$1/M tokens médio

    def log_agent_action(self, agent: str, action: str, data: Dict = None):
        self._log("INFO", f"Agente {agent}: {action}", event="agent_action",
                  agent_name=agent, action=action, **(data or {}))

    def get_case_cost(self) -> Dict:
        total = sum(e["cost_usd"] for e in self._cost_log)
        return {
            "calls": len(self._cost_log),
            "total_usd": round(total, 4),
            "total_eur": round(total * 0.92, 4),
        }


_logger: Optional[TribunalLogger] = None


def get_logger() -> TribunalLogger:
    global _logger
    if _logger is None:
        _logger = TribunalLogger()
    return _logger
