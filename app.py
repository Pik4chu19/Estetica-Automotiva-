import io
import json
import os
import sqlite3
import urllib.parse
from datetime import datetime
from PIL import Image as PILImage
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
            logo_path TEXT,
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


def cadastrar_cliente_e_veiculo(dados, arquivos_vistoria, logo_file):
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

    logo_path = ""
    if logo_file:
        logo_path = salvar_foto_disco(logo_file, f"{timestamp_pasta}_logo")

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
            cliente_id, data_atendimento, nome_estabelecimento, endereco_empresa, telefone_empresa, responsavel_empresa, logo_path,
            proprietario, telefone_cliente, veiculo, cor, ano, observacoes_vistoria,
            fotos_vistoria, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            cliente_id,
            datetime.now().strftime("%d/%m/%Y %H:%M"),
            dados.get("nome_estabelecimento", ""),
            dados.get("endereco_empresa", ""),
            dados.get("telefone_empresa", ""),
            dados.get("responsavel_empresa", ""),
            logo_path,
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


def gerar_pdf_relatorio(reg):
    (
        reg_id,
        cli_id,
        data_atend,
        nome_est,
        end_est,
        tel_est,
        resp_est,
        logo_path,
        prop,
        tel_cli,
        veic,
        cor_v,
        ano_v,
        obs_vist,
        serv_acert,
        obs_fin,
        val_fin,
        pix,
        f_vist_json,
        f_fin_json,
        status_atend,
    ) = reg

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    story = []

    styles = getSampleStyleSheet()
    body_style = styles["BodyText"]

    title_style = ParagraphStyle(
        name="PDFTitle",
        parent=styles["Heading1"],
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#1A365D"),
    )

    sub_info_style = ParagraphStyle(
        name="PDFSubInfo",
        parent=title_style,
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#4A5568"),
    )

    subtitle_style = ParagraphStyle(
        name="PDFSubTitle",
        parent=styles["Heading2"],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#2B6CB0"),
        spaceBefore=10,
        spaceAfter=5,
    )

    empresa_txt = nome_est if nome_est else "X-treme Parts"
    texto_empresa_elements = [Paragraph(f"<b>{empresa_txt}</b>", title_style)]

    if end_est:
        texto_empresa_elements.append(
            Paragraph(f"<b>Endereço:</b> {end_est}", sub_info_style)
        )
    if tel_est:
        texto_empresa_elements.append(
            Paragraph(f"<b>Telefone:</b> {tel_est}", sub_info_style)
        )
    if resp_est:
        texto_empresa_elements.append(
            Paragraph(f"<b>Responsável:</b> {resp_est}", sub_info_style)
        )

    header_table_data = []
    logo_img = ""
    if logo_path and os.path.exists(logo_path):
        try:
            img = PILImage.open(logo_path)
            img_io = io.BytesIO()
            img.convert("RGB").save(img_io, format="JPEG", quality=80)
            img_io.seek(0)
            logo_img = RLImage(img_io, width=70, height=70)
        except Exception:
            logo_img = ""

    if logo_img:
        header_table_data.append([logo_img, texto_empresa_elements])
        t_header = Table(header_table_data, colWidths=[80, 460])
        t_header.setStyle(
            TableStyle
