# Documento de Arquitetura — Tribunal IA Portugal

## Visão Geral

O Tribunal IA Portugal é um sistema de simulação judicial multi-agente que processa casos jurídicos sob o Direito Português. A arquitetura segue princípios de **segurança por design**, **conformidade RGPD** e **observabilidade completa**.

---

## Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────────────┐
│                           UTILIZADOR                                │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         main.py (CLI)                               │
│  • Validação de configuração                                        │
│  • Modo interativo / batch / anonimização-only                      │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    CaseProcessor (Pipeline)                         │
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐ │
│  │Anonimizador │→ │  Detetive   │→ │  Advogados  │→ │  Juízes   │ │
│  │   (RGPD)    │  │  (RAG)      │  │(Acusação/  │  │(3 perfis) │ │
│  │             │  │             │  │  Defesa)    │  │           │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────┬─────┘ │
│                                                           │       │
│                              ┌────────────────────────────┘       │
│                              ▼                                    │
│                    ┌─────────────────┐                            │
│                    │    Escrivão     │                            │
│                    │  (Ata + Vulgar) │                            │
│                    └────────┬────────┘                            │
│                             │                                     │
│                    ┌────────▼────────┐                            │
│                    │  Watermarking   │                            │
│                    │   + Disclaimer  │                            │
│                    └─────────────────┘                            │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Infraestrutura                              │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   Config     │  │   Logger     │  │    Brain     │              │
│  │  (validação) │  │  (tracing)   │  │(LLM + retry) │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              OpenRouter → Claude (Anthropic)                │   │
│  │         Retry: 3 tentativas | Backoff: exponencial          │   │
│  │              Circuit Breaker: 5 falhas / 60s                │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Fluxo de Dados

### 1. Entrada
- Utilizador fornece descrição do caso (texto livre)
- Pode conter: nomes, NIF, moradas, contactos, datas

### 2. Anonimização (RGPD)
```
Texto Original → PortugueseLegalAnonymizer → Texto Anonimizado + Entidades
```
- Regex para entidades estruturadas (NIF, CC, telefone, email)
- Heurísticas contextuais para nomes de pessoas (prefixos: "arguido", "testemunha", etc.)
- Deteção de tribunais e moradas
- Pseudónimos determinísticos (mesmo texto → mesmo pseudónimo)

### 3. Processamento Multi-Agente
Cada agente recebe o texto anonimizado + outputs dos agentes anteriores:

```
Detetive → Relatório de Instrução
    ↓
Acusação → Alegações (com citação de artigos)
    ↓
Defesa → Alegações (contraditório)
    ↓
Juízes (3x) → Sentenças paralelas (rigoroso, garantista, equilibrado)
    ↓
Escrivão → Ata oficial + tradução vulgar
```

### 4. Output Seguro
- Watermark criptográfico (SHA-256) para provar origem
- Disclaimer legal obrigatório
- Hash de verificação do documento
- Guardado em `output_atas/`

---

## Segurança

### Validação de Configuração
- API key obrigatória e validada no arranque
- Rejeita placeholders ("sua_chave_aqui", "xxxx")
- Verifica formato mínimo da chave OpenRouter

### Logging
- Formato JSON para integração com SIEM
- Tracing de agentes (trace_id, case_id, agent_name)
- Log de custos API (tokens, duração, custo estimado USD)
- Log de anonimização (entidades encontradas, tipos)

### Resiliência
- **Retry**: 3 tentativas com backoff exponencial (2s, 4s, 8s)
- **Circuit Breaker**: Abre após 5 falhas, fecha após 60s
- **Timeout**: 60s por chamada API

---

## Conformidade RGPD

| Requisito | Implementação |
|---|---|
| Minimização de dados | Anonimização antes de envio para API de terceiros |
| Pseudonimização | Entidades substituídas por tokens determinísticos |
| Registo de operações | Log de anonimização com tipos de entidades |
| Integridade | Hash de verificação em cada documento |
| Transparência | Disclaimer legal em todas as atas |

---

## Próximas Fases

### Fase 2 — RAG e Validação
- Vector store (ChromaDB) para jurisprudência
- Embeddings multilingues (sentence-transformers)
- Validação de citações de artigos contra base local
- Diferenciação de instâncias (1ª, Relação, STJ)

### Fase 3 — Interface
- Streamlit com visualização do grafo de agentes
- Histórico de casos processados
- Modo educacional vs. profissional

### Fase 4 — Produção
- API REST (FastAPI) com documentação OpenAPI
- Testes de viés (demografia, geografia)
- Conformidade LGPD completa
- Docker + CI/CD
