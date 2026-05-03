"""
Motor RAG melhorado — persistência + BM25 melhorado.
"""

import json
import math
import pickle
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..utils.config import get_config


@dataclass
class Fragmento:
    fonte: str
    tipo: str
    titulo: str
    conteudo: str
    relevancia: float
    artigo: Optional[str] = None


class MotorRAG:
    """
    Motor de recuperação jurídica com persistência em disco.
    """

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
        self.pasta_precedentes = pasta_raiz / "data" / "precedentes"
        self._indice: List[Fragmento] = []
        self._doc_freq: Dict[str, int] = {}  # Document frequency para IDF real
        self._indexado = False
        self._index_path = pasta_raiz / "src" / "cache" / "rag_index.pkl"
        self._docfreq_path = pasta_raiz / "src" / "cache" / "rag_docfreq.pkl"

    def indexar(self, forcar: bool = False) -> int:
        """Indexa ficheiros. Usa cache em disco se disponível."""
        if not forcar and self._index_path.exists():
            try:
                with open(self._index_path, "rb") as f:
                    self._indice = pickle.load(f)
                with open(self._docfreq_path, "rb") as f:
                    self._doc_freq = pickle.load(f)
                self._indexado = True
                return len(self._indice)
            except Exception:
                pass  # Falha no cache, reindexar

        self._indice = []
        self._doc_freq = {}
        total_docs = 0

        for pasta, tipo in [
            (self.pasta_leis, "lei"),
            (self.pasta_jurisprudencia, "jurisprudencia"),
            (self.pasta_precedentes, "precedente"),
        ]:
            if pasta.exists():
                for ficheiro in sorted(pasta.glob("*.txt")):
                    frags = self._processar_ficheiro(ficheiro, tipo)
                    self._indice.extend(frags)
                    total_docs += len(frags)

        # Calcular document frequency real
        for frag in self._indice:
            tokens = set(self._tokenizar(frag.conteudo + " " + frag.titulo))
            for t in tokens:
                self._doc_freq[t] = self._doc_freq.get(t, 0) + 1

        self._indexado = True
        self._persistir()
        return len(self._indice)

    def _persistir(self):
        """Guarda índice em disco."""
        try:
            with open(self._index_path, "wb") as f:
                pickle.dump(self._indice, f)
            with open(self._docfreq_path, "wb") as f:
                pickle.dump(self._doc_freq, f)
        except Exception:
            pass

    def _processar_ficheiro(self, path: Path, tipo: str) -> List[Fragmento]:
        try:
            texto = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return []

        nome = path.stem.replace("_", " ").replace("-", " ")
        fragmentos = []

        # Dividir por artigos
        partes = re.split(
            r"\n(?=(?:Artigo\s+\d+\.?[º°]?\|Art\.?\s+\d+\.?[º°]?\|ARTIGO\s+\d+))",
            texto, flags=re.IGNORECASE
        )

        if len(partes) > 1:
            for parte in partes:
                parte = parte.strip()
                if len(parte) < 30:
                    continue
                m = re.match(r"(Art(?:igo)?\.?\s+\d+\.?[º°]?[A-Za-z]?)", parte, re.IGNORECASE)
                artigo = m.group(1) if m else None
                titulo = parte[:80].split("\n")[0].strip()
                fragmentos.append(Fragmento(
                    fonte=nome, tipo=tipo, titulo=titulo,
                    conteudo=parte[:1500], relevancia=0.0, artigo=artigo,
                ))
        else:
            blocos = [b.strip() for b in texto.split("\n\n") if len(b.strip()) > 80]
            for i, bloco in enumerate(blocos[:50]):
                fragmentos.append(Fragmento(
                    fonte=nome, tipo=tipo, titulo=f"{nome} — bloco {i+1}",
                    conteudo=bloco[:1500], relevancia=0.0,
                ))

        return fragmentos

    def _tokenizar(self, texto: str) -> List[str]:
        palavras = re.findall(r"\b[a-záàâãéêíóôõúçA-ZÁÀÂÃÉÊÍÓÔÕÚÇ]{3,}\b", texto.lower())
        return [p for p in palavras if p not in self.STOPWORDS]

    def _score_bm25(self, query_tokens: List[str], doc_tokens: List[str]) -> float:
        if not doc_tokens or not query_tokens:
            return 0.0
        k1, b = 1.5, 0.75
        avg_len = 200
        doc_len = len(doc_tokens)
        freq_map: Dict[str, int] = {}
        for t in doc_tokens:
            freq_map[t] = freq_map.get(t, 0) + 1

        score = 0.0
        N = max(len(self._indice), 1)
        for token in set(query_tokens):
            if token in freq_map:
                tf = freq_map[token]
                df = self._doc_freq.get(token, 1)
                idf = math.log((N - df + 0.5) / (df + 0.5) + 1)  # IDF real
                numerador = tf * (k1 + 1)
                denominador = tf + k1 * (1 - b + b * doc_len / avg_len)
                score += idf * (numerador / denominador)
        return score

    def pesquisar(self, consulta: str, n_resultados: int = 5,
                  tipo_filtro: Optional[str] = None) -> List[Fragmento]:
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
                resultados.append(Fragmento(
                    fonte=frag.fonte, tipo=frag.tipo, titulo=frag.titulo,
                    conteudo=frag.conteudo, relevancia=round(score, 3),
                    artigo=frag.artigo,
                ))

        resultados.sort(key=lambda f: f.relevancia, reverse=True)
        return resultados[:n_resultados]

    def formatar_contexto(self, fragmentos: List[Fragmento], max_chars: int = 3000) -> str:
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
        if not self._indexado:
            self.indexar()
        return len(self._indice) > 0

    def estatisticas(self) -> Dict:
        if not self._indexado:
            self.indexar()
        leis = sum(1 for f in self._indice if f.tipo == "lei")
        jurisp = sum(1 for f in self._indice if f.tipo == "jurisprudencia")
        prec = sum(1 for f in self._indice if f.tipo == "precedente")
        return {
            "total_fragmentos": len(self._indice),
            "fragmentos_leis": leis,
            "fragmentos_jurisprudencia": jurisp,
            "fragmentos_precedentes": prec,
            "fontes": list(set(f.fonte for f in self._indice)),
        }

    def recarregar(self):
        """Força reindexação completa."""
        self._indexado = False
        if self._index_path.exists():
            self._index_path.unlink()
        return self.indexar()
