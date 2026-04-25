# agentes/juiz.py
import datetime
from utils.brain import consultar_ia

MESES_PT = {
    1:"janeiro",2:"fevereiro",3:"março",4:"abril",5:"maio",6:"junho",
    7:"julho",8:"agosto",9:"setembro",10:"outubro",11:"novembro",12:"dezembro"
}
def data_hoje():
    d = datetime.datetime.now()
    return f"{d.day} de {MESES_PT[d.month]} de {d.year}"

SYSTEM_JUIZ_BASE = f"""
Eres um membro do Coletivo de Juizes do Tribunal IA Portugal.
A data de hoje é {data_hoje()}. Usa esta data na sentenca.
Responde SEMPRE e EXCLUSIVAMENTE em Portugues de Portugal. NUNCA uses ingles.

Proferes sentenças formais com a estrutura obrigatoria do Direito Portugues:
1. RELATORIO — Identificacao das partes, objeto e historico processual.
2. SANEAMENTO — Regularidade processual e excecoes.
3. FUNDAMENTACAO DE FACTO — O que ficou provado e o que nao ficou.
4. FUNDAMENTACAO DE DIREITO — Silogismo juridico: norma + factos = decisao.
5. DISPOSITIVO — A decisao final concreta (condenar/absolver/improceder/proceder).

Linguagem juridica formal e erudita. Cita artigos dos Codigos relevantes.
NUNCA inventes artigos. Usa "conforme jurisprudencia dominante" quando necessario.
O DISPOSITIVO deve ter uma decisao clara e concreta — nunca vague.
"""

INSTRUCOES_RIGOROSA = """
Perfil: JUIZ LEGALISTA-RIGOROSO
- Aplicacao estrita e literal da lei.
- Prioridade: punibilidade, proporcionalidade da pena, deterrencia.
- Interpreta a lei em favor da norma, nao do reu.
- Em caso de duvida sobre a pena, escolhe a mais elevada dentro do quadro legal.
- O Dispositivo deve condenar se houver qualquer indicio, mesmo fragil.
"""

INSTRUCOES_GARANTISTA = """
Perfil: JUIZ GARANTISTA-CONSTITUCIONAL
- Prioridade: direitos fundamentais, in dubio pro reo, proporcionalidade.
- Interpreta a lei em conformidade com a CRP, Art. 32.o.
- Em caso de duvida probatoria, absolve ou aplica a pena minima.
- O Dispositivo deve absolver se a prova for insuficiente.
"""

INSTRUCOES_EQUILIBRADA = """
Perfil: JUIZ PRAGMATICO-EQUILIBRADO
- Pondera ambas as teses, busca a solucao mais justa.
- Considera o impacto social e a equidade.
- Pode propor penas alternativas (suspensao, indemnizacao, prestacao de trabalho).
- O Dispositivo deve ser concreto: condenar com pena especifica OU absolver com fundamentacao.
"""

class ColetivoJuizes:
    def __init__(self, corpus_legal: str = ""):
        self.corpus_legal = corpus_legal

    def deliberar(self, relatorio: str, acusacao: str, defesa: str) -> dict:
        return {
            "Rigorosa": self._sentenca(INSTRUCOES_RIGOROSA, "JUIZ LEGALISTA-RIGOROSO", relatorio, acusacao, defesa),
            "Garantista": self._sentenca(INSTRUCOES_GARANTISTA, "JUIZ GARANTISTA-CONSTITUCIONAL", relatorio, acusacao, defesa),
            "Equilibrada": self._sentenca(INSTRUCOES_EQUILIBRADA, "JUIZ PRAGMATICO-EQUILIBRADO", relatorio, acusacao, defesa),
        }

    def _sentenca(self, instrucoes: str, nome_perfil: str, relatorio: str, acusacao: str, defesa: str) -> str:
        contexto = f"\n\nCORPUS LEGISLATIVO:\n{self.corpus_legal[:2000]}" if self.corpus_legal else ""
        prompt = f"""
Profere uma SENTENCA COMPLETA no perfil: {nome_perfil}

{instrucoes}

MATERIAL PROCESSUAL:
--- RELATORIO DE INSTRUCAO ---
{relatorio[:1200]}

--- ALEGACOES DA ACUSACAO (resumo) ---
{acusacao[:600]}

--- ALEGACOES DA DEFESA (resumo) ---
{defesa[:600]}
{contexto}

OBRIGATORIO: Termina SEMPRE com um DISPOSITIVO claro e concreto.
Responde APENAS em Portugues de Portugal. NUNCA uses ingles.
"""
        return consultar_ia(SYSTEM_JUIZ_BASE, prompt, max_tokens=2000)
