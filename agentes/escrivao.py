# agentes/escrivao.py
import os
import datetime
from utils.brain import consultar_ia

MESES_PT = {
    1:"janeiro",2:"fevereiro",3:"março",4:"abril",5:"maio",6:"junho",
    7:"julho",8:"agosto",9:"setembro",10:"outubro",11:"novembro",12:"dezembro"
}
def data_hoje():
    d = datetime.datetime.now()
    return f"{d.day} de {MESES_PT[d.month]} de {d.year}"

SYSTEM_ESCRIVAO = f"""
Eres o Escrivao de Direito do Tribunal IA Portugal.
A data de hoje é {data_hoje()}.
Responde SEMPRE e EXCLUSIVAMENTE em Portugues de Portugal. NUNCA uses ingles.

Para a traducao em linguagem vulgar:
- Frases simples e curtas. Tom amigavel e calmo.
- Evita jargao juridico. Se o usas, explica entre parenteses.
- Uma crianca de 10 anos deve conseguir perceber o essencial.
- Maximo 4 paragrafos curtos.
"""

class EscrivaoDireito:
    def __init__(self):
        self.numero_processo = datetime.datetime.now().strftime("%Y/%m%d-%H%M")
        agora = datetime.datetime.now()
        self.data_pt = f"{agora.day} de {MESES_PT[agora.month]} de {agora.year}, {agora.strftime('%H:%M')}"

    def traduzir_sentenca(self, sentenca_tecnica: str, nome_perfil: str) -> str:
        if not sentenca_tecnica or sentenca_tecnica.startswith("❌"):
            return f"📖 EM LINGUAGEM SIMPLES ({nome_perfil.upper()}): [Tradução não disponível.]"
        prompt = f"""
Traduz a seguinte sentenca juridica para linguagem simples e acessivel.
Responde APENAS em Portugues de Portugal. NUNCA uses ingles.
Maximo 4 paragrafos curtos.

SENTENCA:
{sentenca_tecnica[:2000]}

Comeca SEMPRE com: "📖 EM LINGUAGEM SIMPLES ({nome_perfil.upper()}):"

Explica: (1) o que aconteceu no caso, (2) o que o juiz decidiu e porque, (3) o que isso significa na pratica.
"""
        return consultar_ia(SYSTEM_ESCRIVAO, prompt, max_tokens=500)

    def calcular_custas(self) -> dict:
        return {
            "Taxas de Justiça (DRE/RCP)": "204,00 € a 612,00 € (processos simples) / até 25.500,00 € (processos complexos)",
            "Honorários de Advogado (estimativa)": "750,00 € a 5.000,00 € (1.ª instância, caso simples a moderado)",
            "Tempo Médio de Resolução": "12 a 36 meses (1.ª instância) / 24 a 60 meses (com recurso)",
            "Alternativa - Julgados de Paz": "Grátis até 15.000,00 € em litígios elegíveis (julgadosdepaz.mj.pt)",
            "Apoio Judiciário": "Disponível para cidadãos com carências económicas (Art. 20.º CRP)"
        }

    def redigir_ata_final(self, caso_original, relatorio_instrucao, nota_pos_debate, tese_acusacao, tese_defesa, sentencas, traducoes):
        custas = self.calcular_custas()
        sep = "=" * 72
        linha = "-" * 72
        ata = f"""
{sep}
🏛️  TRIBUNAL IA PORTUGAL — ATA DE AUDIÊNCIA DE DISCUSSÃO E JULGAMENTO
{sep}
PROCESSO N.º: {self.numero_processo}-AUTO
DATA: {self.data_pt}
TRIBUNAL: Tribunal IA Portugal (Simulação Jurídica Educativa)
COLETIVO: Magistrado-Presidente IA, Representante da Acusação IA, Patrono da Defesa IA

{linha}
I. OBJETO DO LITÍGIO
{linha}
{caso_original}

{linha}
II. RELATÓRIO DE INSTRUÇÃO (Agente de Instrução)
{linha}
{relatorio_instrucao}

{linha}
III. ALEGAÇÕES DA ACUSAÇÃO (Ministério Público)
{linha}
{tese_acusacao}

{linha}
IV. ALEGAÇÕES DA DEFESA (Patrono Garantista)
{linha}
{tese_defesa}

{linha}
V. NOTA DE INSTRUÇÃO PÓS-DEBATE (Agente de Instrução)
{linha}
{nota_pos_debate}

{linha}
VI. DELIBERAÇÃO — MAPA DE REALIDADES PARALELAS
{linha}
O Coletivo de Juízes deliberou e apresenta três leituras jurídicas do caso,
correspondentes a diferentes correntes doutrinárias e jurisprudenciais vigentes
no ordenamento jurídico português.

{sep}
SENTENÇA A — LEITURA RIGOROSA (Corrente Legalista)
{sep}
{sentencas.get('Rigorosa', 'Não disponível.')}

{traducoes.get('Rigorosa', '')}

{sep}
SENTENÇA B — LEITURA GARANTISTA (Corrente Constitucional)
{sep}
{sentencas.get('Garantista', 'Não disponível.')}

{traducoes.get('Garantista', '')}

{sep}
SENTENÇA C — LEITURA EQUILIBRADA (Corrente Pragmática)
{sep}
{sentencas.get('Equilibrada', 'Não disponível.')}

{traducoes.get('Equilibrada', '')}

{sep}
VII. ESTIMATIVA DE CUSTAS E PRAZOS
{sep}
"""
        for k, v in custas.items():
            ata += f"  • {k}: {v}\n"
        ata += f"""
{sep}
VIII. AVISO LEGAL
{sep}
Este documento foi gerado por um sistema de simulação jurídica com fins
exclusivamente educativos e informativos. NÃO substitui o aconselhamento
jurídico profissional prestado por um Advogado inscrito na Ordem dos Advogados
de Portugal. Para questões jurídicas reais, consulte sempre um profissional habilitado.

Assinado eletronicamente pelo Escrivão de Direito do Tribunal IA Portugal.
Processo n.º {self.numero_processo} — {self.data_pt}
{sep}
"""
        return ata

    def guardar_ata(self, ata: str, pasta: str = "output_atas/") -> str:
        os.makedirs(pasta, exist_ok=True)
        nome = f"ata_{self.numero_processo.replace('/', '_').replace(':', '')}.txt"
        caminho = os.path.join(pasta, nome)
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(ata)
        return caminho
