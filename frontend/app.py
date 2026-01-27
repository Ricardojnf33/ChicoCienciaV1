import streamlit as st
import sys
import os
import yaml
import json
import time
import threading
import queue
import io
from pathlib import Path
from PIL import Image

# Add parent directory to path to import src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.crews.ai_scientist_v2 import build_crew
from src.processes.ats_process import run_agentic_tree
from src.core.tree import AgenticTree
from src.config.logging_config import configure_logging

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="ChicoCienciaV1 - Dashboard",
    page_icon="🧠",
    layout="wide"
)

# --- STYLING ---
st.markdown("""
<style>
    .main {
        background-color: #0e1117;
    }
    .stButton>button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        height: 3em;
        border-radius: 10px;
        border: none;
        font-weight: bold;
    }
    .stCodeBlock {
        border-radius: 10px;
    }
    .css-1offfwp {
        padding: 2rem 1rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("🧠 ChicoCienciaV1: Orquestrador de Agentes Científicos")
st.markdown("---")

# --- SESSION STATE ---
if "logs" not in st.session_state:
    st.session_state.logs = ""
if "running" not in st.session_state:
    st.session_state.running = False
if "run_id" not in st.session_state:
    st.session_state.run_id = None

# --- LOGGING UTILITY ---
class StreamToQueue:
    def __init__(self, q):
        self.q = q
    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.q.put(line)
    def flush(self):
        pass

log_queue = queue.Queue()

# --- SIDEBAR: CONFIGURATION ---
with st.sidebar:
    st.header("⚙️ Configurações")
    budget = st.slider("Budget (Iterações)", min_value=1, max_value=20, value=3)
    verbose = st.checkbox("Logs Verbosos", value=True)
    
    st.markdown("### Status do Ambiente")
    env_file = Path("../.env")
    if os.path.exists(".env") or os.path.exists("../.env"):
        st.success("✅ .env localizado")
    else:
        st.error("❌ .env não localizado")

# --- MAIN AREA: INPUTS ---
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📝 Objetivo Científico")
    with st.form("objective_form"):
        title = st.text_input("Título do Experimento", value="Otimização de Classificação no Wine")
        question = st.text_area("Pergunta de Pesquisa", value="Como a regularização L2 impacta o F1-Score em dados de alta dimensão?")
        primary_metric = st.selectbox("Métrica Primária", ["accuracy", "f1_score", "precision", "recall"])
        datasets = st.multiselect("Datasets", ["iris", "wine", "digits"], default=["wine"])
        constraints = st.text_area("Constraints (JSON ou Texto)", value='["Reprodutibilidade (seed 42)"]')
        
        submit = st.form_submit_button("🚀 Iniciar Pesquisa Agentiva")

# --- EXECUTION LOGIC ---
if submit and not st.session_state.running:
    st.session_state.running = True
    st.session_state.logs = "Iniciando orquestração...\n"
    
    # Prepare objective dict
    obj_dict = {
        "objective": {
            "title": title,
            "question": question,
            "primary_metric": primary_metric,
            "datasets": datasets,
            "constraints": yaml.safe_load(constraints) if constraints else []
        }
    }
    
    # Save temporary yaml
    temp_yaml = "temp_objective.yaml"
    with open(temp_yaml, "w") as f:
        yaml.dump(obj_dict, f)
    
    def run_process():
        # Redirect stdout to queue
        old_stdout = sys.stdout
        sys.stdout = StreamToQueue(log_queue)
        
        try:
            configure_logging(verbose=verbose)
            crew = build_crew()
            tree = AgenticTree.new(objective_yaml=temp_yaml)
            run_id = "ui_" + str(int(time.time()))
            st.session_state.run_id = run_id
            
            run_agentic_tree(
                crew, 
                tree, 
                budget=budget, 
                checkpoint_path=f"runs/{run_id}.json"
            )
            print(f"\n--- EXECUÇÃO FINALIZADA ---")
        except Exception as e:
            print(f"\n❌ ERRO NA EXECUÇÃO: {str(e)}")
        finally:
            sys.stdout = old_stdout
            st.session_state.running = False

    # Start thread
    thread = threading.Thread(target=run_process)
    thread.start()

# --- REAL-TIME VISUALIZATION ---
with col2:
    st.header("💬 Conversa entre Agentes")
    log_container = st.empty()
    
    # Simple loop to display logs
    if st.session_state.running:
        log_container.code(st.session_state.logs, language="bash")
        # Rerun to keep checking the queue
        time.sleep(0.5)
        
        # Pull everything from queue
        new_lines = []
        while not log_queue.empty():
            new_lines.append(log_queue.get())
        
        if new_lines:
            st.session_state.logs += "\n".join(new_lines) + "\n"
            
        st.rerun()
    else:
        log_container.code(st.session_state.logs, language="bash")

# --- RESULTS & PLOTS ---
st.markdown("---")
st.header("📊 Artefatos e Resultados")

if st.session_state.logs:
    # Scan experiments directory for NEW plots
    exp_path = Path("experiments")
    if exp_path.exists():
        # Get subdirectories sorted by time
        nodes = sorted([d for d in exp_path.iterdir() if d.is_dir()], key=os.path.getmtime, reverse=True)
        
        if nodes:
            st.subheader(f"Últimos Resultados (Nó: {nodes[0].name})")
            res_col1, res_col2 = st.columns([1, 2])
            
            # Show results.json if exists
            res_json_path = nodes[0] / "results.json"
            # Some implementations save it in experiments/node_id/experiments/node_id/results.json
            nested_res = nodes[0] / "experiments" / nodes[0].name / "results.json"
            
            if nested_res.exists():
                res_json_path = nested_res
            
            if res_json_path.exists():
                with res_col1:
                    with open(res_json_path, 'r') as f:
                        data = json.load(f)
                        st.json(data)
            
            # Show plots
            with res_col2:
                # Find all pngs
                plots = list(nodes[0].glob("**/*.png"))
                if plots:
                    # Create tabs for plots
                    tab_names = [p.name for p in plots]
                    tabs = st.tabs(tab_names)
                    for i, tab in enumerate(tabs):
                        with tab:
                            st.image(str(plots[i]))
                else:
                    st.info("Aguardando geração de gráficos...")
        else:
            st.info("Nenhum experimento processado ainda.")
