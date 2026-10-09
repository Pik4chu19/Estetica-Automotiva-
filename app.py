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
if
