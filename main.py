# main.py
import os
import dotenv
dotenv.load_dotenv()

from utils.loader import carregar_documentos
from utils.brain import get_llm
from agentes.detetive import DetetiveJudicial
from agentes.advogados import Acusacao, Defesa
from agentes.juiz import ColetivoJuizes
from agentes.escrivao import EscrivaoDireito

class TribunalMaestro:
    def __init__(self):
        print("📂 [SISTEMA] A carregar base de dados jurídica...")
        self.documentos = carregar_documentos("data/leis/")
        self.contexto_legal = "\n".join([doc.page_content[:800] for doc in self.documentos[:15]])  # resumo para prompts
        print(f"✅ [RAG] {len(self.documentos)} fragmentos carregados.")

        self.detetive = DetetiveJudicial()
        self.acusacao = Acusacao()
        self.defesa = Defesa()
        self.juiz = ColetivoJuizes()
        self.escrivao = EscrivaoDireito()

        self.caso_completo = ""

    def iniciar_sessao(self):
        print("\n🏛️ TRIBUNAL IA PORTUGAL - Versão Melhorada (com OpenRouter + RAG)")
        caso = input("⚖️ Descreva o caso: ")
        self.caso_completo = caso
        self.correr_fluxo()

    def correr_fluxo(self):
        # Loop do Detetive
        while True:
            lacunas = self.detetive.analisar_caso(self.caso_completo)
            print(f"🌡️ STATUS: {self.detetive.termometro_evidencia}")
            if lacunas:
                for i, p in enumerate(lacunas, 1):
                    print(f"   {i}. {p}")
                resp = input("\n📝 Resposta (ou 'JULGAR'): ")
                if resp.upper() == "JULGAR":
                    break
                self.caso_completo += f" [Adicional: {resp}]"
            else:
                break

        # Debate
        relatorio = self.detetive.relatorio_para_o_juiz()
        tese_acusacao = self.acusacao.construir_tese(relatorio, self.contexto_legal)
        tese_defesa = self.defesa.construir_tese(relatorio, self.contexto_legal)

        print("\n🐍 Acusação:\n", tese_acusacao)
        print("\n🛡️ Defesa:\n", tese_defesa)

        # Deliberação
        # 1. Corrige o nome do objeto de 'self.juizes' para 'self.juiz'
        deliberacao_bruta = self.juiz.deliberar(
            analise_detetive=relatorio, 
            tese_acusacao=tese_acusacao, 
            tese_defesa=tese_defesa, 
            contexto_legal=self.contexto_legal
        )
        
        # 2. Extrai o texto da deliberação
        texto_deliberacao = deliberacao_bruta.get('realidades', '')

        # 3. Prepara o dicionário de realidades que o escrivão espera
        #    (Aqui podes melhorar o parsing, mas para já isto resolve o KeyError)
        realidades_para_ata = {
            "Rigorosa": texto_deliberacao,
            "Garantista": texto_deliberacao,
            "Equilibrada": texto_deliberacao
        }

        # Ata Final
        # 4. Usa as 'realidades_para_ata' para traduzir e redigir a ata
        traducoes = self.escrivao.traduzir_para_cidadao(realidades_para_ata)
        custas = self.escrivao.calcular_custas_estimadas()
        
        print(self.escrivao.redigir_ata_final(
            self.caso_completo, 
            realidades_para_ata,  # <-- Passa o dicionário, não a string
            traducoes, 
            custas
        ))

if __name__ == "__main__":
    tribunal = TribunalMaestro()
    tribunal.iniciar_sessao()
