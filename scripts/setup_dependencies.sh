#!/bin/bash
# Script para instalar dependências usando uv
set -e

cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)

echo "=========================================="
echo "Instalação de Dependências com UV"
echo "=========================================="
echo ""

# Verifica se uv está instalado
if ! command -v ~/.local/bin/uv &> /dev/null; then
    echo "Instalando uv..."
    curl -fsSL https://astral.sh/uv/install.sh | sh
fi

UV_BIN=~/.local/bin/uv

# Ativa venv ou cria novo
if [ ! -d ".venv" ]; then
    echo "Criando venv..."
    $UV_BIN venv -p python3.11
fi

source .venv/bin/activate

echo "Sincronizando dependências com uv..."
echo ""

# Usa uv para sincronizar baseado no pyproject.toml
# Primeiro, instala dependências principais sem conflitos conhecidos
echo "1. Instalando dependências base..."
$UV_BIN pip install -q \
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
    "wandb>=0.17.0" \
    "click==8.1.7" || true

echo "2. Instalando CrewAI (pode ter conflitos de langchain)..."
# Tenta instalar crewai sem crewai-tools primeiro
$UV_BIN pip install -q "crewai>=0.50.0" || {
    echo "   Tentando versão específica..."
    $UV_BIN pip install -q "crewai==0.51.0" || {
        echo "   ⚠️  CrewAI pode ter conflitos. Continuando..."
    }
}

echo "3. Verificando instalação..."
python -c "import crewai; print(f'   ✅ CrewAI {crewai.__version__} instalado')" 2>/dev/null || {
    echo "   ⚠️  CrewAI não instalado. Sistema usará stubs."
}

echo ""
echo "=========================================="
echo "✅ Instalação concluída!"
echo "=========================================="
echo ""
echo "Para ativar o ambiente:"
echo "  source .venv/bin/activate"
echo ""

