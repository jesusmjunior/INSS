import streamlit as st
import pandas as pd
import numpy as np
import re
import json
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
aba = st.sidebar.radio("Selecione a Aba:", [
    "Dashboard Previdenciário",
    "Extrator CNIS & Carta Benefício",
    "Inserção Manual de Dados",
    "Relatório Final Unificado"
])

# ===================== FUNÇÕES COMUNS =====================
def exportar_csv(df, nome_base):
    df.to_csv(f"{nome_base}.csv", index=False)
    st.session_state[nome_base + '.csv'] = f"{nome_base}.csv"
    return f"{nome_base}.csv"

def ler_texto(uploaded_file):
    stringio = StringIO(uploaded_file.getvalue().decode("utf-8", errors='ignore'))
    return stringio.read()

def estrutura_cnis(texto):
    linhas = texto.split('\n')
    data = []
    for line in linhas:
        match = re.search(r"(\d{2}/\d{4})\s+([0-9.]+,[0-9]{2})", line)
        if match:
            competencia = match.group(1)
            remuneracao = match.group(2).replace('.', '').replace(',', '.')
            data.append({'Competência': competencia, 'Remuneração': float(remuneracao)})
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
                'Salário': float(salario),
                'Índice': float(indice),
                'Sal. Corrigido': float(sal_corrigido),
                'Observação': observacao
            })
    return pd.DataFrame(data)

def filtrar_salarios_desconsiderados_cnis(df_cnis):
    salario_minimo = 1000
    df_filtrado = df_cnis[df_cnis['Remuneração'] < salario_minimo].copy()
    df_filtrado['Origem'] = "CNIS"
    return df_filtrado

def filtrar_salarios_desconsiderados_carta(df_carta):
    df_filtrado = df_carta[df_carta['Observação'].str.upper().str.contains("DESCONSIDERADO")].copy()
    df_filtrado['Origem'] = "Carta"
    return df_filtrado

def combinar_salarios_desconsiderados(cnis, carta, manual):
    return pd.concat([cnis, carta, manual], ignore_index=True)

# ===================== ABA 2: Extrator CNIS & Carta Benefício =====================
if aba == "Extrator CNIS & Carta Benefício":
    st.title("📄 Extrator CNIS & Carta Benefício")

    col1, col2 = st.columns(2)

    with col1:
        uploaded_cnis_txt = st.file_uploader("Upload CNIS TXT", type="txt")
    with col2:
        uploaded_carta_txt = st.file_uploader("Upload Carta Benefício TXT", type="txt")

    if uploaded_cnis_txt:
        texto_cnis = ler_texto(uploaded_cnis_txt)
        df_cnis = estrutura_cnis(texto_cnis)
        st.dataframe(df_cnis)
        exportar_csv(df_cnis, "CNIS_EXTRAIDO")

    if uploaded_carta_txt:
        texto_carta = ler_texto(uploaded_carta_txt)
        df_carta = estrutura_carta(texto_carta)
        st.dataframe(df_carta)
        exportar_csv(df_carta, "CARTA_BENEFICIO_EXTRAIDA")

    if uploaded_cnis_txt and uploaded_carta_txt:
        df_desconsid_cnis = filtrar_salarios_desconsiderados_cnis(df_cnis)
        df_desconsid_carta = filtrar_salarios_desconsiderados_carta(df_carta)
        df_total_desconsid = combinar_salarios_desconsiderados(df_desconsid_cnis, df_desconsid_carta, pd.DataFrame())
        exportar_csv(df_total_desconsid, "SALARIOS_DESCONSIDERADOS_TOTAL")
        st.success("Arquivos desconsiderados extraídos com sucesso!")

# ===================== ABA 3: Inserção Manual de Dados =====================
elif aba == "Inserção Manual de Dados":
    st.title("✍️ Inserção Manual de Dados Alienígenas")
    st.info("Preencha os campos abaixo para adicionar salários manuais no padrão da carta de benefício")

    if "manual_data" not in st.session_state:
        st.session_state.manual_data = []

    with st.form("form_manual"):
        data = st.text_input("Data (MM/AAAA)", value="01/2020")
        salario = st.text_input("Salário", value="2000.00")
        indice = st.text_input("Índice", value="1.0")
        sal_corrigido = st.text_input("Salário Corrigido", value="2000.00")
        observacao = st.text_input("Observações", value="Manual")
        submitted = st.form_submit_button("Adicionar")

        if submitted:
            st
