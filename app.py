import io
import urllib.parse
from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    Image as RLImage,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
import streamlit as st

st.set_page_config(page_title="Estética Automotiva - Gestão", page_icon="🚗")

st.title("🚗 Controle de Serviços - Estética Automotiva")

# --- DADOS DO ESTABELECIMENTO E VEÍCULO ---
st.subheader("📋 Dados Gerais")

col_emp1, col_emp2 = st.columns([2, 1])
with col_emp1:
    nome_estabelecimento = st.text_input(
        "Nome do Estabelecimento:",
        placeholder="Digite o nome da sua estética automotiva",
    )
    endereco_empresa = st.text_input(
        "Endereço da Estética:",
    )
    col_emp_sub1, col_emp_sub2 = st.columns(2)
    with col_emp_sub1:
        telefone_empresa = st.text_input(
            "Telefone da Estética:",
            placeholder
