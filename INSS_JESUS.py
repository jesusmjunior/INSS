import streamlit as st
import pandas as pd
import re
from io import StringIO

# ===================== CONFIGURAÇÃO DA PÁGINA =====================
st.set_page_config(page_title="Jesus e INSS | Sistema Completo", layout="wide")

# ===================== LOGIN ABA 1 =====================
def login():
    if 'login_visible' not in st.session_state:
        st.session_state.login_visible = True

    if st.session_state.login_visible:
        with st.expander("🔐 Área Protegida - Login Obrigatório", expanded=True):
            user = st.text_input("Usuário (Email)")
            password = st.text_input("Senha", type="password")

            usuarios = {
                "jesusmjunior2021@gmail.com": "jr010507",
                "joliveiramaccf@gmail.com": "cgti@383679"
            }

            if (user in usuarios and password == usuarios[user]):
                st.success("Login efetuado com sucesso ✅")
                if st.button("Ocultar Login"):
                    st.session_state.login_visible = False
                return True
            else:
                if user and password:
                    st.error("Usuário ou senha incorretos ❌")
                st.stop()
    else:
        st.info("Login ocultado. Clique abaixo para reexibir.")
        if st.button("Mostrar Login"):
            st.session_state.login_visible = True
            st.experimental_rerun()

# ===================== EXECUTA LOGIN =====================
login()

# ===================== SELEÇÃO DE ABA =====================
aba = st.sidebar.radio("Selecione a Aba:", ["Dashboard Previdenciário", "Extrator CNIS & Carta Benefício"])

# ===================== ABA 1: DASHBOARD PREVIDENCIÁRIO =====================
if aba == "Dashboard Previdenciário":
    st.title("📑 Dashboard Previdenciário Profissional")
    st.info("Conteúdo do Dashboard Previdenciário Profissional carregado com sucesso.")

# ===================== ABA 2: EXTRATOR CNIS & CARTA =====================
elif aba == "Extrator CNIS & Carta Benefício":

    # ===================== CONFIG PÁGINA DA SEGUNDA ABA =====================
    st.title("📄 JESUS e INSS - Extrator CNIS & Carta Benefício")
    st.write("**Recepção de arquivos TXT bagunçados ➔ Organização ➔ Visualização das tabelas completas ➔ Exportação CSV.**")

    # ===================== RECEPÇÃO DOS TXT =====================
    col1, col2 = st.columns(2)

    with col1:
        uploaded_cnis_txt = st.file_uploader("🔽 Upload do arquivo CNIS (TXT):", type="txt", key="cnis_txt")

    with col2:
        uploaded_carta_txt = st.file_uploader("🔽 Upload do arquivo Carta Benefício (TXT):", type="txt", key="carta_txt")

    # ===================== FUNÇÕES BASE =====================

    def ler_texto(uploaded_file):
        stringio = StringIO(uploaded_file.getvalue().decode("utf-8", errors='ignore'))
        texto = stringio.read()
        return texto

    def estrutura_cnis(texto):
        linhas = texto.split('\n')
        data = []
        for line in linhas:
            match = re.search(r"(\d{2}/\d{4})\s+([0-9.]+,[0-9]{2})", line)
            if match:
                competencia = match.group(1)
                remuneracao = match.group(2).replace('.', '').replace(',', '.')
                data.append({'Competência': competencia, 'Remuneração': remuneracao})
        return pd.DataFrame(data)

    def estrutura_carta(texto):
        linhas = texto.split('\n')
        data = []
        for line in linhas:
            match = re.match(r"^(\d{3})\s+(\d{2}/\d{4})\s+([0-9.,]+)\s+([0-9.,]+)\s+([0-9.,]+)(\s+.*)?", line)
            if match:
                seq = match.group(1)
                data_col = match.group(2)
                salario = match.group(3).replace('.', '').replace(',', '.')
                indice = match.group(4).replace(',', '.')
                sal_corrigido = match.group(5).replace('.', '').replace(',', '.')
                observacao = match.group(6).strip() if match.group(6) else ""
                data.append({
                    'Seq.': seq,
                    'Data': data_col,
                    'Salário': salario,
                    'Índice': indice,
                    'Sal. Corrigido': sal_corrigido,
                    'Observação': observacao
                })
        return pd.DataFrame(data)

    def exportar_csv(df, nome_base):
        df.to_csv(f"{nome_base}.csv", index=False)
        return f"{nome_base}.csv"

    # ===================== LAYOUT COM TABELAS =====================

    st.subheader("📊 Tabelas Organizacionais")

    col3, col4 = st.columns(2)

    with col3:
        st.markdown("### 📄 Extrato CNIS")
        if uploaded_cnis_txt is not None:
            texto_txt = ler_texto(uploaded_cnis_txt)
            df_cnis = estrutura_cnis(texto_txt)
            if not df_cnis.empty:
                st.dataframe(df_cnis, use_container_width=True)
                file_output = exportar_csv(df_cnis, "Extrato_CNIS_Organizado")
                st.download_button("⬇️ Baixar CNIS CSV", data=open(file_output, 'rb'), file_name=file_output, mime='text/csv')
            else:
                st.warning("⚠️ Nenhum dado CNIS identificado.")
        else:
            st.info("Faça upload do TXT CNIS para visualizar.")

    with col4:
        st.markdown("### 📄 Carta Benefício")
        if uploaded_carta_txt is not None:
            texto_txt = ler_texto(uploaded_carta_txt)
            df_carta = estrutura_carta(texto_txt)
            if not df_carta.empty:
                st.dataframe(df_carta, use_container_width=True)
                file_output = exportar_csv(df_carta, "Carta_Beneficio_Organizada")
                st.download_button("⬇️ Baixar Carta CSV", data=open(file_output, 'rb'), file_name=file_output, mime='text/csv')
            else:
                st.warning("⚠️ Nenhum dado da Carta identificado.")
        else:
            st.info("Faça upload do TXT da Carta para visualizar.")
