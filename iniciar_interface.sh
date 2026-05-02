#!/bin/bash
# Tribunal IA Portugal — Iniciar Interface Web

echo "🏛️  Tribunal IA Portugal — Iniciando interface web..."
echo ""

# Verificar ambiente
if [ ! -d ".venv" ]; then
    echo "❌ Ambiente virtual não encontrado. Executa primeiro:"
    echo "   python -m venv .venv"
    echo "   source .venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

source .venv/bin/activate

# Verificar .env
if [ ! -f ".env" ]; then
    echo "⚠️  .env não encontrado. Copia .env.example para .env e configura a tua chave."
    exit 1
fi

echo "✅ Ambiente ativado"
echo "🚀 A iniciar Streamlit..."

streamlit run app.py