#!/bin/bash
cd "$(dirname "$0")"
.venv/bin/streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0
