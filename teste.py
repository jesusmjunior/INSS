import streamlit as st
import pandas as pd
import re
from io import StringIO

# ===================== CONFIGURAÇÃO DA PÁGINA =====================
st.set_page_config(page_title="Jesus e INSS | Sistema Completo", layout="wide")

# Título do App
st.title("📄 JESUS e INSS - Extrator CNIS & Carta Benefício")
st.write("**Recepção de arquivos TXT bagunçados ➔ Organização ➔ Visualização das tabelas completas ➔ Exportação CSV.**")

# ===================== ABA DE LOGIN =====================
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

# ===================== FUNÇÕES DE LEITURA E ESTRUTURAÇÃO =====================

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
            data.append({'Competência': competencia, 'Remuneração': remuneracao, 'Origem': 'CNIS'})
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
                'Observação': observacao,
                'Origem': 'Carta Benefício'
            })
    return pd.DataFrame(data)


def exportar_csv(df, nome_base):
    df.to_csv(f"{nome_base}.csv", index=False)
    return f"{nome_base}.csv"

# ===================== LAYOUT COM TABELAS =====================

st.subheader("📊 Tabelas Organizacionais")

col1, col2 = st.columns(2)

with col1:
    uploaded_cnis_txt = st.file_uploader("🔽 Upload do arquivo CNIS (TXT):", type="txt", key="cnis_txt")

with col2:
    uploaded_carta_txt = st.file_uploader("🔽 Upload do arquivo Carta Benefício (TXT):", type="txt", key="carta_txt")

# ===================== PROCESSAMENTO DOS DADOS =====================

if uploaded_cnis_txt and uploaded_carta_txt:
    # Processando CNIS
    texto_cnis = ler_texto(uploaded_cnis_txt)
    df_cnis = estrutura_cnis(texto_cnis)

    # Processando Carta Benefício
    texto_carta = ler_texto(uploaded_carta_txt)
    df_carta = estrutura_carta(texto_carta)

    # Exportando CNIS e Carta para CSV
    file_cnis = exportar_csv(df_cnis, "Extrato_CNIS_Organizado")
    file_carta = exportar_csv(df_carta, "Carta_Beneficio_Organizada")
    st.download_button("⬇️ Baixar CNIS CSV", data=open(file_cnis, 'rb'), file_name=file_cnis, mime='text/csv')
    st.download_button("⬇️ Baixar Carta CSV", data=open(file_carta, 'rb'), file_name=file_carta, mime='text/csv')

    # ===================== SALÁRIOS DESCONSIDERADOS =====================

    # CNIS - Filtrando os salários desconsiderados
    df_desconsiderados_cnis = df_cnis[df_cnis['Remuneração'].astype(float) < 1000]  # Exemplo de filtro
    df_desconsiderados_carta = df_carta[df_carta['Salário'].astype(float) < 1000]  # Exemplo de filtro

    # Agrupando os dados de salários desconsiderados
    df_desconsiderados = pd.concat([df_desconsiderados_cnis, df_desconsiderados_carta], ignore_index=True)
    file_output_desconsiderados = exportar_csv(df_desconsiderados, "Salarios_Desconsiderados")

    # Exibindo os salários desconsiderados
    st.subheader("📊 Salários Desconsiderados (CNIS e Carta)")
    st.dataframe(df_desconsiderados, use_container_width=True)
    st.download_button("⬇️ Baixar Salários Desconsiderados CSV", data=open(file_output_desconsiderados, 'rb'), file_name=file_output_desconsiderados, mime='text/csv')

    # ===================== CAIXA DE DADOS ALIENÍGENAS =====================

    alienigenas_input = st.text_area("Inserir dados alienígenas para cálculo (formato livre):")
    if st.button("Formatar Dados Alienígenas"):
        # Processamento para formatar os dados alienígenas (exemplo simples)
        alienigenas_formatted = alienigenas_input.replace(",", ".").replace("\n", ",").split(',')
        df_alienigenas = pd.DataFrame({'Dados Alienígenas': alienigenas_formatted})
        st.write("### Dados Alienígenas Formatados:")
        st.dataframe(df_alienigenas)

        # Gerar CSV para download
        file_output_alienigenas = exportar_csv(df_alienigenas, "Alienigenas_Formatados")
        st.download_button("⬇️ Baixar Alienígenas CSV", data=open(file_output_alienigenas, 'rb'), file_name=file_output_alienigenas, mime='text/csv')

else:
    st.info("🔔 Faça upload dos arquivos CNIS e Carta Benefício para iniciar o processamento.")
