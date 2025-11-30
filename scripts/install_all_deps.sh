#!/bin/bash
# Instala todas as dependências resolvendo conflitos
set -e

cd "$(dirname "$0")/.."
source .venv/bin/activate

echo "=========================================="
echo "Instalação Completa de Dependências"
echo "=========================================="
echo ""

# Instala dependências base primeiro
echo "1. Instalando dependências base..."
pip install -q --upgrade pip setuptools wheel
pip install -q \
    "pydantic>=2.7.0" \
    "pydantic-settings>=2.5.2" \
    "typer>=0.12.0" \
    "structlog>=24.1.0" \
    "sqlmodel>=0.0.16" \
    "aiosqlite>=0.20.0" \
    "numpy>=1.26.0" \
    "scikit-learn>=1.5.0" \
    "matplotlib>=3.8.0" \
    "pillow>=10.3.0" \
    "arxiv>=2.1.0" \
    "semanticscholar>=0.7.0" \
    "crossrefapi>=1.6.0" \
    "tiktoken>=0.7.0" \
    "tenacity>=9.0.0" \
    "pyyaml>=6.0.1" \
    "python-dotenv>=1.0.1" \
    "click==8.1.7"

echo "2. Instalando dependências do CrewAI..."
# Instala versões compatíveis
pip install -q "openai<2.0.0,>=1.13.3" || pip install -q "openai==1.54.5"
pip install -q "instructor==1.3.3" || true
pip install -q "langchain>=0.2.0,<0.3.0" || pip install -q "langchain==0.2.16"

echo "3. Instalando CrewAI..."
pip install -q --no-deps "crewai==0.51.0" || pip install -q "crewai==0.51.0"

# Instala dependências do CrewAI manualmente se necessário
pip install -q "langchain-openai>=0.1.0" || true
pip install -q "langchain-community>=0.2.0" || true

echo "4. Verificando instalação..."
python <<PY
try:
    import crewai
    print(f"✅ CrewAI {crewai.__version__} instalado")
except ImportError as e:
    print(f"❌ CrewAI não instalado: {e}")
    exit(1)

try:
    from src.config.settings import Settings
    print("✅ Settings importado")
except ImportError as e:
    print(f"❌ Settings não importado: {e}")
    exit(1)
PY

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ Instalação concluída com sucesso!"
    echo "=========================================="
else
    echo ""
    echo "=========================================="
    echo "⚠️  Instalação com problemas"
    echo "=========================================="
    exit 1
fi

