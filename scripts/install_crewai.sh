#!/bin/bash
# Instalação específica do CrewAI resolvendo conflitos
set -e

cd "$(dirname "$0")/.."
source .venv/bin/activate

echo "Instalando CrewAI com resolução de conflitos..."

# Estratégia: instalar langchain compatível primeiro
echo "1. Instalando langchain compatível..."
pip install -q "langchain>=0.2.0,<0.3.0" || {
    echo "   Tentando versão alternativa..."
    pip install -q "langchain==0.2.16" || true
}

# Instala crewai
echo "2. Instalando CrewAI..."
pip install -q "crewai==0.51.0" || {
    echo "   Tentando versão mais recente..."
    pip install -q "crewai>=0.50.0" || {
        echo "   ⚠️  Falha na instalação do CrewAI"
        exit 1
    }
}

# Verifica instalação
echo "3. Verificando..."
python -c "import crewai; print(f'✅ CrewAI {crewai.__version__} instalado')" && {
    echo ""
    echo "✅ Instalação concluída com sucesso!"
    exit 0
} || {
    echo "❌ CrewAI não pôde ser importado"
    exit 1
}

