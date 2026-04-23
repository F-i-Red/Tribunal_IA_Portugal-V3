# 🏛️ Tribunal IA Portugal 🇵🇹

O **Tribunal IA Portugal** é um simulador judicial de alta fidelidade que utiliza inteligência artificial multi-agente para processar casos jurídicos sob a égide do Direito Português. 

Ao contrário de bots convencionais, este sistema replica a **metodologia jurídica e o contraditório**, oferecendo uma análise profunda que vai desde a investigação factual até à previsão de realidades paralelas de sentenciamento.

## ⚖️ Os Agentes de Excelência

O sistema opera através de um coletivo de agentes especializados:

1.  **🔍 O Detetive (Instrução):** Analista cético de factos. Identifica lacunas, pede provas (SMS, fotos, testemunhas) e calcula o **Termómetro de Evidência**.
2.  **🐍 Advogado do Diabo (Acusação):** Focado na tipicidade, dolo e punibilidade. Utiliza o Código Penal e Civil para construir a tese de culpa.
3.  **🛡️ O Defensor (Garantismo):** Protege os direitos fundamentais baseados na CRP. Procura atenuantes, nulidades e a dúvida razoável.
4.  **🔨 Coletivo de Juízes:** Gera múltiplas **Realidades Paralelas** de sentenciamento, pesando diferentes correntes doutrinárias e jurisprudenciais.
5.  **📜 O Escrivão:** Redige a Ata Oficial, calcula as **Custas Judiciais** e traduz o veredito para **Linguagem Vulgar** (Justiça de Proximidade).

## 🔄 Fluxo de Trabalho (Loop Dinâmico)

O Tribunal não decide sem prova. O sistema utiliza um **Loop de Instrução Recurrente**:
1. O utilizador apresenta o caso.
2. O **Detetive** interroga.
3. O utilizador responde.
4. O **Debate Instrutório** entre Acusação e Defesa é atualizado em tempo real.
5. O ciclo repete-se até à maturidade do processo.

## 🔮 Funcionalidades Exclusivas

* **Mapa de Realidades Paralelas:** Visualização de diferentes desfechos consoante o perfil do juiz (Rigoroso, Garantista ou Equilibrado).
* **Termómetro de Evidência:** Classificação da solidez do caso (🔴 Frágil, 🟡 Moderada, 🟢 Sólida).
* **Justiça para Crianças:** Tradução instantânea de jargão jurídico para linguagem corrente.
* **Estimativa de Custas:** Cálculo aproximado de taxas de justiça e honorários.

## 🔗 Fontes Oficiais de Dados (Dataset Legislativo)
Deves adicionar ao teu ficheiro para garantir que o juiz saiba onde buscar a "Verdade Jurídica":

Para garantir o rigor técnico e a conformidade com o Ordenamento Jurídico Português, o Tribunal IA Portugal utiliza as seguintes fontes de dados oficiais:

### 1. Legislação Consolidada (DRE - Diário da República Eletrónico)
Constituição da República Portuguesa: https://dre.pt/dre/legislacao-consolidada/decreto-aprovacao-constituicao-1976-115598

Código Civil: https://dre.pt/dre/legislacao-consolidada/decreto-lei/1966-34509075

Código Penal: https://dre.pt/dre/legislacao-consolidada/decreto-lei/1982-34522695

Código de Processo Penal: https://dre.pt/dre/legislacao-consolidada/decreto-lei/1987-34551175

Código de Processo Civil: https://dre.pt/dre/legislacao-consolidada/lei/2013-34580575

Código do Trabalho: https://dre.pt/dre/legislacao-consolidada/lei/2009-34546475

### 2. Jurisprudência e Precedentes (DGSI - Bases Jurídicas)
Portal Geral de Pesquisa (Acórdãos dos Tribunais Superiores): http://www.dgsi.pt/

Supremo Tribunal de Justiça (STJ): http://www.dgsi.pt/jstj.nsf

Tribunal da Relação de Lisboa (TRL): http://www.dgsi.pt/jtrl.nsf

Tribunal da Relação do Porto (TRP): http://www.dgsi.pt/jtrp.nsf

### 3. Custas e Mediação
Regulamento das Custas Processuais (RCP): https://dre.pt/dre/legislacao-consolidada/decreto-lei/2008-34413675

Portal dos Julgados de Paz (Resolução Alternativa de Litígios): https://julgadosdepaz.mj.pt/

## 💡 Nota de Implementação
Este protótipo conceptual foi desenhado para que os agentes (Detetive, Advogados e Juízes) utilizem estes links como base de consulta prioritária, garantindo que a análise factual e as sentenças simuladas refletem a letra da lei vigente em Portugal.

---

## Tribunal-IA-Portugal/
```bash
├── main.py              <-- O Maestro (Gere o loop e a lógica de estado)
├── agentes/
│   ├── detetive.py      <-- Cérebro factual e termómetro de evidência
│   ├── acusacao.py      <-- Advogado do Diabo (Rigor da Lei)
│   ├── defesa.py        <-- Guardião das Garantias (CRP)
│   ├── juiz.py          <-- O Coletivo (Gera as 3 Realidades Paralelas)
│   └── escrivao.py      <-- Redator e custos
├── data/
│   ├── leis/          <-- Coloca aqui os .txt ou .pdf do DRE (Código Penal, Civil, etc.)
│   ├── jurisprudencia/ <-- Coloca aqui os resumos de acórdãos do DGSI
│   ├── contexto_utilizador/ <-- (Opcional) Teu repositório de documentos pessoais
│   └── links_fonte.md   <-- A lista de links no README.md
├── templates/
│   └── ata_final.md
└── README.md
```
---
## 🛠️ O que precisas de fazer agora para testar:
Faz download do repositório para o teu computador.

Fazer download dos PDFs ou .txt das leis dos links: Põe dentro da pasta data/leis em .txt (ex: crp.txt) ou um .pdf.

Instalar dependências:

No terminal, corre:
```bash
pip install -r requirements.txt
```
Correr o Maestro:
```
python main.py
```
---

## ⚠️ Aviso Legal
Este projeto tem fins educativos e de simulação. Não substitui o aconselhamento jurídico profissional por um advogado inscrito na Ordem dos Advogados.
