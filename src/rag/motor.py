"""
Motor RAG (Retrieval-Augmented Generation) — Fase 2.

Funciona 100% offline com ficheiros de texto locais.
Sem ChromaDB, sem embeddings pesados, sem dependências externas.

Algoritmo: TF-IDF simplificado + pesquisa por relevância para português jurídico.
"""

import math
import re
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple, Dict


@dataclass
class Fragmento:
    """Fragmento de texto recuperado de uma fonte jurídica."""
    fonte: str          # Nome do ficheiro/diploma
    tipo: str           # "lei", "jurisprudencia", "doutrina"
    titulo: str         # Título do artigo/secção
    conteudo: str       # Texto do fragmento
    relevancia: float   # Score de relevância (0-1)
    artigo: Optional[str] = None   # Ex: "art. 143.º"


class MotorRAG:
    """
    Motor de recuperação de informação jurídica.
    
    Indexa ficheiros .txt das pastas data/leis/ e data/jurisprudencia/
    e recupera fragmentos relevantes para cada consulta.
    """

    # Stopwords portuguesas jurídicas
    STOPWORDS = {
        "a", "o", "as", "os", "um", "uma", "de", "do", "da", "dos", "das",
        "em", "no", "na", "nos", "nas", "por", "para", "com", "sem", "sob",
        "que", "se", "é", "são", "foi", "ser", "ter", "ao", "à", "aos", "às",
        "e", "ou", "mas", "nem", "não", "sim", "já", "ainda", "também",
        "quando", "onde", "como", "porque", "pois", "porém", "contudo",
        "n", "nº", "art", "artigo", "alínea", "número", "parágrafo",
        "lei", "decreto", "código", "diploma",
    }

    def __init__(self, pasta_raiz: Path):
        self.pasta_raiz = pasta_raiz
        self.pasta_leis = pasta_raiz / "data" / "leis"
        self.pasta_jurisprudencia = pasta_raiz / "data" / "jurisprudencia"
        self._indice: List[Fragmento] = []
        self._indexado = False

    def indexar(self) -> int:
        """Indexa todos os ficheiros. Retorna número de fragmentos."""
        self._indice = []
        for pasta, tipo in [
            (self.pasta_leis, "lei"),
            (self.pasta_jurisprudencia, "jurisprudencia"),
        ]:
            if pasta.exists():
                for ficheiro in sorted(pasta.glob("*.txt")):
                    frags = self._processar_ficheiro(ficheiro, tipo)
                    self._indice.extend(frags)
        self._indexado = True
        return len(self._indice)

    def _processar_ficheiro(self, path: Path, tipo: str) -> List[Fragmento]:
        """Divide um ficheiro em fragmentos por artigo/secção."""
        try:
            texto = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return []

        nome = path.stem.replace("_", " ").replace("-", " ")
        fragmentos = []

        # Tentar dividir por artigos
        partes = re.split(
            r"\n(?=(?:Artigo\s+\d+\.?[º°]?|Art\.?\s+\d+\.?[º°]?|ARTIGO\s+\d+))",
            texto, flags=re.IGNORECASE
        )

        if len(partes) > 1:
            # Ficheiro com estrutura de artigos
            for parte in partes:
                parte = parte.strip()
                if len(parte) < 30:
                    continue
                # Extrair número do artigo
                m = re.match(r"(Art(?:igo)?\.?\s+\d+\.?[º°]?[A-Za-z]?)", parte, re.IGNORECASE)
                artigo = m.group(1) if m else None
                titulo = parte[:80].split("\n")[0].strip()

                fragmentos.append(Fragmento(
                    fonte=nome,
                    tipo=tipo,
                    titulo=titulo,
                    conteudo=parte[:1500],
                    relevancia=0.0,
                    artigo=artigo,
                ))
        else:
            # Dividir por blocos de texto (parágrafos)
            blocos = [b.strip() for b in texto.split("\n\n") if len(b.strip()) > 80]
            for i, bloco in enumerate(blocos[:50]):  # máx 50 blocos por ficheiro
                fragmentos.append(Fragmento(
                    fonte=nome,
                    tipo=tipo,
                    titulo=f"{nome} — bloco {i+1}",
                    conteudo=bloco[:1500],
                    relevancia=0.0,
                ))

        return fragmentos

    def _tokenizar(self, texto: str) -> List[str]:
        """Tokeniza texto em palavras, removendo stopwords."""
        palavras = re.findall(r"\b[a-záàâãéêíóôõúçA-ZÁÀÂÃÉÊÍÓÔÕÚÇ]{3,}\b", texto.lower())
        return [p for p in palavras if p not in self.STOPWORDS]

    def _score_bm25(self, query_tokens: List[str], doc_tokens: List[str]) -> float:
        """Score BM25 simplificado."""
        if not doc_tokens or not query_tokens:
            return 0.0
        k1, b = 1.5, 0.75
        avg_len = 200  # comprimento médio estimado
        doc_len = len(doc_tokens)
        freq_map: Dict[str, int] = {}
        for t in doc_tokens:
            freq_map[t] = freq_map.get(t, 0) + 1
        score = 0.0
        for token in set(query_tokens):
            if token in freq_map:
                tf = freq_map[token]
                idf = math.log(1 + (1000 / (1 + 1)))  # IDF simplificado
                numerador = tf * (k1 + 1)
                denominador = tf + k1 * (1 - b + b * doc_len / avg_len)
                score += idf * (numerador / denominador)
        return score

    def pesquisar(self, consulta: str, n_resultados: int = 5,
                  tipo_filtro: Optional[str] = None) -> List[Fragmento]:
        """
        Pesquisa fragmentos relevantes para a consulta.
        
        Args:
            consulta: Texto da consulta (caso, questão jurídica, etc.)
            n_resultados: Número máximo de resultados
            tipo_filtro: "lei", "jurisprudencia" ou None (todos)
        
        Returns:
            Lista de fragmentos ordenados por relevância.
        """
        if not self._indexado:
            self.indexar()

        if not self._indice:
            return []

        query_tokens = self._tokenizar(consulta)
        if not query_tokens:
            return []

        resultados = []
        for frag in self._indice:
            if tipo_filtro and frag.tipo != tipo_filtro:
                continue
            doc_tokens = self._tokenizar(frag.conteudo + " " + frag.titulo)
            score = self._score_bm25(query_tokens, doc_tokens)
            if score > 0:
                frag_copia = Fragmento(
                    fonte=frag.fonte,
                    tipo=frag.tipo,
                    titulo=frag.titulo,
                    conteudo=frag.conteudo,
                    relevancia=round(score, 3),
                    artigo=frag.artigo,
                )
                resultados.append(frag_copia)

        resultados.sort(key=lambda f: f.relevancia, reverse=True)
        return resultados[:n_resultados]

    def formatar_contexto(self, fragmentos: List[Fragmento], max_chars: int = 3000) -> str:
        """Formata fragmentos como contexto para o LLM."""
        if not fragmentos:
            return ""
        linhas = ["=== CONTEXTO JURÍDICO RELEVANTE (RAG) ===\n"]
        total = 0
        for f in fragmentos:
            bloco = (
                f"[{f.tipo.upper()}] {f.fonte}"
                + (f" — {f.artigo}" if f.artigo else "")
                + f"\n{f.conteudo[:600]}\n"
            )
            if total + len(bloco) > max_chars:
                break
            linhas.append(bloco)
            total += len(bloco)
        linhas.append("=== FIM DO CONTEXTO ===\n")
        return "\n".join(linhas)

    def tem_dados(self) -> bool:
        """Verifica se há ficheiros indexados."""
        if not self._indexado:
            self.indexar()
        return len(self._indice) > 0

    def estatisticas(self) -> Dict:
        """Retorna estatísticas do índice."""
        if not self._indexado:
            self.indexar()
        leis = sum(1 for f in self._indice if f.tipo == "lei")
        jurisp = sum(1 for f in self._indice if f.tipo == "jurisprudencia")
        return {
            "total_fragmentos": len(self._indice),
            "fragmentos_leis": leis,
            "fragmentos_jurisprudencia": jurisp,
            "fontes": list(set(f.fonte for f in self._indice)),
        }
