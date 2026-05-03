"""
Pipeline de processamento de casos judiciais.
"""
from .case_processor import CaseProcessor, process_case
from .instancias import INSTANCIAS, detectar_instancia_por_keywords

__all__ = ["CaseProcessor", "process_case", "INSTANCIAS", "detectar_instancia_por_keywords"]
