# agentes/detetive.py
import datetime
from utils.brain import consultar_ia

MESES_PT = {
    1:"janeiro",2:"fevereiro",3:"março",4:"abril",5:"maio",6:"junho",
    7:"julho",8:"agosto",9:"setembro",10:"outubro",11:"novembro",12:"dezembro"
}
def data_hoje():
    d = datetime.datetime.now()
    return f"{d.day} de {MESES_PT[d.month]} de {d.year}"

SYSTEM_DETETIVE = f"""
Eres o Agente de Instrucao do Tribunal IA Portugal.
A data de hoje é {data_hoje()}.
Responde SEMPRE e EXCLUSIVAMENTE em Portugues de Portugal. NUNCA uses ingles.

O teu papel é o de um magistrado instrutor experiente, com formacao em Direito Processual Penal Portugues.

As tuas funcoes sao:
1. Analisar o relato de forma critica e imparcial.
2. Classificar as provas existentes segundo o CPP.
3. Identificar lacunas factuais que impediriam a boa instrucao do processo.
4. Calcular o Termometro de Evidencia: FRAGIL (🔴), MODERADA (🟡) ou SOLIDA (🟢).
5. Apos as alegacoes dos advogados, identificar pontos por esclarecer que surgiram no debate.

Usa terminologia juridica portuguesa. Tom sobrio, analitico e imparcial.
Quando o caso tiver informacao suficiente, declara PRONTO_PARA_JULGAR: SIM.
"""

class DetetiveJudicial:
    def __init__(self, corpus_legal: str = ""):
        self.corpus_legal = corpus_legal
        self.historico_instrucao = []
        self.termometro = "🔴 FRAGIL"
        self.iteracao = 0

    def analisar_caso(self, descricao_caso: str) -> dict:
        self.iteracao += 1
        contexto_legal = f"\n\nCORPUS LEGISLATIVO:\n{self.corpus_legal[:3000]}" if self.corpus_legal else ""
        prompt = f"""
Analisa o seguinte caso (Iteracao #{self.iteracao}):

RELATO:
{descricao_caso}

HISTORICO DE INSTRUCAO:
{chr(10).join(self.historico_instrucao[-3:]) if self.historico_instrucao else 'Nenhum ainda.'}
{contexto_legal}

Responde APENAS em Portugues de Portugal. Segue EXACTAMENTE este formato:

TERMOMETRO: [🔴 FRAGIL / 🟡 MODERADA / 🟢 SOLIDA]

AVALIACAO: [Dois paragrafos de analise factual rigorosa das provas existentes]

LACUNAS:
- [Lacuna 1 — pergunta concreta ao queixoso]
- [Lacuna 2 — pergunta concreta, se existir]
- [Lacuna 3, se existir]

PRONTO_PARA_JULGAR: [SIM / NAO]
"""
        resposta = consultar_ia(SYSTEM_DETETIVE, prompt, max_tokens=800)
        self.historico_instrucao.append(f"Iteracao {self.iteracao}: {descricao_caso[:150]}...")

        pronto = "PRONTO_PARA_JULGAR: SIM" in resposta.upper() or "PRONTO_PARA_JULGAR:SIM" in resposta.upper()
        if "🟢" in resposta:
            self.termometro = "🟢 SOLIDA"
        elif "🟡" in resposta:
            self.termometro = "🟡 MODERADA"
        else:
            self.termometro = "🔴 FRAGIL"

        lacunas = []
        em_lacunas = False
        for linha in resposta.split("\n"):
            l = linha.strip()
            if "LACUNAS:" in l.upper():
                em_lacunas = True
                continue
            if em_lacunas and l.startswith("-"):
                lacunas.append(l[1:].strip())
            elif em_lacunas and l and not l.startswith("-") and "PRONTO" not in l.upper():
                em_lacunas = False

        return {
            "resposta_completa": resposta,
            "termometro": self.termometro,
            "lacunas": lacunas,
            "pronto": pronto,
            "iteracao": self.iteracao,
        }

    def questoes_pos_debate(self, tese_acusacao: str, tese_defesa: str, caso_completo: str) -> str:
        """
        Intervencao do Detetive APOS as alegacoes dos advogados.
        Identifica pontos do debate que precisam de esclarecimento adicional
        ou que revelam novas questoes a considerar na sentenca.
        """
        prompt = f"""
Acabaram de ser apresentadas as alegacoes da Acusacao e da Defesa.
Como Agente de Instrucao, analisa o debate e identifica:

1. Que pontos divergentes entre acusacao e defesa nao foram suficientemente esclarecidos?
2. Que questoes juridicas levantadas pelos advogados sao relevantes para a sentenca?
3. Que diligencias adicionais, se fossem possiveis, poderiam clarificar o caso?
4. Qual o teu juizo sobre a solidez probatoria, agora que conheces ambas as posicoes?

CASO ORIGINAL (resumo):
{caso_completo[:500]}

ALEGACOES DA ACUSACAO (excerto):
{tese_acusacao[:600]}

ALEGACOES DA DEFESA (excerto):
{tese_defesa[:600]}

Responde em Portugues de Portugal. Tom formal de magistrado instrutor.
Titulo do teu parecer: "NOTA DE INSTRUCAO POS-DEBATE"
Maximo 3 paragrafos concisos.
"""
        return consultar_ia(SYSTEM_DETETIVE, prompt, max_tokens=600)

    def relatorio_para_tribunal(self, caso_completo: str) -> str:
        prompt = f"""
Redige o RELATORIO DE INSTRUCAO formal para o Tribunal Coletivo.
Data: {data_hoje()}. Usa esta data no cabecalho.
Responde APENAS em Portugues de Portugal. NUNCA uses ingles.

CASO COMPLETO:
{caso_completo}

Estrutura obrigatoria:
1. Identificacao do tipo de litigio
2. Identificacao das partes (com [campos em branco] para dados desconhecidos)
3. Resumo factual objetivo
4. Provas e indicios identificados (o que existe E o que nao existe)
5. Termometro de Evidencia com fundamentacao detalhada
6. Enquadramento juridico preliminar com artigos do CP e CPP
7. Lacunas factuais identificadas
8. Conclusao de instrucao e diligencias recomendadas

Seras rigoroso, tecnico e imparcial. Usa a data {data_hoje()} nos cabecalhos.
"""
        return consultar_ia(SYSTEM_DETETIVE, prompt, max_tokens=2000)
