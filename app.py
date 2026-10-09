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

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT fotos_finalizacao FROM atendimentos WHERE id = ?",
        (atendimento_id,),
    )
    res = cursor.fetchone()
    caminhos_final
