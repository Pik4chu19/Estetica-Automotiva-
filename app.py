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

# --- CONFIGURAÇÃO DO BANCO DE DADOS E DIRETÓRIOS ---
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
            fotos_finalizacao TEXT
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


def salvar_atendimento_db(dados, arquivos_vistoria, arquivos_finalizacao):
    timestamp_pasta = datetime.now().strftime("%Y%m%d_%H%M%S")

    caminhos_vistoria = []
    if arquivos_vistoria:
        for f in arquivos_vistoria:
            caminhos_vistoria.append(
                salvar_foto_disco(f, f"{timestamp_pasta}_vistoria")
            )

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
        INSERT INTO atendimentos (
            data_atendimento, nome_estabelecimento, endereco_empresa, telefone_empresa, responsavel_empresa,
            proprietario, telefone_cliente, veiculo, cor, ano, observacoes_vistoria, servicos_acertados,
            observacoes_finais, valor_final, chave_pix, fotos_vistoria, fotos_finalizacao
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            dados.get("servicos_acertados", ""),
            dados.get("observacoes_finais", ""),
            dados.get("valor_final", 0.0),
            dados.get("chave_pix", ""),
            json.dumps(caminhos_vistoria),
            json.dumps(caminhos_finalizacao),
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
    "Navegação", ["🚗 Atendimento Atual", "📂 Histórico de Clientes"]
)

