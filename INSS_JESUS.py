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

# ===================== ABA 2: EXTRATOR CNIS & CARTA BENEFÍCIO =====================
if aba == "Extrator CNIS & Carta Benefício":
    st.title("📄 JESUS e INSS - Extrator CNIS & Carta Benefício")
    st.write("**Recepção de arquivos TXT bagunçados ➔ Organização ➔ Visualização das tabelas completas ➔ Exportação CSV.**")

    col1, col2 = st.columns(2)

    with col1:
        uploaded_cnis_txt = st.file_uploader("🔽 Upload do arquivo CNIS (TXT):", type="txt", key="cnis_txt")

    with col2:
        uploaded_carta_txt = st.file_uploader("🔽 Upload do arquivo Carta Benefício (TXT):", type="txt", key="carta_txt")

    st.subheader("📊 Tabelas Organizacionais")
    col3, col4 = st.columns(2)

    with col3:
        st.markdown("### 📄 Extrato CNIS")
        if uploaded_cnis_txt is not None:
            texto_cnis = ler_texto(uploaded_cnis_txt)
            df_cnis = estrutura_cnis(texto_cnis)
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
            texto_carta = ler_texto(uploaded_carta_txt)
            df_carta = estrutura_carta(texto_carta)
            if not df_carta.empty:
                st.dataframe(df_carta, use_container_width=True)
                file_output = exportar_csv(df_carta, "Carta_Beneficio_Organizada")
                st.download_button("⬇️ Baixar Carta CSV", data=open(file_output, 'rb'), file_name=file_output, mime='text/csv')
            else:
                st.warning("⚠️ Nenhum dado da Carta identificado.")
        else:
            st.info("Faça upload do TXT da Carta para visualizar.")

# ===================== ABA 3: INSERÇÃO MANUAL DE DADOS =====================
elif aba == "Inserção Manual de Dados":
    st.title("✍️ Inserção Manual de Salários (Modelo Carta de Concessão)")

    st.write("Preencha os campos conforme o modelo da carta de concessão. Os valores de Índice e Salário Corrigido serão calculados automaticamente.")

    with st.form("manual_form"):
        data = st.text_input("Data (MM/AAAA)", max_chars=7)
        salario = st.text_input("Salário Bruto (Ex: 4390.24)")
        observacao = st.text_input("Observação (Opcional)")

        submitted = st.form_submit_button("Adicionar Salário")

        if submitted:
            try:
                salario_float = float(salario.replace(",", "."))
                indice = 1.03  # valor simbólico
                sal_corrigido = round(salario_float * indice, 2)

                if 'dados_alienigenas' not in st.session_state:
                    st.session_state.dados_alienigenas = []

                st.session_state.dados_alienigenas.append({
                    "Seq.": len(st.session_state.dados_alienigenas) + 1,
                    "Data": data,
                    "Salário": salario_float,
                    "Índice": indice,
                    "Sal. Corrigido": sal_corrigido,
                    "Observação": observacao,
                    "Origem": "Manual"
                })
                st.success("Salário adicionado com sucesso!")
            except ValueError:
                st.error("Erro ao converter salário. Use formato numérico: 1234.56")

    if 'dados_alienigenas' in st.session_state and st.session_state.dados_alienigenas:
        st.subheader("📋 Salários Inseridos Manualmente")
        df_alien = pd.DataFrame(st.session_state.dados_alienigenas)
        st.dataframe(df_alien, use_container_width=True)

        file_output = exportar_csv(df_alien, "Salarios_Alienigenas_Manual")
        st.download_button("⬇️ Baixar CSV dos Inseridos", data=open(file_output, 'rb'), file_name=file_output, mime='text/csv')

# ===================== ABA FINAL: RELATÓRIO UNIFICADO =====================
elif aba == "Relatório Final Unificado":
    st.title("📦 Relatório Unificado - Salários Desconsiderados")

    df_list = []

    if 'dados_alienigenas' in st.session_state:
        df_alien = pd.DataFrame(st.session_state.dados_alienigenas)
        df_list.append(df_alien)

    if 'Salarios_Desconsid_Carta.csv' in st.session_state:
        df_carta = pd.read_csv('Salarios_Desconsid_Carta.csv')
        df_carta['Origem'] = "Carta"
        df_list.append(df_carta)

    if 'Salarios_Desconsid_CNIS.csv' in st.session_state:
        df_cnis = pd.read_csv('Salarios_Desconsid_CNIS.csv')
        df_cnis['Origem'] = "CNIS"
        df_list.append(df_cnis)

    if df_list:
        df_total = pd.concat(df_list, ignore_index=True)
        st.subheader("📑 Salários Desconsiderados Unificados")
        st.dataframe(df_total, use_container_width=True)

        file_total = exportar_csv(df_total, "Salarios_Desconsiderados_Unificado")
        st.download_button("⬇️ Baixar CSV Consolidado", data=open(file_total, 'rb'), file_name=file_total, mime='text/csv')
    else:
        st.warning("Nenhum dado carregado para consolidação. Volte às abas anteriores para subir os arquivos.")
