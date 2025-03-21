import streamlit as st
import pandas as pd
import numpy as np
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

# ===================== FUNÇÕES COMUNS =====================
def exportar_csv(df, nome_base):
    df.to_csv(f"{nome_base}.csv", index=False)
    return f"{nome_base}.csv"

# ===================== ABA 1: DASHBOARD PREVIDENCIÁRIO =====================
if aba == "Dashboard Previdenciário":
    st.title("📑 Dashboard Previdenciário Profissional")

    def organizar_cnis(file):
        df = pd.read_csv(file, delimiter=';', encoding='utf-8')
        df = df.iloc[:,0].str.split(',', expand=True)
        df.columns = ['Seq', 'Competência', 'Remuneração', 'Ano']
        df['Remuneração'] = pd.to_numeric(df['Remuneração'], errors='coerce')
        df = df[df['Remuneração'] < 50000]
        return df

    def organizar_desconsiderados(file):
        df = pd.read_csv(file, delimiter=';', encoding='utf-8')
        df = df.iloc[:,0].str.split(',', expand=True)
        df.columns = ['Seq', 'Seq.', 'Data', 'Salário', 'Índice', 'Sal. Corrigido', 'Observação', 'Ano', 'Duplicado']
        df['Sal. Corrigido'] = pd.to_numeric(df['Sal. Corrigido'], errors='coerce')
        return df

    def fator_previdenciario(Tc, Es, Id, a=0.31):
        fator = (Tc * a / Es) * (1 + ((Id + Tc * a) / 100))
        return round(fator, 4)

    def formatar_moeda(valor):
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    st.sidebar.header("🔽 Upload dos Arquivos")
    cnis_file = st.sidebar.file_uploader("Upload - CNIS", type=["csv"])
    carta_file = st.sidebar.file_uploader("Upload - Carta", type=["csv"])
    desconsid_file = st.sidebar.file_uploader("Upload - Desconsiderados", type=["csv"])

    aba_dash = st.sidebar.radio("Navegação", ["Dashboard", "Gráficos", "Explicação", "Simulador", "Relatório"])

    if cnis_file and carta_file and desconsid_file:
        df_cnis = organizar_cnis(cnis_file)
        df_desconsiderados = organizar_desconsiderados(desconsid_file)

        # Desconsiderados da carta de concessão
        df_descons_carta = df_desconsiderados[df_desconsiderados['Observação'].str.contains("DESCONSIDERADO", na=False)]
        df_descons_carta['Origem'] = 'Carta'

        # Desconsiderados do CNIS: por padrão, vamos assumir que valores acima de 50000 são outliers/desconsiderados
        df_descons_cnis = df[df['Remuneração'] > 50000].copy() if 'Remuneração' in df_cnis.columns else pd.DataFrame()
        df_descons_cnis.columns = ['Seq', 'Competência', 'Remuneração', 'Ano']
        df_descons_cnis['Sal. Corrigido'] = np.nan
        df_descons_cnis['Origem'] = 'CNIS'

        # Unificar em um CSV de todos os salários desconsiderados
        df_descons_cnis = df_descons_cnis[['Competência', 'Remuneração', 'Origem']]
        df_descons_carta = df_descons_carta[['Data', 'Salário', 'Origem']].rename(columns={'Data': 'Competência', 'Salário': 'Remuneração'})

        df_total_descons = pd.concat([df_descons_cnis, df_descons_carta], ignore_index=True)
        exportar_csv(df_descons_carta, "Salarios_Desconsiderados_Carta")
        exportar_csv(df_descons_cnis, "Salarios_Desconsiderados_CNIS")
        exportar_csv(df_total_descons, "Salarios_Desconsiderados")

        st.success("Arquivos de salários desconsiderados exportados com sucesso!")

        # RESTANTE DA LÓGICA PERMANECE...

# ===================== ABA 2: EXTRATOR CNIS & CARTA =====================
elif aba == "Extrator CNIS & Carta Benefício":
    st.title("📄 JESUS e INSS - Extrator CNIS & Carta Benefício")
    st.write("**Recepção de arquivos TXT bagunçados ➔ Organização ➔ Visualização das tabelas completas ➔ Exportação CSV.**")

    col1, col2 = st.columns(2)
    with col1:
        uploaded_cnis_txt = st.file_uploader("🔽 Upload do arquivo CNIS (TXT):", type="txt", key="cnis_txt")
    with col2:
        uploaded_carta_txt = st.file_uploader("🔽 Upload do arquivo Carta Benefício (TXT):", type="txt", key="carta_txt")

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
