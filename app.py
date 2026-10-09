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
with col_emp2:
    logo_empresa = st.file_uploader(
        "Logo da Empresa (para o PDF):",
        type=["png", "jpg", "jpeg"],
        key="logo",
    )

col1, col2 = st.columns(2)
with col1:
    veiculo = st.text_input("Veículo:")
    cor = st.text_input("Cor:")
with col2:
    ano = st.text_input("Ano:")
    proprietario = st.text_input("Proprietário:")

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
fotos_finalizacao = []

if st.session_state.etapa_atual == len(etapas):
    st.divider()
    st.subheader("✨ Finalização e Entrega")

    col_v1, col_v2 = st.columns(2)
    with col_v1:
        valor_final = st.number_input(
            "💰 Valor Total dos Serviços (R$):",
            min_value=0.0,
            format="%.2f",
            step=10.0,
        )
    with col_v2:
        observacoes_finais = st.text_area(
            "📝 Observações Finais / Recomendações:",
            placeholder="Ex: Não lavar o veículo pelas próximas 48h devido à cura do vitrificador.",
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

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Heading1"],
        fontSize=18,
        leading=22,
        alignment=0,
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

    empresa_txt = (
        nome_estabelecimento
        if nome_estabelecimento
        else "Estética Automotiva"
    )

    header_text = [
        Paragraph(f"<b>{empresa_txt}</b>", title_style),
        Paragraph(
            "Relatório de Serviço e Vistoria",
            ParagraphStyle(
                "Sub",
                parent=