# ==========================================
# ABA 1: ATENDIMENTO ATUAL
# ==========================================
if opcao_menu == "🚗 Atendimento Atual":
    st.title("🚗 Controle de Serviços - Estética Automotiva")

    st.subheader("📋 Dados Gerais")

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

    observacoes_vistoria = st.text_area(
        "📝 Observações da Vistoria (Avarias, detalhes de pintura, etc.):",
        placeholder="Ex: Risco no pára-choque dianteiro lado direito, banco de couro com pequena mancha.",
    )

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
                st.image(
                    foto,
                    caption=f"Vistoria {index + 1}",
                    use_container_width=True,
                )

    st.subheader("🛠️ Serviços Acertados com o Cliente")
    servicos_acertados = st.text_area(
        "Descreva os serviços a serem executados:",
        placeholder="Ex: Lavagem detalhada, Higienização interna, Vitrificação de pintura.",
    )

    st.divider()

    st.subheader("⚙️ Acompanhamento do Processo")

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
        st.subheader("✨ Finalização e Entrega")

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

    if telefone and veiculo:
        st.divider()
        st.subheader("📲 Notificar Cliente")

        etapa_nome = (
            etapas[st.session_state.etapa_atual - 1]
            if st.session_state.etapa_atual > 0
            else "Cadastro Inicial"
        )

        texto_detalhes = ""
        if etapa_nome == "Vistoria Concluída":
            if observacoes_vistoria:
                texto_detalhes += f"\n\n📌 *Vistoria:* {observacoes_vistoria}"
            if servicos_acertados:
                texto_detalhes += f"\n🛠️ *Serviços Acertados:* {servicos_acertados}"

        elif st.session_state.etapa_atual == len(etapas):
            if observacoes_finais:
                texto_detalhes += (
                    f"\n\n📝 *Observações Finais:* {observacoes_finais}"
                )
            if valor_final > 0:
                texto_detalhes += f"\n💰 *Valor Total:* R$ {valor_final:.2f}"
            if chave_pix:
                texto_detalhes += f"\n🔑 *Chave Pix:* {chave_pix}"

            texto_detalhes += (
                "\n\n✨ *\"Cuidamos hoje do bem que um dia foi seu maior sonho, "
                "porque aquilo que conquistamos merece ser preservado nos mínimos detalhes.\"*"
            )

        cabecalho_empresa = (
            f"*{nome_estabelecimento}*\n" if nome_estabelecimento else ""
        )

        mensagem = (
            f"{cabecalho_empresa}"
            f"Olá {proprietario}! 👋\n\n"
            f"Atualização sobre o seu veículo *{veiculo}* ({cor} - {ano}):\n"
            f"Status: *{etapa_nome}*{texto_detalhes}\n\n"
            f"Qualquer dúvida, estamos à disposição!"
        )

        link_wa = gerar_link_whatsapp(telefone, mensagem)

        st.markdown(
            f'<a href="{link_wa}" target="_blank">'
            f'<button style="background-color:#25D366; color:white; border:none; padding:12px 24px; border-radius:8px; cursor:pointer; font-weight:bold; font-size:16px;">'
            f"Enviar Status via WhatsApp 🚀"
            f"</button></a>",
            unsafe_allow_html=True,
        )

    def gerar_pdf():
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
            alignment=0,
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

        empresa_txt = (
            nome_estabelecimento
            if nome_estabelecimento
            else "Estética Automotiva"
        )

        header_paragraphs = [Paragraph(f"<b>{empresa_txt}</b>", title_style)]

        if endereco_empresa:
            header_paragraphs.append(
                Paragraph(
                    f"<b>Endereço:</b> {endereco_empresa}", sub_info_style
                )
            )
        if telefone_empresa:
            header_paragraphs.append(
                Paragraph(
                    f"<b>Telefone:</b> {telefone_empresa}", sub_info_style
                )
            )
        if responsavel_empresa:
            header_paragraphs.append(
                Paragraph(
                    f"<b>Responsável:</b> {responsavel_empresa}",
                    sub_info_style,
                )
            )

        if logo_empresa:
            img_logo = Image.open(logo_empresa)
            img_io_logo = io.BytesIO()
            img_logo.convert("RGB").save(img_io_logo, format="JPEG", quality=85)
            img_io_logo.seek(0)
            rl_logo = RLImage(img_io_logo, width=110, height=70)

            tabela_header = Table(
                [[rl_logo, header_paragraphs]], colWidths=[120, 420]
            )
            tabela_header.setStyle(
                TableStyle([
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (0, 0), (0, 0), "LEFT"),
                    ("ALIGN", (1, 0), (1, 0), "LEFT"),
                    ("PADDING", (0, 0), (-1, -1), 0),
                ])
            )
            story.append(tabela_header)
        else:
            for p in header_paragraphs:
                story.append(p)

        story.append(Spacer(1, 15))

        dados_veiculo = [
            [
                Paragraph("<b>Proprietário(a):</b>", body_style),
                Paragraph(proprietario or "-", body_style),
                Paragraph("<b>Telefone:</b>", body_style),
                Paragraph(telefone or "-", body_style),
            ],
            [
                Paragraph("<b>Veículo:</b>", body_style),
                Paragraph(veiculo or "-", body_style),
                Paragraph("<b>Cor / Ano:</b>", body_style),
                Paragraph(f"{cor or '-'} / {ano or '-'}", body_style),
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

        if servicos_acertados:
            story.append(Paragraph("Serviços Acertados", subtitle_style))
            story.append(Paragraph(servicos_acertados, body_style))
            story.append(Spacer(1, 10))

        if observacoes_vistoria:
            story.append(Paragraph("Observações da Vistoria", subtitle_style))
            story.append(Paragraph(observacoes_vistoria, body_style))
            story.append(Spacer(1, 10))

        if observacoes_finais or valor_final > 0 or chave_pix:
            story.append(Paragraph("Finalização do Serviço", subtitle_style))
            if observacoes_finais:
                story.append(
                    Paragraph(
                        f"<b>Observações Finais:</b> {observacoes_finais}",
                        body_style,
                    )
                )
            if valor_final > 0:
                story.append(
                    Paragraph(
                        f"<b>Valor Total do Serviço:</b> R$ {valor_final:.2f}",
                        body_style,
                    )
                )
            if chave_pix:
                story.append(
                    Paragraph(
                        f"<b>Chave Pix para Pagamento:</b> {chave_pix}",
                        body_style,
                    )
                )
            story.append(Spacer(1, 10))

        def adicionar_fotos_ao_pdf(lista_arquivos, titulo_secao):
            if not lista_arquivos:
                return
            story.append(Paragraph(titulo_secao, subtitle_style))
            imgs_row = []
            tabela_fotos = []
            for file in lista_arquivos:
                img = Image.open(file)
                img_io = io.BytesIO()
                img.convert("RGB").save(img_io, format="JPEG", quality=75)
                img_io.seek(0)
                rl_img = RLImage(img_io, width=160, height=120)
                imgs_row.append(rl_img)

                if len(imgs_row) == 3:
                    tabela_fotos.append(imgs_row)
                    imgs_row = []
            if imgs_row:
                while len(imgs_row) < 3:
                    imgs_row.append("")
                tabela_fotos.append(imgs_row)

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

        adicionar_fotos_ao_pdf(fotos_vistoria, "Fotos da Vistoria Inicial")
        adicionar_fotos_ao_pdf(
            fotos_finalizacao, "Fotos do Veículo Finalizado"
        )

        doc.build(story)
        buffer.seek(0)
        return buffer

    st.divider()

    st.subheader("📄 Salvar e Gerar Relatório")
    col_pdf1, col_pdf2 = st.columns(2)

    with col_pdf1:
        if st.button("📊 Gerar Relatório em PDF"):
            pdf_bytes = gerar_pdf()
            nome_arquivo = f"relatorio_{veiculo or 'veiculo'}.pdf"
            st.download_button(
                label="📥 Baixar PDF",
                data=pdf_bytes,
                file_name=nome_arquivo,
                mime="application/pdf",
            )

    with col_pdf2:
        if st.button("💾 Salvar Atendimento no Histórico"):
            if veiculo or proprietario:
                dados_atendimento = {
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
                    "servicos_acertados": servicos_acertados,
                    "observacoes_finais": observacoes_finais,
                    "valor_final": valor_final,
                    "chave_pix": chave_pix,
                }
                salvar_atendimento_db(
                    dados_atendimento, fotos_vistoria, fotos_finalizacao
                )
                st.success("✅ Atendimento registrado no histórico com sucesso!")
            else:
                st.error("⚠️ Preencha pelo menos o Veículo ou Proprietário(a).")

    st.divider()
    if st.button("🔄 Iniciar Novo Veículo"):
        st.session_state.etapa_atual = 0
        st.rerun()

# ==========================================
# ABA 2: HISTÓRICO DE CLIENTES
# ==========================================
elif opcao_menu == "📂 Histórico de Clientes":
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
            ) = reg

            with st.expander(
                f"🚗 {veic or 'Veículo'} - {prop or 'Cliente'} ({data_atend})"
            ):
                col_h1, col_h2 = st.columns(2)
                with col_h1:
                    st.write(f"**Proprietário(a):** {prop or '-'}")
                    st.write(f"**Telefone:** {tel_cli or '-'}")
                    st.write(f"**Veículo:** {veic or '-'}")
                    st.write(f"**Cor / Ano:** {cor_v or '-'} / {ano_v or '-'}")
                with col_h2:
                    st.write(f"**Valor Total:** R$ {val_fin:.2f}")
                    st.write(f"**Chave Pix:** {pix or '-'}")
                    st.write(f"**Responsável:** {resp_est or '-'}")

                if serv_acert:
                    st.write(f"**Serviços Executados:**\n{serv_acert}")
                if obs_vist:
                    st.write(f"**Observações de Vistoria:**\n{obs_vist}")
                if obs_fin:
                    st.write(f"**Observações Finais:**\n{obs_fin}")

                # Exibição de Fotos da Vistoria do Histórico
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

                # Exibição de Fotos da Finalização do Histórico
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
    else:
        st.info("Nenhum histórico de atendimento encontrado.")
