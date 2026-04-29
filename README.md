# 🏛️ Tribunal IA Portugal 🇵🇹

Simulador judicial de alta fidelidade baseado no **Direito Português vigente**, powered by **Claude (Anthropic)** via OpenRouter.

> ⚠️ **Aviso Legal**: Este projeto tem fins exclusivamente **educativos e de simulação**. Não substitui o aconselhamento jurídico profissional. Para questões reais, consulte um Advogado inscrito na Ordem dos Advogados de Portugal.

---

## 🆕 Melhorias da Fase 1 (Esta Versão)

| Funcionalidade | Descrição |
|---|---|
| 🔒 **Anonimização RGPD** | NER específico para português jurídico — mascar NIF, CC, NISS, telefones, emails, nomes, moradas antes de enviar para API |
| 🛡️ **Validação de Configuração** | Verificação de segurança da API key no arranque (não permite placeholders) |
| 📊 **Logging Estruturado** | JSON logs com tracing de agentes, custos API e auditoria completa |
| 🔄 **Retry + Circuit Breaker** | Backoff exponencial e circuit breaker para falhas de API |
| 🏷️ **Watermarking** | Hash criptográfico em cada ata para provar origem de simulação |
| ⚖️ **Disclaimer Obrigatório** | Aviso legal em todas as atas geradas |
| 🧪 **Testes Unitários** | Suite pytest para anonimização e configuração |

---

## ⚖️ Os Agentes

| Agente | Papel |
|---|---|
| 🔍 **Detetive** | Analisa factos, pede provas, calcula Termómetro de Evidência |
| 🐍 **Acusação** | Constrói tese de culpa com citação de artigos |
| 🛡️ **Defesa** | Garante contraditório, invoca *in dubio pro reo* |
| 🔨 **Juiz (3 perfis)** | Rigoroso, Garantista, Equilibrado |
| 📜 **Escrivão** | Redige ata oficial + tradução vulgar + custas |

---

## 🚀 Instalação

### 1. Requisitos

- Python 3.9+
- Chave GRATUITA do [OpenRouter](https://openrouter.ai/)

### 2. Clonar e instalar

```bash
git clone <repo>
cd tribunal_ia_fase1
pip install -r requirements.txt
```

### 3. Configurar

```bash
cp .env.example .env
# Edita .env e coloca a tua OPENROUTER_API_KEY
```

### 4. Correr

```bash
# Modo interativo
python main.py

# Processar ficheiro
python main.py --file caso.txt

# Processar texto inline
python main.py --text "O arguido João Silva..."

# Apenas anonimizar (teste RGPD)
python main.py --anonimizar-only --text "Texto com NIF 123456789..."
```

---

## 🧪 Testes

```bash
pytest tests/ -v
```

---

## 📁 Estrutura do Projeto

```
tribunal_ia_fase1/
├── main.py                     # Ponto de entrada
├── requirements.txt
├── .env.example
├── .gitignore
│
├── src/
│   ├── utils/
│   │   ├── config.py          # Validação de configuração
│   │   ├── logger.py          # Logging estruturado com tracing
│   │   ├── brain.py           # Interface LLM + retry + circuit breaker
│   │   └── anonymizer.py      # NER para português jurídico
│   ├── pipeline/
│   │   └── case_processor.py  # Orquestração do fluxo completo
│   └── agents/                # (reservado para Fase 2)
│
├── tests/
│   ├── test_anonymizer.py
│   └── test_config.py
│
├── data/
│   ├── leis/                  # Legislação (txt/pdf)
│   └── precedentes/           # Jurisprudência
│
└── output_atas/               # Atas geradas
```

---

## ⚙️ Configuração (.env)

| Variável | Descrição | Padrão |
|---|---|---|
| `OPENROUTER_API_KEY` | Chave da API | *(obrigatório)* |
| `MODELO` | Modelo Claude | `claude-sonnet-4-6` |
| `MAX_RETRIES` | Tentativas em caso de falha | `3` |
| `ANONIMIZAR_ENTIDADES` | Ativar anonimização RGPD | `true` |
| `WATERMARK_ATAS` | Adicionar watermark | `true` |
| `DISCLAIMER_OBRIGATORIO` | Aviso legal nas atas | `true` |
| `LOG_LEVEL` | Nível de log | `INFO` |
| `LOG_FORMAT` | Formato (json/text) | `json` |

---

## 🔗 Fontes de Legislação

- [DRE](https://dre.pt) — Diário da República Eletrónico
- [DGSI](http://www.dgsi.pt/) — Jurisprudência
- [Julgados de Paz](https://julgadosdepaz.mj.pt/)

---

## 🗺️ Roadmap

| Fase | Funcionalidade | Estado |
|---|---|---|
| **Fase 1** | Segurança, anonimização, logging, retry | ✅ Completo |
| **Fase 2** | RAG com vector store, validação de citações, jurisprudência | 🔄 Próximo |
| **Fase 3** | Interface Streamlit, visualização do processo | 📋 Planeado |
| **Fase 4** | API REST, testes de viés, conformidade LGPD | 📋 Planeado |

---

## 📄 Licença

MIT License — Uso educativo e de pesquisa.

**Nota**: O uso deste software para fins fraudulentos (falsificação de documentos judiciais) é estritamente proibido e punível por lei.
