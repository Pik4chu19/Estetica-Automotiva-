import io
import json
import os
import sqlite3
import urllib.parse
from datetime import datetime
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

st.set_page_config(page_title="X-treme Parts - Gestão", page_icon="🚗")

# --- BANCO DE DADOS E DIRETÓRIOS ---
DB_NAME = "estetica.db"
PASTA_FOTOS = "fotos_clientes"

if not os.path.exists(PASTA_FOTOS):
    os.makedirs(PASTA_FOTOS)


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            telefone TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS atendimentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            data_atendimento TEXT,
            nome_estabelecimento TEXT,
            endereco_empresa TEXT,
            telefone_empresa TEXT,
            responsavel_empresa TEXT,
            proprietario TEXT,
            telefone_cliente TEXT,
            veiculo TEXT,
            cor TEXT,
            ano TEXT,
            observacoes_vistoria TEXT,
            servicos_acertados TEXT,
            observacoes_finais TEXT,
            valor_final REAL,
            chave_pix TEXT,
            fotos_vistoria TEXT,
            fotos_finalizacao TEXT,
            status TEXT,
            FOREIGN KEY(cliente_id) REFERENCES clientes(id)
        )
    """)
    conn.commit()
    conn.close()


init_db()


def salvar_foto_disco(uploaded_file, subpasta):
    pasta_destino = os.path.join(PASTA_FOTOS, subpasta)
    if not os.path.exists(pasta_destino):
        os.makedirs(pasta_destino)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"{timestamp}_{uploaded_file.name}"
    filepath = os.path.join(pasta_destino, filename)

    with open(filepath, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return filepath


def listar_clientes():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, telefone FROM clientes ORDER BY nome")
    rows = cursor.fetchall()
    conn.close()
    return rows


def buscar_veiculos_cliente(cliente_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, veiculo, cor, ano FROM atendimentos WHERE cliente_id = ? ORDER BY id DESC",
        (cliente_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def cadastrar_cliente_e_veiculo(dados, arquivos_vistoria):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM clientes WHERE nome = ? OR telefone = ?",
        (dados.get("proprietario"), dados.get("telefone")),
    )
    cliente = cursor.fetchone()

    if cliente:
        cliente_id = cliente[0]
    else:
        cursor.execute(
            "INSERT INTO clientes (nome, telefone) VALUES (?, ?)",
            (dados.get("proprietario"), dados.get("telefone")),
        )
        cliente_id = cursor.lastrowid

    conn.commit()
    conn.close()

    timestamp_pasta = datetime.now().strftime("%Y%m%d_%H%M%S")
    caminhos_vistoria = []
    if arquivos_vistoria:
        for f in arquivos_vistoria:
            caminhos_vistoria.append(
                salvar_foto_disco(f, f"{timestamp_pasta}_vistoria")
            )

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO atendimentos (
            cliente_id, data_atendimento, nome_estabelecimento, endereco_empresa, telefone_empresa, responsavel_empresa,
            proprietario, telefone_cliente, veiculo, cor, ano, observacoes_vistoria,
            fotos_vistoria, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            cliente_id,
            datetime.now().strftime("%d/%m/%Y %H:%M"),
            dados.get("nome_estabelecimento", ""),
            dados.get("endereco_empresa", ""),
            dados.get("telefone_empresa", ""),
            dados.get("responsavel_empresa", ""),
            dados.get("proprietario", ""),
            dados.get("telefone", ""),
            dados.get("veiculo", ""),
            dados.get("cor", ""),
            dados.get("ano", ""),
            dados.get("observacoes_vistoria", ""),
            json.dumps(caminhos_vistoria),
            "Em Aberto",
        ),
    )
    atendimento_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return atendimento_id


def atualizar_atendimento_db(
    atendimento_id, dados, arquivos_finalizacao_novos
):
    timestamp_pasta = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Buscar fotos de finalização existentes para não apagar ao atualizar
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT fotos_finalizacao FROM atendimentos WHERE id = ?",
        (atendimento_id,),
    )
    res = cursor.fetchone()
    caminhos_finalizacao = json.loads(res[0]) if res and res[0] else []

    if arquivos_finalizacao_novos:
        for f in arquivos_finalizacao_novos:
            caminhos_finalizacao.append(
                salvar_foto_disco(f, f"{timestamp_pasta}_finalizacao")
            )

    cursor.execute(
        """
        UPDATE atendimentos SET
            servicos_acertados = ?,
            observacoes_finais = ?,
            valor_final = ?,
            chave_pix = ?,
            fotos_finalizacao = ?,
            status = ?
        WHERE id = ?
    """,
        (
            dados.get("servicos_acertados", ""),
            dados.get("observacoes_finais", ""),
            dados.get("valor_final", 0.0),
            dados.get("chave_pix", ""),
            json.dumps(caminhos_finalizacao),
            "Concluído",
            atendimento_id,
        ),
    )
    conn.commit()
    conn.close()


def buscar_atendimentos(termo=""):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if termo:
        query = "%" + termo + "%"
        cursor.execute(
            """
            SELECT * FROM atendimentos 
            WHERE proprietario LIKE ? OR veiculo LIKE ? OR telefone_cliente LIKE ?
            ORDER BY id DESC
        """,
            (query, query, query),
        )
    else:
        cursor.execute("SELECT * FROM atendimentos ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows


def carregar_atendimento_por_id(atendimento_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM atendimentos WHERE id = ?", (atendimento_id,))
    row = cursor.fetchone()
    conn.close()
    return row


# --- MENU LATERAL ---
st.sidebar.title("📌 Menu")
opcao_menu = st.sidebar.radio(
    "Navegação",
    [
        "📝 Novo Cadastro / Vistoria",
        "🚗 Abrir Atendimento (Veículo Existente)",
        "📂 Histórico de Clientes",
    ],
)

# ==========================================
# ABA 1: NOVO CADASTRO / VISTORIA
# ==========================================
if opcao_menu == "📝 Novo Cadastro / Vistoria":
    st.title("🚗 Novo Cadastro de Cliente / Veículo & Vistoria")

    st.subheader("📋 1. Dados do Estabelecimento")
    col_emp1, col_emp2 = st.columns([2, 1])
    with col_emp1:
        nome_estabelecimento = st.text_input(
            "Nome do Estabelecimento:",
            placeholder="Digite o nome da sua estética automotiva",
        )
        endereco_empresa = st.text_input("Endereço da Estética:")
        col_emp_sub1, col_emp_sub2 = st.columns(2)
        with col_emp_sub1:
            telefone_empresa = st.text_input(
                "Telefone da Estética:", placeholder="Ex: (31) 99999-8888"
            )
        with col_emp_sub2:
            responsavel_empresa = st.text_input(
                "Responsável:", placeholder="Ex: Pikachu"
            )

    with col_emp2:
        logo_empresa = st.file_uploader(
            "Logo da Empresa (para o PDF):",
            type=["png", "jpg", "jpeg"],
            key="logo",
        )

    st.divider()
    st.subheader("👤 2. Dados do Cliente e Veículo")
    col1, col2 = st.columns(2)
    with col1:
        veiculo = st.text_input("Veículo (Ex: Fiat Palio):")
        cor = st.text_input("Cor:")
    with col2:
        ano = st.text_input("Ano:")
        proprietario = st.text_input("Proprietário(a):")

    telefone = st.text_input(
        "Telefone do Cliente (DDD + Número, ex: 31999998888):"
    )

    st.subheader("📸 3. Vistoria Inicial")
    observacoes_vistoria = st.text_area(
        "📝 Observações da Vistoria (Avarias, detalhes de pintura, etc.):",
        placeholder="Ex: Risco no pára-choque dianteiro lado direito, banco de couro com pequena mancha.",
    )

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
                st.image(
                    foto,
                    caption=f"Vistoria {index + 1}",
                    use_container_width=True,
                )

    st.divider()

    if st.button("💾 Cadastrar Cliente e Veículo"):
        if veiculo and proprietario:
            dados_cadastro = {
                "nome_estabelecimento": nome_estabelecimento,
                "endereco_empresa": endereco_empresa,
                "telefone_empresa": telefone_empresa,
                "responsavel_empresa": responsavel_empresa,
                "proprietario": proprietario,
                "telefone": telefone,
                "veiculo": veiculo,
                "cor": cor,
                "ano": ano,
                "observacoes_vistoria": observacoes_vistoria,
            }
            novo_id = cadastrar_cliente_e_veiculo(
                dados_cadastro, fotos_vistoria
            )
            st.success(
                f"✅ Cadastro realizado com sucesso! (ID do Atendimento: #{novo_id})"
            )
            st.info(
                "💡 Vá na aba **'Abrir Atendimento (Veículo Existente)'** para gerenciar os serviços deste veículo."
            )
        else:
            st.error("⚠️ Preencha os campos obrigatórios (Veículo e Proprietário).")

# ==========================================
# ABA 2: ABRIR ATENDIMENTO (SELECIONAR VEÍCULO CADASTRADO)
# ==========================================
elif opcao_menu == "🚗 Abrir Atendimento (Veículo Existente)":
    st.title("⚙️ Gerenciar Atendimento de Veículo Cadastrado")

    clientes
