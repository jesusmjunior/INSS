import streamlit as st
import pandas as pd
import numpy as np
import re
from io import StringIO

# ===================== CONFIGURAÇÃO DA PÁGINA =====================
st.set_page_config(page_title="Jesus e INSS | Sistema Completo", layout="wide")

# Título do App
st.title("📄 JESUS e INSS - Extrator CNIS & Carta Benefício")
st.write("**Recepção de arquivos TXT bagunçados ➔ Organização ➔ Visualização das tabelas completas ➔ Exportação CSV.**")

# ===================== FUNÇÕES DE LEITURA E ESTRUTURAÇÃO =====================

def ler_texto(uploaded_file):
    stringio = StringIO(uploaded_file.getvalue().decode("utf-8", errors='ignore'))
    texto = stringio.read()
    return texto

# Função para aplicar a lógica fuzzy para sanitização
def fuzzy_sanitization(value):
    try:
        # Tentar converter o valor para numérico
        sanitized_value = pd.to_numeric(value, errors='coerce')
        if pd.isna(sanitized_value):
            return 0  # Substituir valores não numéricos por 0
        return sanitized_value
    except Exception:
        return 0  # Se falhar, retorna 0 como valor padrão

def estrutura_cnis(texto):
    linhas = texto.split('\n')
    data = []
    for line in linhas:
        match = re.search(r"(\d{2}/\d{4})\s+([0-9.]+,[0-9]{2})", line)
        if match:
            competencia = match.group(1)
            remuneracao = match.group(2).replace('.', '').replace(',', '.')
            data.append({'Competência': competencia, 'Remuneração': remuneracao, 'Observação': 'Dados CNIS'})
    df = pd.DataFrame(data)
    
    # Sanitizando dados
    df['Remuneração'] = df['Remuneração'].apply(fuzzy_sanitization)
    
    return df

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
    df = pd.DataFrame(data)
    
    # Sanitizando dados
    df['Salário'] = df['Salário'].apply(fuzzy_sanitization)
    df['Sal. Corrigido'] = df['Sal. Corrigido'].apply(fuzzy_sanitization)
    
    return df

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

    # Exibindo as tabelas separadas
    st.subheader("📊 Tabela CNIS")
    st.dataframe(df_cnis, use_container_width=True)

    st.subheader("📊 Tabela Carta Benefício")
    st.dataframe(df_carta, use_container_width=True)

    # Botões de download para cada tabela separada
    file_cnis = exportar_csv(df_cnis, "Extrato_CNIS_Organizado")
    file_carta = exportar_csv(df_carta, "Carta_Beneficio_Organizada")

    st.download_button("⬇️ Baixar CNIS CSV", data=open(file_cnis, 'rb'), file_name=file_cnis, mime='text/csv')
    st.download_button("⬇️ Baixar Carta CSV", data=open(file_carta, 'rb'), file_name=file_carta, mime='text/csv')

    # ===================== SALÁRIOS DESCONSIDERADOS =====================

    # Filtrando os salários desconsiderados com base na Observação "DESCONSIDERADO"
    df_desconsiderados_carta = df_carta[df_carta['Observação'] == 'DESCONSIDERADO']

    # Criando a coluna "Ano" a partir da coluna "Data", caso não exista
    if 'Ano' not in df_desconsiderados_carta.columns:
        df_desconsiderados_carta['Ano'] = df_desconsiderados_carta['Data'].apply(lambda x: x.split('/')[1] if isinstance(x, str) else '')

    # Criando ou ajustando a coluna "Salário Corrigido"
    if 'Salário Corrigido' not in df_desconsiderados_carta.columns:
        df_desconsiderados_carta['Salário Corrigido'] = df_desconsiderados_carta['Sal. Corrigido']

    # Preenchendo valores vazios ou nulos nas colunas com valores padrão (se necessário)
    df_desconsiderados_carta = df_desconsiderados_carta.fillna("")

    # Reestruturando a tabela para o formato solicitado
    df_desconsiderados_carta = df_desconsiderados_carta[['Seq.', 'Data', 'Salário', 'Índice', 'Salário Corrigido', 'Observação', 'Ano', 'Salário Corrigido']]

    # Exportando os salários desconsiderados da Carta para CSV
    file_output_desconsiderados_carta = exportar_csv(df_desconsiderados_carta, "Salarios_Desconsiderados_Carta_Formatted")

    # Exibindo os salários desconsiderados da Carta Benefício
    st.subheader("📊 Salários Desconsiderados Carta Benefício")
    st.dataframe(df_desconsiderados_carta, use_container_width=True)
    st.download_button("⬇️ Baixar Salários Desconsiderados Carta CSV", data=open(file_output_desconsiderados_carta, 'rb'), file_name=file_output_desconsiderados_carta, mime='text/csv')

else:
    st.info("🔔 Faça upload dos arquivos CNIS e Carta Benefício para iniciar o processamento.")
