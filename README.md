# 🏛️ Tribunal IA Portugal 🇵🇹

Simulador judicial de alta fidelidade baseado no **Direito Português vigente**, powered by **Claude (Anthropic)**.

O sistema replica a metodologia jurídica real: instrução factual → debate contraditório → deliberação coletiva → sentença → tradução para linguagem vulgar.

---

## ⚖️ Os Agentes

| Agente | Papel |
|--------|-------|
| 🔍 **Detetive (Instrução)** | Analisa factos, pede provas, calcula o Termómetro de Evidência (🔴🟡🟢) |
| 🐍 **Advogado do Diabo (Acusação)** | Constrói a tese de culpa com citação de artigos dos Códigos |
| 🛡️ **Patrono da Defesa** | Garante o contraditório, invoca *in dubio pro reo* e direitos fundamentais |
| 🔨 **Coletivo de Juízes** | Profere 3 sentenças paralelas (Rigorosa, Garantista, Equilibrada) |
| 📜 **Escrivão** | Redige a Ata oficial + traduz para linguagem vulgar + estima custas |

---

## 🔄 Fluxo de Trabalho

```
Utilizador descreve o caso
       ↓
🔍 Detetive interroga (até 5 rondas)
       ↓
📋 Relatório de Instrução
       ↓
🐍 Alegações da Acusação
       ↓
🛡️ Alegações da Defesa
       ↓
🔨 3 Sentenças Paralelas
       ↓
📖 Tradução para linguagem vulgar (cada sentença)
       ↓
📜 Ata Final completa (guardada em output_atas/)
```

---

## Podes correr apenas o interface.html
(faz doanload do ficheiro: https://github.com/F-i-Red/Tribunal_IA_Portugal/blob/main/interface.html)
### 1. Requisitos
- Chave GRATUITA do OpenRouter (https://openrouter.ai/)

ou

## 🚀 Instalação e Uso

### 1. Requisitos
- Python 3.9+
- Chave GRATUITA do OpenRouter (https://openrouter.ai/)

### 2. Instalar dependências
```bash
pip install -r requirements.txt
```

### 3. Configurar a chave de API
```bash
cp .env.example .env
# Edita o ficheiro .env e coloca a tua OPENROUTER_API_KEY
```

### 4. (Opcional) Adicionar legislação
Coloca ficheiros `.txt` ou `.pdf` das leis em `data/leis/`.  
Ver instruções em `data/leis/INSTRUCOES.txt`.

### 5. Correr
```bash
python main.py
```

---

## 📁 Estrutura do Repositório

```
Tribunal_IA_Portugal/
├── main.py                     ← O Maestro (orquestra tudo)
├── requirements.txt
├── .env.example                ← Copia para .env e preenche a chave
├── .gitignore
│
├── agentes/
│   ├── detetive.py             ← Instrução factual e termómetro de evidência
│   ├── advogados.py            ← Acusação e Defesa
│   ├── juiz.py                 ← Coletivo de Juízes (3 perfis)
│   └── escrivao.py             ← Ata, tradução, custas
│
├── utils/
│   ├── brain.py                ← Interface central com a API Claude
│   └── loader.py               ← Carrega .txt e .pdf de data/leis/
│
├── data/
│   └── leis/                   ← Coloca aqui os ficheiros de lei
│       └── INSTRUCOES.txt
│
└── output_atas/                ← Atas geradas automaticamente
```

---

## ⚙️ Configuração (.env)

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `OPENROUTER_API_KEY` | Chave da API Anthropic | *(obrigatório)* |
| `MODELO` | Modelo Claude a usar | `claude-sonnet-4-6` |
| `PASTA_LEIS` | Pasta com ficheiros de lei | `data/leis/` |
| `GUARDAR_ATAS` | Guardar atas em ficheiro | `true` |
| `PASTA_ATAS` | Pasta de destino das atas | `output_atas/` |

**Modelos disponíveis:**
- `claude-sonnet-4-6` — Recomendado (equilíbrio qualidade/velocidade)
- `claude-opus-4-6` — Máxima qualidade (mais lento e caro)
- `claude-haiku-4-5-20251001` — Mais rápido e económico

---

## ⚠️ Aviso Legal

Este projeto tem fins exclusivamente **educativos e de simulação**. Não substitui o aconselhamento jurídico profissional prestado por um Advogado inscrito na **Ordem dos Advogados de Portugal**.

Para questões jurídicas reais, consulte sempre um profissional habilitado.

---

## 🔗 Fontes de Legislação

- **DRE** (Diário da República Eletrónico): https://dre.pt
- **DGSI** (Jurisprudência): http://www.dgsi.pt/
- **Julgados de Paz**: https://julgadosdepaz.mj.pt/
