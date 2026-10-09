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
        placeholder="Ex: Rua Papa Leão I, 35 - Ouro Minas",
    )
    col_emp_sub1, col_emp_sub2 = st.columns(2)
    with col_emp_sub1:
        telefone_empresa = st.text_input(
            "Telefone da Estética:",
            placeholder="Ex: (31) 99999-8888",
        )
    with col_emp_sub2:
        responsavel_empresa = st.text_input(
            "Responsável:",
            placeholder="Ex: Pikachu",
        )

with col_emp2:
    logo_empresa = st.file_uploader(
        "Logo da Empresa (para o PDF):",
        type=["png", "jpg", "jpeg"],
        key="logo",
    )

st.divider()

col1, col2 = st.columns(2)
with col1:
    veiculo = st.text_input("Veículo:")
    cor = st.text_input("Cor:")
with col2:
    ano = st.text_input("Ano:")
    proprietario = st.text_input("Proprietário(a):")

telefone = st.text_input(
    "Telefone do Cliente (DDD + Número, ex: 31999998888):"
)

# --- CAMPO DE OBSERVAÇÕES / VISTORIA ---
observacoes_vistoria = st.text_area(
    "📝 Observações da Vistoria (Avarias, detalhes de pintura, etc.):",
    placeholder="Ex: Risco no pára-choque dianteiro lado direito, banco de couro com pequena mancha.",
)

# --- FOTOS DA VISTORIA INICIAL ---
st.subheader("📸 Fotos da Vistoria Inicial")
fotos_vistoria = st.file_uploader(
    "Anexe ou tire fotos das avarias/estado inicial do veículo:",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=True,
    key="vistoria",
)

if fotos_vistoria:
    st.write(f"**{len(fotos_vistoria)} foto(s) de vistoria carregada(s):**")
    cols = st.columns(3)
    for index, foto in enumerate(fotos_vistoria):
        with cols[index % 3]:
            
