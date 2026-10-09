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

    subtitle_style = ParagraphStyle(
        name="PDFSubTitle",
        parent=styles["Heading2"],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#2B6CB0"),
        spaceBefore=10,
        spaceAfter=5,
    )

    sub_info_style = ParagraphStyle(
        name="PDFSubInfo",
        parent=title_style,
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#4A5568"),
    )

    empresa_txt = nome_est if nome_est else "X-treme Parts"
    header_paragraphs = [Paragraph(f"<b>{empresa_txt}</b>", title_style)]

    if end_est:
        header_paragraphs.append(
            Paragraph(f"<b>Endereço:</b> {end_est}", sub_info_style)
        )
    if tel_est:
        header_paragraphs.append(
            Paragraph(f"<b>Telefone:</b> {tel_est}", sub_info_style)
        )
    if resp_est:
        header_paragraphs.append(
            Paragraph(f"<b>Responsável:</b> {resp_est}", sub_info_style)
        )

    for p in header_paragraphs:
        story.append(p)

    story.append(Spacer(1, 15))

    dados_veiculo = [
        [
            Paragraph("<b>Proprietário(a):</b>", body_style),
            Paragraph(prop or "-", body_style),
            Paragraph("<b>Telefone:</b>", body_style),
            Paragraph(tel_cli or "-", body_style),
        ],
        [
            Paragraph("<b>Veículo:</b>", body_style),
            Paragraph(veic or "-", body_style),
            Paragraph("<b>Cor / Ano:</b>", body_style),
            Paragraph(f"{cor_v or '-'} / {ano_v or '-'}", body_style),
        ],
        [
            Paragraph("<b>Data Atendimento:</b>", body_style),
            Paragraph(data_atend or "-", body_style),
            Paragraph("<b>Status:</b>", body_style),
            Paragraph(status_atend or "-", body_style),
        ],
    ]
    tabela = Table(dados_veiculo, colWidths=[100, 170, 90, 180])
    tabela.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7FAFC")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("PADDING", (0, 0), (-1, -1), 6),
        ])
    )
    story.append(tabela)
    story.append(Spacer(1, 10))

    if serv_acert:
        story.append(Paragraph("Serviços Acertados", subtitle_style))
        story.append(Paragraph(serv_acert, body_style))
        story.append(Spacer(1, 10))

    if obs_vist:
        story.append(Paragraph("Observações da Vistoria", subtitle_style))
        story.append(Paragraph(obs_vist, body_style))
        story.append(Spacer(1, 10))

    if obs_fin or (val_fin and val_fin > 0) or pix:
        story.append(Paragraph("Finalização do Serviço", subtitle_style))
        if obs_fin:
            story.append(
                Paragraph(f"<b>Observações Finais:</b> {obs_fin}", body_style)
            )
        if val_fin and val_fin > 0:
            story.append(
                Paragraph(
                    f"<b>Valor Total do Serviço:</b> R$ {val_fin:.2f}",
                    body_style,
                )
            )
        if pix:
            story.append(
                Paragraph(f"<b>Chave Pix para Pagamento:</b> {pix}", body_style)
            )
        story.append(Spacer(1, 10))

    def adicionar_fotos_pdf(caminhos_json, titulo):
        try:
            lista_paths = json.loads(caminhos_json) if caminhos_json else []
        except Exception:
            lista_paths = []

        if not lista_paths:
            return

        story.append(Paragraph(titulo, subtitle_style))
        imgs_row = []
        tabela_fotos = []
        for p_foto in lista_paths:
            if os.path.exists(p_foto):
                try:
                    img = Image.open(p_foto)
                    img_io = io.BytesIO()
                    img.convert("RGB").save(img_io, format="JPEG", quality=75)
                    img_io.seek(0)
                    rl_img = RLImage(img_io, width=160, height=120)
                    imgs_row.append(rl_img)

                    if len(imgs_row) == 3:
                        tabela_fotos.append(imgs_row)
                        imgs_row = []
                except Exception:
                    continue
        if imgs_row:
            while len(imgs_row) < 3:
                imgs_row.append("")
            tabela_fotos.append(imgs_row)

        if tabela_fotos:
            t_fotos = Table(tabela_fotos, colWidths=[180, 180, 180])
            t_fotos.setStyle(
                TableStyle([
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("PADDING", (0, 0), (-1, -1), 4),
                ])
            )
            story.append(t_fotos)
            story.append(Spacer(1, 10))

    adicionar_fotos_pdf(f_vist_json, "Fotos da Vistoria Inicial")
    adicionar_fotos_pdf(f_fin_json, "Fotos do Veículo Finalizado")

    doc.build(story)
    buffer.seek(0)
    return buffer


