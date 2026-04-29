#!/bin/bash
# setup.sh — Script de instalação do Tribunal IA Portugal

set -e

echo "🏛️  Tribunal IA Portugal — Instalação"
echo "======================================"

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Instala primeiro."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Python $PYTHON_VERSION encontrado"

# Criar ambiente virtual
if [ ! -d "venv" ]; then
    echo "📦 A criar ambiente virtual..."
    python3 -m venv venv
fi

# Ativar ambiente virtual
echo "🔄 A ativar ambiente virtual..."
source venv/bin/activate || source venv/Scripts/activate

# Instalar dependências
echo "📥 A instalar dependências..."
pip install --upgrade pip
pip install -r requirements.txt

# Configurar .env
if [ ! -f ".env" ]; then
    echo "⚙️  A criar ficheiro .env..."
    cp .env.example .env
    echo ""
    echo "📝 IMPORTANTE: Edita o ficheiro .env e coloca a tua OPENROUTER_API_KEY"
    echo "   Obtém uma chave gratuita em: https://openrouter.ai/"
    echo ""
fi

# Criar diretórios necessários
mkdir -p data/leis data/precedentes output_atas data/chroma_db

# Verificar instalação
echo ""
echo "🔍 A verificar instalação..."
python3 -c "from src.utils import get_config; print('✅ Módulos importados com sucesso')" 2>/dev/null || {
    echo "⚠️  Aviso: Verifica se estás na pasta correta do projeto"
}

echo ""
echo "======================================"
echo "✅ Instalação completa!"
echo ""
echo "Próximos passos:"
echo "  1. Edita .env com a tua OPENROUTER_API_KEY"
echo "  2. Corre: python main.py"
echo ""
echo "Para testar a anonimização:"
echo "  python main.py --anonimizar-only --text "O arguido João Silva (NIF 123456789)...""
echo ""
