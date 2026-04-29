#!/bin/bash
# test.sh — Corre todos os testes

echo "🧪 A correr testes do Tribunal IA Portugal..."
echo ""

source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null

pytest tests/ -v --tb=short

echo ""
echo "✅ Testes concluídos"
