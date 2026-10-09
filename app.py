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
            st.image(
                foto,
                caption=f"Vistoria {index + 1}",
                use_container_width=True,
            )

# --- SERVIÇOS CONTRATADOS ---
st.subheader("🛠️ Serviços Acertados com o Cliente")
servicos_acertados = st.text_area(
    "Descreva os serviços a serem executados:",
    placeholder="Ex: Lavagem detalhada, Higienização interna, Vitrificação de pintura.",
)

st.divider()

# --- ETAPAS DO PROCESSO ---
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

# --- CAMPOS APÓS FINALIZAÇÃO (ÚLTIMA ETAPA) ---
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

# --- NOTIFICAÇÃO VIA WHATSAPP ---
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
            texto_detalhes += f"\n\n📝 *Observações Finais:* {observacoes_finais}"
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


# --- GERADOR DE PDF ---
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
        nome_estabelecimento if nome_estabelecimento else "Estética Automotiva"
    )

    header_paragraphs = [Paragraph(f"<b>{empresa_txt}</b>", title_style)]

    if endereco_empresa:
        header_paragraphs.append(
            Paragraph(f"<b>Endereço:</b> {endereco_empresa}", sub_info_style)
        )
    if telefone_empresa:
        header_paragraphs.append(
            Paragraph(f"<b>Telefone:</b> {telefone_empresa}", sub_info_style)
        )
    if responsavel_empresa:
        header_paragraphs.append(
            Paragraph(f"<b>Responsável:</b> {responsavel_empresa}", sub_info_style)
        )

    if logo_empresa:
        img_logo = Image.open(logo_empresa)
        img_io_logo = io.BytesIO()
        img_logo.convert("RGB").save(img_io_logo, format="JPEG", quality=85)
        img_io_logo.seek(0)
        rl_logo = RLImage(img_io_logo, width=110, height=70)

        tabela_header = Table([[rl_logo, header_paragraphs]], colWidths=[120, 420])
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
    adicionar_fotos_ao_pdf(fotos_finalizacao, "Fotos do Veículo Finalizado")

    doc.build(story)
    buffer.seek(0)
    return buffer


st.divider()

# Botão de Download do PDF
st.subheader("📄 Relatório do Serviço")
if st.button("📊 Gerar Relatório em PDF"):
    pdf_bytes = gerar_pdf()
    nome_arquivo = f"relatorio_{veiculo or 'veiculo'}.pdf"
    st.download_button(
        label="📥 Baixar PDF",
        data=pdf_bytes,
        file_name=nome_arquivo,
        mime="application/pdf",
    )

# Botão para limpar e iniciar novo veículo
st.divider()
if st.button("🔄 Iniciar Novo Veículo"):
    st.session_state.etapa_atual = 0
    st.rerun()
