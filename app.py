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
        CREATE TABLE IF NOT EXISTS atendimentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            status TEXT
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


def cadastrar_cliente_vistoria(dados, arquivos_vistoria):
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
            data_atendimento, nome_estabelecimento, endereco_empresa, telefone_empresa, responsavel_empresa,
            proprietario, telefone_cliente, veiculo, cor, ano, observacoes_vistoria,
            fotos_vistoria, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
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


def atualizar_atendimento_db(atendimento_id, dados, arquivos_finalizacao):
    timestamp_pasta = datetime.now().strftime("%Y%m%d_%H%M%S")

    caminhos_finalizacao = []
    if arquivos_finalizacao:
        for f in arquivos_finalizacao:
            caminhos_finalizacao.append(
                salvar_foto_disco(f, f"{timestamp_pasta}_finalizacao")
            )

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
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


# --- MENU LATERAL ---
st.sidebar.title("📌 Menu")
opcao_menu = st.sidebar.radio(
    "Navegação", ["📝 Cadastro & Vistoria", "📂 Histórico de Clientes"]
)

# ==========================================
# ABA 1: CADASTRO & ABERTURA DE ATENDIMENTO
# ==========================================
if opcao_menu == "📝 Cadastro & Vistoria":
    st.title("🚗 Cadastro do Cliente & Vistoria Inicial")

    # ETAPA 1: CADASTRO DO CLIENTE E VEÍCULO
    if "atendimento_id_atual" not in st.session_state:
        st.session_state.atendimento_id_atual = None

    if st.session_state.atendimento_id_atual is None:
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
            veiculo = st.text_input("Veículo:")
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
            st.write(
                f"**{len(fotos_vistoria)} foto(s) de vistoria carregada(s):**"
            )
            cols = st.columns(3)
            for index, foto in enumerate(fotos_vistoria):
                with cols[index % 3]:
                    st.image(
                        foto,
                        caption=f"Vistoria {index + 1}",
                        use_container_width=True,
                    )

        st.divider()

        if st.button("💾 Realizar Cadastro e Abrir Atendimento"):
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
                novo_id = cadastrar_cliente_vistoria(
                    dados_cadastro, fotos_vistoria
                )
                st.session_state.atendimento_id_atual = novo_id
                st.session_state.dados_atual = dados_cadastro
                st.session_state.etapa_atual = 0
                st.success(
                    f"✅ Cadastro #{novo_id} realizado com sucesso! Prosseguindo com os serviços..."
                )
                st.rerun()
            else:
                st.error("⚠️ Preencha os campos obrigatórios (Veículo e Proprietário).")

    # ETAPA 2: SERVIÇOS E ACOMPANHAMENTO DO ATENDIMENTO
    else:
        st.info(
            f"🚗 **Atendimento em Andamento - Registro #{st.session_state.atendimento_id_atual}**"
        )
        dados = st.session_state.dados_atual

        st.write(
            f"**Cliente:** {dados.get('proprietario')} | **Veículo:** {dados.get('veiculo')} ({dados.get('cor')} - {dados.get('ano')})"
        )

        st.divider()
        st.subheader("🛠️ 4. Serviços Combinados")
        servicos_acertados = st.text_area(
            "Descreva os serviços acertados com o cliente:",
            placeholder="Ex: Lavagem detalhada, Higienização interna, Vitrificação de pintura.",
        )

        st.divider()
        st.subheader("⚙️ 5. Acompanhamento do Processo")

        etapas = [
            "Vistoria Concluída",
            "🚿 Já iniciamos a lavagem e limpeza do seu veículo.",
            "🌬 Lavagem finalizada, estamos no processo de secagem e aplicação de acabamentos solicitados.",
            "🌟 Processo final de serviços, em poucos minutos estará pronto.",
            "🫡 Prontinho, seu veículo está pronto para ser retirado, estamos te aguardando.",
        ]

        if "etapa_atual" not in st.session_state:
            st.session_state.etapa_atual = 0

        def gerar_link_whatsapp(num, texto):
            texto_codificado = urllib.parse.quote(texto)
            return f"https://api.whatsapp.com/send?phone=55{num}&text={texto_codificado}"

        for idx, etapa in enumerate(etapas):
            col_status, col_acao = st.columns([3, 2])

            with col_status:
                if idx < st.session_state.etapa_atual:
                    st.success(f"✅ {etapa}")
                elif idx == st.session_state.etapa_atual:
                    st.warning(f"⏳ Em andamento: {etapa}")
                else:
                    st.caption(f"⚪ {etapa}")

            with col_acao:
                if idx == st.session_state.etapa_atual:
                    if st.button(f"Concluir: {etapa}", key=idx):
                        st.session_state.etapa_atual += 1
                        st.rerun()

        observacoes_finais = ""
        valor_final = 0.0
        chave_pix = ""
        fotos_finalizacao = []

        if st.session_state.etapa_atual == len(etapas):
            st.divider()
            st.subheader("✨ 6. Finalização e Entrega")

            col_v1, col_v2, col_v3 = st.columns(3)
            with col_v1:
                valor_final = st.number_input(
                    "💰 Valor Total dos Serviços (R$):",
                    min_value=0.0,
                    format="%.2f",
                    step=10.0,
                )
            with col_v2:
                chave_pix = st.text_input(
                    "🔑 Chave Pix para Pagamento:",
                    placeholder="Ex: CPF, CNPJ, Telefone ou E-mail",
                )
            with col_v3:
                observacoes_finais = st.text_area(
                    "📝 Observações Finais / Recomendações:",
                    placeholder="Ex: Não lavar o veículo pelas próximas 48h.",
                )

            st.subheader("📸 Fotos do Veículo Finalizado")
            fotos_finalizacao = st.file_uploader(
                "Anexe as fotos do veículo pronto/entregue:",
                type=["png", "jpg", "jpeg"],
                accept_multiple_files=True,
                key="finalizacao",
            )

            if fotos_finalizacao:
                st.write(
                    f"**{len(fotos_finalizacao)} foto(s) de finalização carregada(s):**"
                )
                cols_fin = st.columns(3)
                for index, foto in enumerate(fotos_finalizacao):
                    with cols_fin[index % 3]:
                        st.image(
                            foto,
                            caption=f"Finalizado {index + 1}",
                            use_container_width=True,
                        )

        # NOTIFICAÇÃO VIA WHATSAPP
        if dados.get("telefone") and dados.get("veiculo"):
            st.divider()
            st.subheader("📲 Notificar Cliente via WhatsApp")

            etapa_nome = (
                etapas[st.session_state.etapa_atual - 1]
                if st.session_state.etapa_atual > 0
                else "Cadastro Inicial"
            )

            texto_detalhes = ""
            if etapa_nome == "Vistoria Concluída":
                if dados.get("observacoes_vistoria"):
                    texto_detalhes += (
                        f"\n\n📌 *Vistoria:* {dados.get('observacoes_vistoria')}"
                    )
                if servicos_acertados:
                    texto_detalhes += (
                        f"\n🛠️ *Serviços Acertados:* {servicos_acertados}"
                    )

            elif st.session_state.etapa_atual == len(etapas):
                if observacoes_finais:
                    texto_detalhes += (
                        f"\n\n📝 *Observações Finais:* {observacoes_finais}"
                    )
                if valor