# --- MENU LATERAL ---
st.sidebar.title("📌 Menu")
opcao_menu = st.sidebar.radio(
    "Navegação",
    [
        "📝 Novo Cadastro / Vistoria",
        "🚗 Abrir Atendimento (Veículo Existente)",
        "📂 Histórico de Atendimento",
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

    clientes = listar_clientes()

    if clientes:
        cliente_opcoes = {f"{c[1]} (Tel: {c[2]})": c[0] for c in clientes}
        cliente_selecionado_nome = st.selectbox(
            "👤 Selecione o Cliente / Proprietário(a):",
            options=list(cliente_opcoes.keys()),
        )
        cliente_id_sel = cliente_opcoes[cliente_selecionado_nome]

        veiculos_cliente = buscar_veiculos_cliente(cliente_id_sel)

        if veiculos_cliente:
            veiculo_opcoes = {
                f"{v[1]} ({v[2]} - Ano {v[3]}) [Atendimento #{v[0]}]": v[0]
                for v in veiculos_cliente
            }
            veiculo_selecionado_str = st.selectbox(
                "🚗 Selecione qual veículo cadastrado deseja mexer:",
                options=list(veiculo_opcoes.keys()),
            )
            atendimento_id_sel = veiculo_opcoes[veiculo_selecionado_str]

            reg = carregar_atendimento_por_id(atendimento_id_sel)
            if reg:
                (
                    reg_id,
                    cli_id,
                    data_atend,
                    nome_est,
                    end_est,
                    tel_est,
                    resp_est,
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

                st.info(
                    f"Atendimento selecionado para: **{prop}** - Veículo: **{veic}** ({cor_v} - {ano_v}) | Status: **{status_atend}**"
                )

                st.divider()
                st.subheader("🛠️ 4. Serviços Combinados")
                servicos_acertados = st.text_area(
                    "Descreva os serviços acertados com o cliente:",
                    value=serv_acert or "",
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
                            if st.button(f"Concluir: {etapa}", key=f"etp_{idx}"):
                                st.session_state.etapa_atual += 1
                                st.rerun()

                observacoes_finais = ""
                valor_final = val_fin or 0.0
                chave_pix = pix or ""
                fotos_finalizacao = []

                if st.session_state.etapa_atual == len(etapas):
                    st.divider()
                    st.subheader("✨ 6. Finalização e Entrega")

                    col_v1, col_v2, col_v3 = st.columns(3)
                    with col_v1:
                        valor_final = st.number_input(
                            "💰 Valor Total dos Serviços (R$):",
                            min_value=0.0,
                            value=float(val_fin or 0.0),
                            format="%.2f",
                            step=10.0,
                        )
                    with col_v2:
                        chave_pix = st.text_input(
                            "🔑 Chave Pix para Pagamento:",
                            value=pix or "",
                            placeholder="Ex: CPF, CNPJ, Telefone ou E-mail",
                        )
                    with col_v3:
                        observacoes_finais = st.text_area(
                            "📝 Observações Finais / Recomendações:",
                            value=obs_fin or "",
                            placeholder="Ex: Não lavar o veículo pelas próximas 48h.",
                        )

                    st.subheader("📸 Fotos do Veículo Finalizado")
                    fotos_finalizacao = st.file_uploader(
                        "Anexe as fotos do veículo pronto/entregue:",
                        type=["png", "jpg", "jpeg"],
                        accept_multiple_files=True,
                        key="finalizacao_existente",
                    )

                if tel_cli and veic:
                    st.divider()
                    st.subheader("📲 Notificar Cliente via WhatsApp")

                    etapa_nome = (
                        etapas[st.session_state.etapa_atual - 1]
                        if st.session_state.etapa_atual > 0
                        else "Cadastro Inicial"
                    )

                    texto_detalhes = ""
                    if etapa_nome == "Vistoria Concluída":
                        if obs_vist:
                            texto_detalhes += f"\n\n📌 *Vistoria:* {obs_vist}"
                        if servicos_acertados:
                            texto_detalhes += (
                                f"\n🛠️ *Serviços Acertados:* {servicos_acertados}"
                            )

                    elif st.session_state.etapa_atual == len(etapas):
                        if observacoes_finais:
                            texto_detalhes += (
                                f"\n\n📝 *Observações Finais:* {observacoes_finais}"
                            )
                        if valor_final > 0:
                            texto_detalhes += (
                                f"\n💰 *Valor Total:* R$ {valor_final:.2f}"
                            )
                        if chave_pix:
                            texto_detalhes += f"\n🔑 *Chave Pix:* {chave_pix}"

                        texto_detalhes += (
                            "\n\n✨ *\"Cuidamos hoje do bem que um dia foi seu maior sonho, "
                            "porque aquilo que conquistamos merece ser preservado nos mínimos detalhes.\"*"
                        )

                    cabecalho_empresa = (
                        f"*{nome_est}*\n" if nome_est else ""
                    )

                    mensagem = (
                        f"{cabecalho_empresa}"
                        f"Olá {prop}! 👋\n\n"
                        f"Atualização sobre o seu veículo *{veic}* ({cor_v} - {ano_v}):\n"
                        f"Status: *{etapa_nome}*{texto_detalhes}\n\n"
                        f"Qualquer dúvida, estamos à disposição!"
                    )

                    link_wa = gerar_link_whatsapp(tel_cli, mensagem)

                    st.markdown(
                        f'<a href="{link_wa}" target="_blank">'
                        f'<button style="background-color:#25D366; color:white; border:none; padding:12px 24px; border-radius:8px; cursor:pointer; font-weight:bold; font-size:16px;">'
                        f"Enviar Status via WhatsApp 🚀"
                        f"</button></a>",
                        unsafe_allow_html=True,
                    )

                st.divider()
                st.subheader("💾 Salvar e Gerar Relatório")

                col_b1, col_b2 = st.columns(2)

                with col_b1:
                    if st.button("💾 Concluir e Atualizar Atendimento"):
                        dados_atualizacao = {
                            "servicos_acertados": servicos_acertados,
                            "observacoes_finais": observacoes_finais,
                            "valor_final": valor_final,
                            "chave_pix": chave_pix,
                        }
                        atualizar_atendimento_db(
                            atendimento_id_sel,
                            dados_atualizacao,
                            fotos_finalizacao,
                        )
                        st.success(
                            "✅ Atendimento atualizado e salvo com sucesso!"
                        )
                        st.rerun()

                with col_b2:
                    pdf_file = gerar_pdf_relatorio(reg)
                    st.download_button(
                        label="📥 Baixar PDF para Enviar ao Cliente",
                        data=pdf_file,
                        file_name=f"relatorio_{veic or 'veiculo'}.pdf",
                        mime="application/pdf",
                    )
        else:
            st.warning("Este cliente ainda não possui veículos cadastrados.")
    else:
        st.info(
            "Nenhum cliente cadastrado ainda. Vá em 'Novo Cadastro / Vistoria' primeiro."
        )

# ==========================================
# ABA 3: HISTÓRICO DE ATENDIMENTO
# ==========================================
elif opcao_menu == "📂 Histórico de Atendimento":
    st.title("📂 Histórico de Atendimentos")

    termo_busca = st.text_input(
        "🔍 Buscar por Proprietário(a), Veículo ou Telefone:",
        placeholder="Digite o nome ou modelo do carro...",
    )

    registros = buscar_atendimentos(termo_busca)

    if registros:
        st.write(f"**Total de registros encontrados:** {len(registros)}")

        for reg in registros:
            (
                reg_id,
                cli_id,
                data_atend,
                nome_est,
                end_est,
                tel_est,
                resp_est,
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
                status,
            ) = reg

            status_tag = "🟡 Em Aberto" if status == "Em Aberto" else "✅ Concluído"

            with st.expander(
                f"{status_tag} | 🚗 {veic or 'Veículo'} - {prop or 'Cliente'} ({data_atend})"
            ):
                col_h1, col_h2 = st.columns(2)
                with col_h1:
                    st.write(f"**Proprietário(a):** {prop or '-'}")
                    st.write(f"**Telefone:** {tel_cli or '-'}")
                    st.write(f"**Veículo:** {veic or '-'}")
                    st.write(f"**Cor / Ano:** {cor_v or '-'} / {ano_v or '-'}")
                with col_h2:
                    st.write(f"**Valor Total:** R$ {val_fin or 0.0:.2f}")
                    st.write(f"**Chave Pix:** {pix or '-'}")
                    st.write(f"**Responsável:** {resp_est or '-'}")

                if serv_acert:
                    st.write(f"**Serviços Executados:**\n{serv_acert}")
                if obs_vist:
                    st.write(f"**Observações de Vistoria:**\n{obs_vist}")
                if obs_fin:
                    st.write(f"**Observações Finais:**\n{obs_fin}")

                # Fotos Vistoria
                try:
                    caminhos_vist = json.loads(f_vist_json) if f_vist_json else []
                except Exception:
                    caminhos_vist = []

                if caminhos_vist:
                    st.write("**📸 Fotos da Vistoria Inicial:**")
                    cols_hv = st.columns(3)
                    for idx_f, p_foto in enumerate(caminhos_vist):
                        if os.path.exists(p_foto):
                            with cols_hv[idx_f % 3]:
                                st.image(
                                    p_foto,
                                    caption=f"Vistoria {idx_f + 1}",
                                    use_container_width=True,
                                )

                # Fotos Finalização
                try:
                    caminhos_fin = json.loads(f_fin_json) if f_fin_json else []
                except Exception:
                    caminhos_fin = []

                if caminhos_fin:
                    st.write("**📸 Fotos do Veículo Finalizado:**")
                    cols_hf = st.columns(3)
                    for idx_f, p_foto in enumerate(caminhos_fin):
                        if os.path.exists(p_foto):
                            with cols_hf[idx_f % 3]:
                                st.image(
                                    p_foto,
                                    caption=f"Finalizado {idx_f + 1}",
                                    use_container_width=True,
                                )

                st.divider()
                pdf_file_hist = gerar_pdf_relatorio(reg)
                st.download_button(
                    label=f"📥 Baixar PDF deste Atendimento (#{reg_id})",
                    data=pdf_file_hist,
                    file_name=f"relatorio_atendimento_{reg_id}_{veic or 'veiculo'}.pdf",
                    mime="application/pdf",
                    key=f"dl_hist_{reg_id}",
                )
    else:
        st.info("Nenhum histórico de atendimento encontrado.")
