# agentes/escrivao.py
# O Oficial de Justiça: Tradutor, Contabilista de Custas e Redator de Atas

class EscrivaoDireito:
    def __init__(self):
        self.nome = "Escrivão de Direito"
        # Glossário básico para tradução automática
        self.glossario = {
            "Absolvição": "Livre de culpa (pode ir para casa)",
            "Condenação": "Foi considerado culpado e terá um castigo",
            "Ilicitude": "Fazer algo que é contra a lei",
            "Dolo": "Fazer de propósito, com intenção",
            "In Dubio Pro Reo": "Na dúvida, o juiz decide a favor do réu",
            "Pena Suspensa": "Não vai para a prisão, mas tem de se portar bem",
            "Indemnização": "Dinheiro pago para compensar o estrago feito"
        }

    def calcular_custas_estimadas(self, tipo_processo="Penal"):
        """Estima as taxas de justiça com base no Regulamento das Custas Processuais."""
        # Valores simplificados para o protótipo conceptual
        estimativa = {
            "Taxas de Justiça (DRE)": "204.00 € a 612.00 €",
            "Honorários Médios (Estimativa)": "750.00 € a 2,500.00 €",
            "Tempo de Espera Médio": "12 a 24 meses"
        }
        return estimativa

    def traduzir_para_cidadao(self, sentencas_tecnicas):
        """Traduz as 3 Realidades Paralelas para uma linguagem de proximidade."""
        traducoes = {}
        for nome, texto in sentencas_tecnicas.items():
            if "Condenação Máxima" in texto:
                traducoes[nome] = "O tribunal foi muito rigoroso. Acha que o que fizeste é grave e vais ter o castigo mais alto que a lei permite."
            elif "Absolvição" in texto:
                traducoes[nome] = "Estás livre. Como não há provas suficientes, o juiz prefere não castigar ninguém para não cometer um erro."
            elif "Solução de Compromisso" in texto:
                traducoes[nome] = "Ficou no meio-termo. Vais ter um castigo, mas o juiz dá-te uma oportunidade de não ires para a prisão se cumprires as regras."
            else:
                traducoes[nome] = "Decisão equilibrada: pagas o que estragaste e o caso encerra."
        
        return traducoes

    def redigir_ata_final(self, caso, realidades, traducoes, custas):
        """Gera o documento final 'bonito' e estruturado para o utilizador."""
        ata = f"""
🏛️ TRIBUNAL IA PORTUGAL - ATA DE AUDIÊNCIA
------------------------------------------
PROCESSO: 2026/001-AUTO
OBJETO: {caso[:50]}...

[VERDITO: O MAPA DAS REALIDADES PARALELAS]
1. SENTENÇA RIGOROSA: {realidades['Rigorosa']}
   👉 O que significa: {traducoes['Rigorosa']}

2. SENTENÇA GARANTISTA: {realidades['Garantista']}
   👉 O que significa: {traducoes['Garantista']}

3. SENTENÇA EQUILIBRADA: {realidades['Equilibrada']}
   👉 O que significa: {traducoes['Equilibrada']}

[ESTIMATIVA DE CUSTOS E TEMPO]
- Taxas de Justiça: {custas['Taxas de Justiça (DRE)']}
- Estimativa de Honorários: {custas['Honorários Médios (Estimativa)']}
- Expectativa de Resolução: {custas['Tempo de Espera Médio']}

------------------------------------------
Assinado eletronicamente pelo Escrivão de Direito.
"""
        return ata
