import urllib.parse
import streamlit as st

st.set_page_config(page_title="Estética Automotiva - Gestão", page_icon="🚗")

st.title("🚗 Controle de Serviços - Estética Automotiva")

# --- DADOS DO VEÍCULO ---
st.subheader("📋 Dados do Veículo")

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

# --- CAMPO DE OBSERVAÇÕES ---
observacoes = st.text_area(
    "📝 Observações (Avarias, detalhes de pintura, solicitações especiais):",
    placeholder="Ex: Risco no pára-choque dianteiro lado direito, banco de couro com pequena mancha.",
)

# --- PASTA DE FOTOS DA VISTORIA ---
st.subheader("📸 Fotos da Vistoria")
fotos_vistoria = st.file_uploader(
    "Anexe ou tire fotos das avarias/estado inicial do veículo:",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=True,
)

if fotos_vistoria:
    st.write(f"**{len(fotos_vistoria)} foto(s) carregada(s):**")
    cols = st.columns(3)
    for index, foto in enumerate(fotos_vistoria):
        with cols[index % 3]:
            st.image(
                foto,
                caption=f"Foto {index + 1}",
                use_container_width=True,
            )

st.divider()

# --- ETAPAS DO PROCESSO ---
st.subheader("⚙️ Acompanhamento do Processo")

etapas = [
    "Vistoria Concluída",
    "Início da Lavagem Externa",
    "Fim da Lavagem Externa",
    "Início da Limpeza Interna",
    "Fim da Limpeza Interna",
    "Aplicação de Cerâmica / Proteção",
    "Fase de Finalização / Pronto para Retirada",
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

# --- NOTIFICAÇÃO VIA WHATSAPP ---
if telefone and modelo:
    st.divider()
    st.subheader("📲 Notificar Cliente")

    etapa_nome = (
        etapas[st.session_state.etapa_atual - 1]
        if st.session_state.etapa_atual > 0
        else "Cadastro Inicial"
    )

    texto_obs = f"\n📌 *Observações:* {observacoes}" if observacoes else ""

    mensagem = (
        f"Olá {proprietario}! 👋\n\n"
        f"Atualização sobre o seu *{modelo} ({cor})*:\n"
        f"Status atual: *{etapa_nome}*{texto_obs}\n\n"
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

# Botão para limpar e iniciar novo veículo
st.divider()
if st.button("🔄 Iniciar Novo Veículo"):
    st.session_state.etapa_atual = 0
    st.rerun()
