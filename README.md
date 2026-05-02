# ⚖️ Tribunal IA Portugal

> Simulador judicial de alta fidelidade para o Direito Português — com RAG integrado, cache semântico e paralelismo.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/interface-Streamlit-ff4b4b.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 📌 O que é?

O **Tribunal IA Portugal** é um simulador jurídico open-source que replica o funcionamento de um tribunal português. A partir da descrição de um caso (em linguagem comum), o sistema:

1. **Anonimiza** dados pessoais (RGPD)
2. **Identifica** a instância judicial correta
3. **Recupera** contexto jurídico relevante (RAG)
4. **Conduz** uma fase de instrução interativa
5. **Simula** os papéis de Detetive, Acusação, Defesa e 3 Juízes
6. **Gera** uma ata completa com 3 sentenças distintas (Rigoroso, Garantista, Equilibrado)

> ⚠️ **Aviso:** Ferramenta exclusivamente educativa. Não constitui parecer jurídico nem decisão judicial. Para situações reais, consulte um Advogado inscrito na [Ordem dos Advogados](https://www.oa.pt).

---

## ✨ Funcionalidades Principais

| Funcionalidade | Descrição |
|----------------|-----------|
| 🔍 **RAG Integrado** | Motor de recuperação jurídica com BM25 melhorado, persistência em disco e contexto injetado nos prompts dos agentes |
| 💾 **Cache Semântico** | Evita chamadas repetidas ao LLM, reduzindo custos em até 80% |
| ⚡ **Paralelismo** | As 3 sentenças são geradas em paralelo (async), reduzindo tempo de espera |
| 💰 **Modo Económico** | Usa menos agentes e modelos mais baratos, ideal para testes |
| 🏛️ **7 Instâncias** | Suporta Tribunal de Instrução Criminal, Cível, Trabalho, Administrativo, Família, Comercial e Europeu |
| 🔐 **Anonimização RGPD** | Deteta e substitui nomes, moradas, emails, telefones, NIFs, processos e tribunais |
| 📝 **Fase de Instrução** | Perguntas interativas geradas por IA para completar lacunas factuais |
| 📄 **Ata Completa** | Documento estruturado com watermark, hash e disclaimer legal |
| 🌐 **Interface Web** | Streamlit com tabs, componentes reutilizáveis e estatísticas de custo |
| 🧪 **Testes** | Suite de testes para anonimizador, cache e RAG |

---

## 🚀 Instalação Rápida

### 1. Clonar o repositório

```bash
git clone https://github.com/F-i-Red/Tribunal_IA_Portugal-V2.git
cd Tribunal_IA_Portugal-V2
```

### 2. Criar ambiente virtual

```bash
python -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar chave API

```bash
cp .env.example .env
```

Edita o ficheiro `.env` e coloca a tua chave da [OpenRouter](https://openrouter.ai/keys):

```bash
OPENROUTER_API_KEY="sk-or-v1-xxxxxxxxxxxxxxxx"
```

> 💡 A OpenRouter oferece créditos gratuitos para testes. Não precisas de cartão de crédito para começar.

### 5. Verificar instalação

```bash
python verificar.py
```

---

## 🖥️ Como Usar

### Interface Web (recomendado)

```bash
# Linux / macOS
./iniciar_interface.sh

# Windows
iniciar_interface.bat
```

Acede a `http://localhost:8501` no teu navegador.

### Linha de Comandos (CLI)

```bash
# Modo normal (com instrução interativa)
python main.py

# Modo rápido (sem instrução, sem disclaimer)
python main.py --sem-disclaimer --sem-instrucao

# Modo económico (mais barato)
python main.py --modo-economico

# Tribunal específico
python main.py --instancia TIC
```

### Gestão da Base de Conhecimento

```bash
# Listar fontes indexadas
python gerir_base.py --listar

# Pesquisar na base jurídica
python gerir_base.py --pesquisar "homicídio culposo" -n 5

# Forçar reindexação
python gerir_base.py --recarregar
```

---

## 🏗️ Arquitetura

```
Tribunal_IA_Portugal-V2/
├── src/
│   ├── agents/           # Placeholder para futuros agentes especializados
│   ├── cache/            # Sistema de cache semântico (novo)
│   │   └── __init__.py   # SemanticCache com persistência em disco
│   ├── pipeline/
│   │   ├── case_processor.py   # Pipeline principal (RAG + paralelismo)
│   │   └── instancias.py       # Definição das 7 instâncias judiciais
│   ├── rag/
│   │   ├── motor.py      # Motor RAG com BM25 melhorado e persistência
│   │   └── validador.py  # Validação de citações jurídicas
│   ├── ui/               # Placeholder para componentes UI futuros
│   └── utils/
│       ├── anonymizer.py # Anonimização RGPD (regex + contexto)
│       ├── brain.py      # Interface com OpenRouter + circuit breaker + cache
│       ├── config.py     # Configuração centralizada (Pydantic-style)
│       └── logger.py     # Logger estruturado em JSON + tracking de custos
├── tests/
│   ├── test_anonymizer.py
│   ├── test_cache.py     # (novo)
│   └── test_rag.py       # (novo)
├── data/
│   ├── leis/             # Textos de lei (Constituição, etc.)
│   ├── precedentes/      # Precedentes judiciais (adicionar aqui)
│   └── jurisprudencia/   # Jurisprudência do STJ (adicionar aqui)
├── output_atas/          # Atas geradas automaticamente
├── logs/                 # Logs estruturados em JSON
├── app.py                # Interface Streamlit refatorada
├── main.py               # CLI principal
├── verificar.py          # Verificador de sistema
├── gerir_base.py         # Gestor da base de conhecimento
├── requirements.txt
├── .env.example
└── README.md
```

---

## ⚙️ Configuração Avançada

Edita o ficheiro `.env` para personalizar o comportamento:

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `OPENROUTER_API_KEY` | — | **Obrigatória.** Chave da API OpenRouter |
| `MODELO` | `anthropic/claude-haiku-4-5` | Modelo LLM a usar |
| `MAX_RETRIES` | `3` | Tentativas em caso de falha |
| `REQUEST_TIMEOUT` | `120` | Timeout em segundos |
| `CACHE_ENABLED` | `true` | Ativar cache semântico |
| `PARALELISMO` | `true` | Sentenças em paralelo |
| `MODO_ECONOMICO` | `false` | Reduz agentes e custos |
| `ANONIMIZAR_ENTIDADES` | `true` | Ativar anonimização RGPD |
| `GUARDAR_ATAS` | `true` | Guardar atas em disco |

### Modelos Recomendados

| Modelo | Custo | Qualidade | Uso Ideal |
|--------|-------|-----------|-----------|
| `google/gemini-2.0-flash-001` | ⭐ Muito baixo | Boa | Testes, modo económico |
| `anthropic/claude-haiku-4-5` | ⭐ Baixo | Muito boa | Padrão, equilibrado |
| `google/gemini-2.5-pro` | ⭐⭐ Médio | Excelente | Produção |
| `anthropic/claude-sonnet-4.6` | ⭐⭐⭐ Médio-Alto | Excelente | Casos complexos |
| `anthropic/claude-opus-4.6` | ⭐⭐⭐⭐ Alto | Superior | Máxima qualidade |

---

## 🧪 Testes

```bash
# Executar todos os testes
pytest tests/ -v

# Testes específicos
pytest tests/test_anonymizer.py -v
pytest tests/test_cache.py -v
pytest tests/test_rag.py -v
```

---

## 📊 Estatísticas de Custo

O sistema regista automaticamente:

- Número de chamadas API por caso
- Tokens de input/output
- Custo estimado em USD e EUR
- Poupança do cache

Podes consultar as estatísticas na interface web (sidebar) ou nos logs em `logs/tribunal.log`.

---

## 🔒 Segurança e Privacidade

- ✅ **Anonimização automática** de dados pessoais antes de enviar para o LLM
- ✅ **Chave API** nunca exposta no código (usa `.env`)
- ✅ **.gitignore** configurado para não commitar `.env`, logs nem outputs
- ✅ **Watermark e hash** em todas as atas para rastreabilidade
- ✅ **Disclaimer legal** obrigatório em todos os documentos gerados

---

## 🤝 Como Contribuir

1. Faz fork do repositório
2. Cria uma branch: `git checkout -b minha-feature`
3. Faz commit das alterações: `git commit -am 'Adiciona nova feature'`
4. Faz push: `git push origin minha-feature`
5. Abre um Pull Request

### Ideias para contribuições

- [ ] Adicionar mais textos de lei à pasta `data/leis/`
- [ ] Adicionar jurisprudência do STJ à pasta `data/jurisprudencia/`
- [ ] Suporte a upload de documentos PDF
- [ ] Exportação de atas para PDF (WeasyPrint)
- [ ] Modo contraditório interativo
- [ ] Dockerização
- [ ] Avaliação automática da consistência entre sentenças

---

## 📜 Licença

MIT License — consulta o ficheiro `LICENSE` para detalhes.

---

## 🙏 Agradecimentos

- [OpenRouter](https://openrouter.ai/) — API unificada de LLMs
- [Streamlit](https://streamlit.io/) — Framework web
- Comunidade open-source portuguesa

---

<div align="center">

**🇵🇹 Feito em Portugal para o Direito Português**

*[www.oa.pt](https://www.oa.pt) — Ordem dos Advogados de Portugal*

</div>
