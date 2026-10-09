import io
import urllib.parse
from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Image as RLImage, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
import streamlit as st

st.set_page_config(page_title="Estética Automotiva - Gestão", page_icon="🚗")

st.title("🚗 Controle de Serviços - Estética Automotiva")

# --- DADOS DO ESTABELECIMENTO E VEÍCULO ---
st.subheader("📋 Dados Gerais")

nome_estabelecimento = st.text_input(
    "Nome do Estabelecimento:",
    placeholder="Digite o nome da sua estética automotiva",
)

col1, col2 = st.columns(2)
with col1:
    modelo = st.text_input("Modelo:")
    cor = st.text_input("Cor:")
with col2:
    ano = st.text_input("Ano:")
    proprietario = st.text_input("Proprietário:")

telefone = st.text_input(
    "Telefone do Cliente (DDD + Número, ex: 31999998888):"
)

# --- CAMPO DE OBSERVAÇÕES / VISTORIA ---
observacoes = st.text_area(
    "📝 Observações da Vistoria (Avarias, detalhes de pintura, solicitações especiais):",
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

# --- FOTOS APÓS FINALIZAÇÃO ---
fotos_finalizacao = []
if st.session_state.etapa_atual == len(etapas):
    st.divider()
    st.subheader("✨ Fotos do Veículo Finalizado (Entrega)")
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
if telefone and modelo:
    st.divider()
    st.subheader("📲 Notificar Cliente")

    etapa_nome = (
        etapas[st.session_state.etapa_atual - 1]
        if st.session_state.etapa_atual > 0
        else "Cadastro Inicial"
    )

    texto_obs = ""
    if etapa_nome == "Vistoria Concluída" and observacoes:
        texto_obs = f"\n\n📌 *Dados da Vistoria:* {observacoes}"

    cabecalho_empresa = (
        f"*{nome_estabelecimento}*\n" if nome_estabelecimento else ""
    )

    mensagem = (
        f"{cabecalho_empresa}"
        f"Olá {proprietario}! 👋\n\n"
        f"Atualização sobre o seu veículo *{modelo}* ({cor} - {ano}):\n"
        f"Status: *{etapa_nome}*{texto_obs}\n\n"
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
        buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
    )
    story = []
    styles = getSampleStyleSheet()

    # Estilos
    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Heading1"],
        fontSize=18,
        leading=22,
        alignment=1,
        textColor=colors.HexColor("#1A365D"),
    )
    subtitle_style = ParagraphStyle(
        "SubTitleStyle",
        parent=styles["Heading2"],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#2B6CB0"),
        spaceBefore=10,
        spaceAfter=5,
    )
    body_style = styles["BodyText"]

    # Cabeçalho
    empresa_txt = nome_estabelecimento if nome_estabelecimento else "Estética Automotiva"
    story.append(Paragraph(f"<b>{empresa_txt}</b>", title_style))
    story.append(Paragraph("Relatório de Serviço e Vistoria", ParagraphStyle("Sub", parent=title_style, fontSize=12, textColor=colors.gray)))
    story.append(Spacer(1, 15))

    # Tabela de Dados Gerais
    dados_veiculo = [
        [Paragraph("<b>Proprietário:</b>", body_style), Paragraph(proprietario or "-", body_style), Paragraph("<b>Telefone:</b>", body_style), Paragraph(telefone or "-", body_style)],
        [Paragraph("<b>Modelo:</b>", body_style), Paragraph(modelo or "-", body_style), Paragraph("<b>Cor / Ano:</b>", body_style), Paragraph(f"{cor or '-'} / {ano or '-'}", body_style)],
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
    story.append(Spacer(1, 15))

    # Observações
    if observacoes:
        story.append(Paragraph("Observações da Vistoria", subtitle_style))
        story.append(Paragraph(observacoes, body_style))
        story.append(Spacer(1, 10))

    # Função auxiliar para processar e redimensionar imagens no PDF
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

    # Adiciona fotos no PDF
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
    nome_arquivo = f"relatorio_{modelo or 'veiculo'}.pdf"
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
