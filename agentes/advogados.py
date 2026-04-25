# agentes/advogados.py
import datetime
from utils.brain import consultar_ia

MESES_PT = {
    1:"janeiro",2:"fevereiro",3:"março",4:"abril",5:"maio",6:"junho",
    7:"julho",8:"agosto",9:"setembro",10:"outubro",11:"novembro",12:"dezembro"
}
def data_hoje():
    d = datetime.datetime.now()
    return f"{d.day} de {MESES_PT[d.month]} de {d.year}"

SYSTEM_ACUSACAO = f"""
Eres o Representante da Acusacao no Tribunal IA Portugal.
A data de hoje é {data_hoje()}. Usa esta data nos documentos.
Responde SEMPRE e EXCLUSIVAMENTE em Portugues de Portugal. NUNCA uses ingles.

Perfil: Procurador do Ministerio Publico experiente e rigoroso.
- Cita artigos reais dos Codigos Penal, Civil, etc.
- Usa a formula: "Nos termos do Art. X.o do Codigo Y..."
- Tom formal: "Meritissimo Juiz", "Vossa Excelencia", "Exmo. Senhor Presidente"
- NUNCA inventes artigos. Se nao souberes, diz "conforme jurisprudencia dominante".
"""

SYSTEM_DEFESA = f"""
Eres o Patrono da Defesa no Tribunal IA Portugal.
A data de hoje é {data_hoje()}. Usa esta data nos documentos.
Responde SEMPRE e EXCLUSIVAMENTE em Portugues de Portugal. NUNCA uses ingles.

Perfil: Advogado Garantista especialista em Direito Constitucional e Processual Penal.
- Garante o contraditorio, invoca in dubio pro reo e direitos fundamentais (CRP Art. 32.o)
- Busca causas de exclusao de ilicitude ou culpa
- Invoca circunstancias atenuantes (Art. 71.o e 72.o do CP)
- Tom formal: "Meritissimo Juiz", "Douto Tribunal"
- NUNCA inventes artigos. Se nao souberes, diz "conforme principios constitucionais".
"""

class Acusacao:
    def __init__(self, corpus_legal: str = ""):
        self.corpus_legal = corpus_legal

    def construir_alegacoes(self, relatorio_instrucao: str) -> str:
        contexto = f"\n\nLEGISLACAO:\n{self.corpus_legal[:2500]}" if self.corpus_legal else ""
        prompt = f"""
Constroi as ALEGACOES DE ACUSACAO formais para audiencia de julgamento.
Responde APENAS em Portugues de Portugal. NUNCA uses ingles.

RELATORIO DE INSTRUCAO:
{relatorio_instrucao[:1500]}
{contexto}

Estrutura:
1. Cabecalho formal
2. Qualificacao juridica dos factos (tipicidade) com citacao de artigos
3. Demonstracao da ilicitude
4. Prova do elemento subjetivo (dolo ou negligencia)
5. Pedido concreto (pena sugerida, indemnizacao, etc.)
6. Subscricao formal
"""
        return consultar_ia(SYSTEM_ACUSACAO, prompt, max_tokens=1200)

class Defesa:
    def __init__(self, corpus_legal: str = ""):
        self.corpus_legal = corpus_legal

    def construir_alegacoes(self, relatorio_instrucao: str, tese_acusacao: str) -> str:
        contexto = f"\n\nLEGISLACAO:\n{self.corpus_legal[:2500]}" if self.corpus_legal else ""
        prompt = f"""
Constroi as ALEGACOES DE DEFESA formais para audiencia de julgamento.
Responde APENAS em Portugues de Portugal. NUNCA uses ingles.

RELATORIO DE INSTRUCAO:
{relatorio_instrucao[:1000]}

ALEGACOES DA ACUSACAO:
{tese_acusacao[:800]}
{contexto}

Estrutura:
1. Cabecalho formal
2. Contradicao ponto-a-ponto das teses da acusacao
3. Invocacao de causas de exclusao de ilicitude ou culpa (se aplicavel)
4. Argumento do in dubio pro reo e dos direitos fundamentais
5. Circunstancias atenuantes a considerar
6. Pedido concreto (absolvicao, pena minima, suspensao)
7. Subscricao formal
"""
        return consultar_ia(SYSTEM_DEFESA, prompt, max_tokens=1200)
