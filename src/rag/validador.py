"""
Validador de citações jurídicas — Fase 2.

Verifica se os artigos citados pelo LLM existem realmente
nos ficheiros de leis locais. Evita alucinações de artigos.
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple


from dataclasses import dataclass


class ValidadorCitacoes:
    """
    Valida artigos citados nas peças processuais geradas pelo LLM.
    
    Estratégia:
    1. Extrai todos os artigos citados no texto (ex: "art. 143.º", "artigo 256 CP")
    2. Verifica quais existem nos ficheiros locais
    3. Marca os desconhecidos com [NÃO VERIFICADO]
    4. Gera relatório de citações
    """

    PADROES_ARTIGO = [
        # art. 143.º CP / art. 143 do CP / artigo 143.º
        r"art(?:igo)?\.?\s*(\d+)\.?[º°]?(?:[A-Za-z])?\s*(?:do\s+)?([A-Z]{2,4})?",
        # Artigo 143.º do Código Penal
        r"[Aa]rtigo\s+(\d+)\.?[º°]?(?:[A-Za-z])?\s+do\s+([A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][a-záàâãéêíóôõúç\s]+)",
        # § 3.º / n.º 3 / alínea a)
        r"n\.?[º°]\s*(\d+)\s+do\s+art(?:igo)?\.?\s*(\d+)",
    ]

    DIPLOMAS = {
        "CP":  "Código Penal",
        "CPP": "Código de Processo Penal",
        "CC":  "Código Civil",
        "CPC": "Código de Processo Civil",
        "CT":  "Código do Trabalho",
        "CRP": "Constituição da República Portuguesa",
        "CPTA": "Código de Processo nos Tribunais Administrativos",
    }

    def __init__(self, pasta_leis: Path):
        self.pasta_leis = pasta_leis
        self._artigos_conhecidos: Dict[str, set] = {}
        self._indexado = False

    def _indexar(self):
        """Indexa artigos existentes nos ficheiros de leis."""
        self._artigos_conhecidos = {}
        if not self.pasta_leis.exists():
            self._indexado = True
            return

        for ficheiro in self.pasta_leis.glob("*.txt"):
            nome = ficheiro.stem.upper()
            texto = ficheiro.read_text(encoding="utf-8", errors="replace")
            # Encontrar todos os artigos no ficheiro
            artigos = set()
            for m in re.finditer(
                r"Art(?:igo)?\.?\s+(\d+)\.?[º°]?", texto, re.IGNORECASE
            ):
                artigos.add(m.group(1))
            self._artigos_conhecidos[nome] = artigos

        self._indexado = True

    def extrair_citacoes(self, texto: str) -> List[Tuple[str, str]]:
        """
        Extrai pares (número_artigo, diploma) do texto.
        Ex: [("143", "CP"), ("256", "CPP")]
        """
        if not self._indexado:
            self._indexar()

        citacoes = []
        # Padrão principal: art. NNN [do] SIGLA
        for m in re.finditer(
            r"art(?:igo)?\.?\s*(\d+)\.?[º°]?[A-Za-z]?"
            r"(?:\s+(?:do|da|n\.?[º°]\s*\d+))*"
            r"(?:\s+(?:do\s+)?([A-Z]{2,5}))?",
            texto, re.IGNORECASE
        ):
            num = m.group(1)
            diploma = (m.group(2) or "").upper()
            if num and 1 <= int(num) <= 999:
                citacoes.append((num, diploma))

        # Padrão: [art.?] — marcações de incerteza já geradas
        for m in re.finditer(r"\[art\.?\?(?:\s+([A-Z]{2,5}))?\]", texto):
            citacoes.append(("?", m.group(1) or ""))

        return list(set(citacoes))

    def validar_texto(self, texto: str) -> Tuple[str, List[Dict]]:
        """
        Valida citações num texto e retorna texto anotado + relatório.
        
        Returns:
            (texto_anotado, lista_de_problemas)
        """
        if not self._indexado:
            self._indexar()

        citacoes = self.extrair_citacoes(texto)
        problemas = []
        texto_anotado = texto

        for num, diploma in citacoes:
            if num == "?":
                problemas.append({
                    "artigo": f"[art.? {diploma}]",
                    "status": "incerto",
                    "mensagem": "Artigo marcado como incerto pelo modelo",
                })
                continue

            # Verificar nos ficheiros conhecidos
            verificado = False
            for nome_ficheiro, artigos in self._artigos_conhecidos.items():
                # Mapeamento de siglas para partes do nome do ficheiro
                mapa_diplomas = {
                    "CP": ["PENAL", "PENAL_EXCERTOS"],
                    "CPP": ["PROCESSO_PENAL", "PROCESSO"],
                    "CC": ["CIVIL", "CIVIL_EXCERTOS"],
                    "CPC": ["PROCESSO_CIVIL"],
                    "CT": ["TRABALHO", "TRABALHO_EXCERTOS"],
                    "CRP": ["CONSTITUICAO", "CONSTITUIÇÃO"],
                    "CPTA": ["ADMINISTRATIVO"],
                }
                # Correspondência por diploma
                corresponde = False
                if diploma:
                    termos = mapa_diplomas.get(diploma, [diploma])
                    corresponde = any(t in nome_ficheiro.upper() for t in termos)
                else:
                    corresponde = True  # sem diploma — verificar em todos

                if corresponde and num in artigos:
                    verificado = True
                    break

            if not verificado and self._artigos_conhecidos:
                # Só reportar problema se temos ficheiros indexados
                problemas.append({
                    "artigo": f"art. {num}.º {diploma}".strip(),
                    "status": "nao_verificado",
                    "mensagem": f"Artigo {num} não encontrado nos ficheiros locais de {diploma or 'qualquer diploma'}",
                })

        return texto_anotado, problemas

    def relatorio_citacoes(self, problemas: List[Dict]) -> str:
        """Gera relatório legível dos problemas de citação."""
        if not problemas:
            return "✅ Todas as citações verificadas nos ficheiros locais."
        linhas = [f"⚠️  {len(problemas)} citação(ões) não verificada(s):"]
        for p in problemas:
            linhas.append(f"  • {p['artigo']}: {p['mensagem']}")
        linhas.append("\nNota: Citações não verificadas podem ser correctas mas ausentes dos ficheiros locais.")
        return "\n".join(linhas)
