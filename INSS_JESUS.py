import streamlit as st
import pandas as pd
import numpy as np
import json
import re
from io import StringIO

# ================================
# CONFIGURAÇÃO INICIAL PRIMEIRA LINHA
# ================================
st.set_page_config(page_title="Dashboard Previdenciário Profissional", layout="wide")

# ================================
# LOGIN SIMPLES
# ================================
def login():
    st.title("🔐 Área Protegida - Login Obrigatório")
    user = st.text_input("Usuário (Email)")
    password = st.text_input("Senha", type="password")

    if user == "jesusmjunior2021@gmail.com" and password == "jr010507":
        st.success("Login efetuado com sucesso ✅")
        return True
    else:
        if user and password:
            st.error("Usuário ou senha incorretos ❌")
        st.stop()  # Para bloquear acesso caso não logado

# ================================
# EXECUTA LOGIN
# ================================
login()

# ================================
# FUNÇÕES UTILITÁRIAS
# ================================
def organizar_cnis(file):
    df = pd.read_csv(file, delimiter=';', encoding='utf-8')
    df = df.iloc[:,0].str.split(',', expand=True)
    df.columns = ['Seq', 'Competência', 'Remuneração', 'Ano']
    df['Remuneração'] = pd.to_numeric(df['Remuneração'], errors='coerce')
    df = df[df['Remuneração'] < 50000]  # Remove discrepantes - fuzzy
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

# ================================
# UPLOAD
# ================================
aba = st.sidebar.radio("Navegação",["Extrator"])
st.sidebar.header("🔽 Upload dos Arquivos")
cnis_file = st.sidebar.file_uploader("Upload - CNIS", type=["csv"])
carta_file = st.sidebar.file_uploader("Upload - Carta", type=["csv"])
desconsid_file = st.sidebar.file_uploader("Upload - Desconsiderados", type=["csv"])

aba = st.sidebar.radio("Navegação", ["Dashboard", "Gráficos", "Explicação", "Simulador", "Relatório", "Atualização Monetária"])

# ================================
# PROCESSAMENTO PRINCIPAL
# ================================
if cnis_file and carta_file and desconsid_file:

    df_cnis = organizar_cnis(cnis_file)
    df_desconsiderados = organizar_desconsiderados(desconsid_file)

    # 80% MAIORES SALÁRIOS
    df_cnis_sorted = df_cnis.sort_values(by='Remuneração', ascending=False)
    qtd_80 = int(len(df_cnis_sorted) * 0.8)
    df_top80 = df_cnis_sorted.head(qtd_80)
    df_bottom10 = df_cnis_sorted.tail(len(df_cnis_sorted) - qtd_80)

    # DESCONSIDERADOS VANTAJOSOS
    min_80 = df_top80['Remuneração'].min()
    df_vantajosos = df_desconsiderados[df_desconsiderados['Sal. Corrigido'] > min_80]

    # PARÂMETROS DEFAULT
    Tc_default, Es_default, Id_default, a_default = 38, 21.8, 60, 0.31
    media_salarios = df_top80['Remuneração'].mean()
    fator = fator_previdenciario(Tc_default, Es_default, Id_default, a_default)
    salario_beneficio = round(media_salarios * fator, 2)

    # FORMATAÇÃO MOEDA
    df_top80['Remuneração'] = df_top80['Remuneração'].apply(formatar_moeda)
    df_vantajosos['Sal. Corrigido'] = df_vantajosos['Sal. Corrigido'].apply(formatar_moeda)

    # ================================
    # EXTRATOR 
    # ================================
    if aba == "Extrator":
        st.title("📄 Extrator CNIS & Carta Benefício")
        st.write("Recepção de arquivos TXT bagunçados ➔ Organização ➔ Visualização das tabelas completas ➔ Exportação CSV.")

        col1, col2 = st.columns(2)

        with col1:
            uploaded_cnis_txt = st.file_uploader("🔽 Upload do arquivo CNIS (TXT):", type="txt", key="cnis_txt")

        with col2:
            uploaded_carta_txt = st.file_uploader("🔽 Upload do arquivo Carta Benefício (TXT):", type="txt", key="carta_txt")

        # Funções de Leitura e Estruturação
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

        # Processamento e Exibição
        if uploaded_cnis_txt and uploaded_carta_txt:
            texto_cnis = ler_texto(uploaded_cnis_txt)
            df_cnis = estrutura_cnis(texto_cnis)

            texto_carta = ler_texto(uploaded_carta_txt)
            df_carta = estrutura_carta(texto_carta)

            file_cnis = exportar_csv(df_cnis, "Extrato_CNIS_Organizado")
            file_carta = exportar_csv(df_carta, "Carta_Beneficio_Organizada")
            st.download_button("⬇️ Baixar CNIS CSV", data=open(file_cnis, 'rb'), file_name=file_cnis, mime='text/csv')
            st.download_button("⬇️ Baixar Carta CSV", data=open(file_carta, 'rb'), file_name=file_carta, mime='text/csv')

            # Salários Desconsiderados
            df_desconsiderados_cnis = df_cnis[df_cnis['Remuneração'].astype(float) < 1000]
            df_desconsiderados_carta = df_carta[df_carta['Salário'].astype(float) < 1000]
            df_desconsiderados = pd.concat([df_desconsiderados_cnis, df_desconsiderados_carta], ignore_index=True)
            file_output_desconsiderados = exportar_csv(df_desconsiderados, "Salarios_Desconsiderados")
            st.download_button("⬇️ Baixar Salários Desconsiderados CSV", data=open(file_output_desconsiderados, 'rb'), file_name=file_output_desconsiderados, mime='text/csv')

        else:
            st.info("👆 Faça upload dos arquivos CNIS e Carta Benefício em TXT para iniciar.")

else:
    st.info("🔔 Faça upload dos 3 arquivos obrigatórios para liberar o dashboard.")

