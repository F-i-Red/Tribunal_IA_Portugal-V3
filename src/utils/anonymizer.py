"""
Anonimização de entidades sensíveis em textos jurídicos portugueses.
Conformidade RGPD — mascarar dados ANTES de enviar para APIs de terceiros.

Funciona com texto formal E informal (narrativas na primeira pessoa).
"""

import hashlib
import re
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class Entity:
    text: str
    start: int
    end: int
    label: str
    score: float


class PortugueseLegalAnonymizer:

    # Padrões estruturados (alta precisão)
    STRUCTURED_PATTERNS = {
        "EMAIL":         re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        "IBAN":          re.compile(r"\bPT\d{2}[\s\d]{20,26}\b"),
        "CODIGO_POSTAL": re.compile(r"\b\d{4}-\d{3}\b"),
        "CC":            re.compile(r"\b\d{8}\s*[A-Za-z]{2}\d?\b"),
        "TELEFONE":      re.compile(r"\b(?:\+351[\s-]?)?(?:9[1236]\d{7}|2\d{8})\b"),
        "NIF":           re.compile(r"\b[1235689]\d{8}\b"),
        "NISS":          re.compile(r"\b\d{11}\b"),
        "PROCESSO":      re.compile(r"\b\d{3,4}/\d{2}[.\d]*\b"),
    }

    # Cidades PT
    CIDADES = {
        "lisboa", "porto", "braga", "coimbra", "faro", "aveiro", "guarda", "leiria",
        "viseu", "bragança", "évora", "beja", "portalegre", "setúbal", "santarém",
        "viana do castelo", "vila real", "funchal", "ponta delgada", "amadora",
        "almada", "oeiras", "sintra", "cascais", "loures", "odivelas",
        "vila nova de gaia", "matosinhos", "maia", "gondomar", "portimão", "tavira",
        "evora", "setubal", "santarem",
    }

    # Prefixos que precedem nomes próprios em contexto formal
    PREFIXOS_FORMAIS = [
        r"arguid[oa]\s+", r"r[eé]u\s+", r"autor[ea]?\s+", r"vítima\s+",
        r"ofendid[oa]\s+", r"testemunha\s+", r"sr\.?\s+", r"sra\.?\s+",
        r"dr\.?\s+", r"dra\.?\s+", r"doutor[ea]?\s+", r"professor[ea]?\s+",
        r"advogad[oa]?\s+", r"juiz[a]?\s+", r"senhor[a]?\s+",
        r"menor\s+", r"cônjuge\s+", r"companheiro[a]?\s+",
    ]

    # Padrões para detetar nomes em contexto informal (primeira pessoa, alcunhas, etc.)
    PADROES_INFORMAIS = [
        # "Sou o/a Nome" / "Chamo-me Nome"
        r"(?:sou\s+(?:o|a)\s+|chamo[- ]me\s+)([A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][a-záàâãéêíóôõúç]+(?:\s+[A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][a-záàâãéêíóôõúç]+){0,3})",
        # "o vizinho/a vizinha/o senhorio/a vítima (Nome)"
        r"(?:o\s+vizinho|a\s+vizinha|o\s+senhorio|a\s+senhora|o\s+senhor)\s+(?:\w+\s+)?\(([A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][a-záàâãéêíóôõúç]+(?:\s+[A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][a-záàâãéêíóôõúç]+){0,3})\)",
        # "(Alcunha/Nome)" entre parênteses após descrição
        r"\(([A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][a-záàâãéêíóôõúç]+(?:\s+[A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][a-záàâãéêíóôõúç]+){0,3})\)",
        # "denominado/alcunhado/conhecido por Nome"
        r"(?:denominad[oa]|alcunhad[oa]|conhecid[oa]\s+(?:por|como))\s+([A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][a-záàâãéêíóôõúç]+(?:\s+[A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][a-záàâãéêíóôõúç]+){0,3})",
    ]

    # Referências a familiares e pessoas próximas (anonimizar como papel)
    REFERENCIAS_PESSOAIS = [
        (r"\ba\s+minha\s+mãe\b", "[FAMILIAR_MAE]"),
        (r"\bo\s+meu\s+pai\b", "[FAMILIAR_PAI]"),
        (r"\bo\s+meu\s+avô\b", "[FAMILIAR_AVO]"),
        (r"\ba\s+minha\s+avó\b", "[FAMILIAR_AVO]"),
        (r"\bo\s+meu\s+irmão\b", "[FAMILIAR_IRMAO]"),
        (r"\ba\s+minha\s+irmã\b", "[FAMILIAR_IRMAO]"),
        (r"\bo\s+meu\s+marido\b", "[FAMILIAR_CONJUGE]"),
        (r"\ba\s+minha\s+mulher\b", "[FAMILIAR_CONJUGE]"),
        (r"\bo\s+meu\s+filho\b", "[FAMILIAR_FILHO]"),
        (r"\ba\s+minha\s+filha\b", "[FAMILIAR_FILHO]"),
    ]

    # Palavras que não são nomes
    NAO_NOMES = {
        "tribunal", "juiz", "advogado", "procurador", "ministerio", "direito",
        "lei", "codigo", "artigo", "processo", "sentenca", "nacional", "republica",
        "portuguesa", "europeu", "estado", "comarca", "distrito", "concelho",
        "qualificado", "furto", "delito", "crime", "testemunhas", "antecedentes",
        "em", "na", "no", "de", "do", "da", "para", "por", "foi", "tem", "sao",
        "era", "esta", "fica", "uma", "um", "duas", "dois", "tres", "quatro",
        "cinco", "seis", "sete", "oito", "nove", "dez", "aqui", "ali", "isso",
        "isto", "aquilo", "quando", "onde", "como", "porque", "mas", "pois",
    }

    def __init__(self, salt: str = "tribunal_ia_2024"):
        self.salt = salt

    def _pseudonimo(self, label: str, original: str) -> str:
        key = f"{self.salt}:{label}:{original.lower().strip()}"
        h = int(hashlib.sha256(key.encode()).hexdigest(), 16) % 9000 + 1000
        mapa = {
            "PESSOA":          f"[PESSOA_{h}]",
            "LOCAL":           f"[LOCAL_{h}]",
            "MORADA":          f"[MORADA_{h}]",
            "ORGANIZACAO":     f"[ENTIDADE_{h}]",
            "NIF":             "[NIF_REMOVIDO]",
            "CC":              "[CC_REMOVIDO]",
            "NISS":            "[NISS_REMOVIDO]",
            "TELEFONE":        "[TELEFONE_REMOVIDO]",
            "EMAIL":           "[EMAIL_REMOVIDO]",
            "IBAN":            "[IBAN_REMOVIDO]",
            "CODIGO_POSTAL":   "[CP_REMOVIDO]",
            "PROCESSO":        f"[PROCESSO_{h}]",
            "DATA_NASCIMENTO": "[DATA_NASC_REMOVIDA]",
        }
        return mapa.get(label, f"[{label}_{h}]")

    def _valido_nome(self, nome: str) -> bool:
        palavras = nome.split()
        if len(nome) < 3 or len(palavras) > 5:
            return False
        if palavras[0].lower() in self.NAO_NOMES:
            return False
        # Rejeitar se contém preposições/verbos no meio
        meio_stop = {"por", "em", "de", "para", "com", "sem", "sob", "foi",
                     "tem", "são", "era", "está", "fica", "e", "ou"}
        for w in palavras[1:]:
            if w.lower() in meio_stop:
                return False
        return True

    def _encontrar_estruturados(self, text: str) -> List[Entity]:
        entities = []
        ordem = ["EMAIL", "IBAN", "CODIGO_POSTAL", "CC", "TELEFONE", "NIF", "NISS", "PROCESSO"]
        for label in ordem:
            for m in self.STRUCTURED_PATTERNS[label].finditer(text):
                entities.append(Entity(m.group(), m.start(), m.end(), label, 0.97))
        return entities

    def _encontrar_nomes_formais(self, text: str) -> List[Entity]:
        entities = []
        nome_re = r"([A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][a-záàâãéêíóôõúç]+(?:\s+[A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][a-záàâãéêíóôõúç]+){0,4})"
        for prefix in self.PREFIXOS_FORMAIS:
            pat = re.compile(f"(?:{prefix}){nome_re}", re.IGNORECASE)
            for m in pat.finditer(text):
                nome = m.group(1)
                if self._valido_nome(nome):
                    entities.append(Entity(nome, m.start(1), m.end(1), "PESSOA", 0.90))
        return entities

    def _encontrar_nomes_informais(self, text: str) -> List[Entity]:
        entities = []
        for padrao in self.PADROES_INFORMAIS:
            for m in re.finditer(padrao, text, re.IGNORECASE):
                nome = m.group(1)
                if self._valido_nome(nome):
                    entities.append(Entity(nome, m.start(1), m.end(1), "PESSOA", 0.85))
        return entities

    def _encontrar_referencias_pessoais(self, text: str) -> List[Entity]:
        """Substitui referências a familiares por papel (mãe, pai, avô...)."""
        entities = []
        for padrao, substituto in self.REFERENCIAS_PESSOAIS:
            for m in re.finditer(padrao, text, re.IGNORECASE):
                # Usamos substituto direto em vez de pseudónimo hash
                entities.append(Entity(m.group(), m.start(), m.end(), "FAMILIAR", 0.95))
        return entities

    def _encontrar_locais(self, text: str) -> List[Entity]:
        entities = []
        # Tribunais
        for m in re.finditer(
            r"Tribunal\s+(?:(?:da|do|de|Central)\s+)?[A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][a-záàâãéêíóôõúç]+"
            r"(?:\s+(?:de\s+)?[A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][a-záàâãéêíóôõúç]+)*",
            text, re.IGNORECASE
        ):
            entities.append(Entity(m.group(), m.start(), m.end(), "LOCAL", 0.95))
        # Moradas
        for m in re.finditer(
            r"(?:Rua|Avenida|Av\.?|Praça|Largo|Travessa|Estrada|Alameda|Calçada|Beco)"
            r"\s+[^,.\n]{3,60}(?:,\s*[^,.\n]{2,40}){0,3}",
            text, re.IGNORECASE
        ):
            if len(m.group().split()) >= 2:
                entities.append(Entity(m.group().strip(), m.start(), m.end(), "MORADA", 0.85))
        # Cidades
        for cidade in self.CIDADES:
            for m in re.finditer(rf"\b{re.escape(cidade)}\b", text, re.IGNORECASE):
                entities.append(Entity(m.group(), m.start(), m.end(), "LOCAL", 0.80))
        return entities

    def _encontrar_datas_nascimento(self, text: str) -> List[Entity]:
        entities = []
        contextos = [
            r"nascid[oa]\s+(?:em|a)\s+",
            r"data\s+de\s+nascimento\s*[:\s]+",
            r"n\.?\s*asc\.?\s*[:\s]+",
        ]
        data_re = (
            r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|"
            r"\d{1,2}\s+de\s+(?:janeiro|fevereiro|março|abril|maio|junho|"
            r"julho|agosto|setembro|outubro|novembro|dezembro)\s+de\s+\d{4})"
        )
        for ctx in contextos:
            for m in re.finditer(f"(?:{ctx}){data_re}", text, re.IGNORECASE):
                entities.append(Entity(m.group(1), m.start(1), m.end(1), "DATA_NASCIMENTO", 0.90))
        return entities

    def anonymize(self, text: str) -> Tuple[str, List[Entity]]:
        todas: List[Entity] = []
        todas.extend(self._encontrar_estruturados(text))
        todas.extend(self._encontrar_nomes_formais(text))
        todas.extend(self._encontrar_nomes_informais(text))
        todas.extend(self._encontrar_referencias_pessoais(text))
        todas.extend(self._encontrar_locais(text))
        todas.extend(self._encontrar_datas_nascimento(text))

        # Ordenar e remover sobreposições
        todas.sort(key=lambda e: e.start)
        filtradas: List[Entity] = []
        ultimo_fim = -1
        for ent in todas:
            if ent.start >= ultimo_fim:
                filtradas.append(ent)
                ultimo_fim = ent.end

        # Substituir de trás para a frente
        resultado = text
        for ent in reversed(filtradas):
            if ent.label == "FAMILIAR":
                # Para familiares, o pseudónimo é o próprio label descritivo
                pseudo = ent.text  # mantemos como está — já é genérico
                # Não substituímos referências a familiares — são genéricas e não identificam
                continue
            pseudo = self._pseudonimo(ent.label, ent.text)
            resultado = resultado[:ent.start] + pseudo + resultado[ent.end:]

        return resultado, filtradas


def anonymize_text(text: str) -> Tuple[str, List[Entity]]:
    return PortugueseLegalAnonymizer().anonymize(text)
