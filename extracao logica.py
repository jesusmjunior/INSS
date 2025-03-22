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

def organizar_cnis(cnis_file):
    # Lê o arquivo CSV com ponto e vírgula como delimitador
    df_cnis = pd.read_csv(cnis_file, delimiter=";")
    
    # Verifica e renomeia as colunas
    df_cnis.columns = ['Seq', 'Competência', 'Remuneração', 'Ano']
    
    # Remover quaisquer espaços extras nas células de texto
    df_cnis = df_cnis.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    
    # Converte a coluna 'Remuneração' para numérico
    df_cnis['Remuneração'] = pd.to_numeric(df_cnis['Remuneração'], errors='coerce')
    
    # Filtra para valores acima de 50.000 (caso desejado)
    df_cnis = df_cnis[df_cnis['Remuneração'] > 50000]

    return df_cnis

def organizar_desconsiderados(desconsiderados_file):
    # Lê o arquivo CSV com ponto e vírgula como delimitador
    df_desconsiderados = pd.read_csv(desconsiderados_file, delimiter=";")
    
    # Verifica e renomeia as colunas
    df_desconsiderados.columns = ['Seq', 'Seq.', 'Data', 'Salário', 'Índice', 'Sal. Corrigido', 'Observação', 'Ano', 'Duplicado']
    
    # Remover quaisquer espaços extras nas células de texto
    df_desconsiderados = df_desconsiderados.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    
    # Converte as colunas numéricas
    df_desconsiderados['Salário'] = pd.to_numeric(df_desconsiderados['Salário'], errors='coerce')
    df_desconsiderados['Sal. Corrigido'] = pd.to_numeric(df_desconsiderados['Sal. Corrigido'], errors='coerce')
    
    # Filtra os dados com a observação "DESCONSIDERADO"
    df_desconsiderados = df_desconsiderados[df_desconsiderados['Observação'] == 'DESCONSIDERADO']
    
    return df_desconsiderados

def organizar_80_maiores_salarios(file):
    # Lê o arquivo CSV com ponto e vírgula como delimitador
    df = pd.read_csv(file, delimiter=";")
    
    # Verifica e renomeia as colunas
    df.columns = ['Seq', 'Competência', 'Remuneração', 'Ano']
    
    # Remover quaisquer espaços extras nas células de texto
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    
    # Converte a coluna 'Remuneração' para numérico
    df['Remuneração'] = pd.to_numeric(df['Remuneração'], errors='coerce')
    
    return df

def exportar_csv(df, nome_base):
    df.to_csv(f"{nome_base}.csv", index=False)
    return f"{nome_base}.csv"

# ===================== LAYOUT COM TABELAS =====================

st.subheader("📊 Tabelas Organizacionais")

col1, col2 = st.columns(2)

with col1:
    uploaded_cnis_file = st.file_uploader("🔽 Upload do arquivo 80% Maiores Salários CNIS", type="csv", key="cnis_file")

with col2:
    uploaded_carta_file = st.file_uploader("🔽 Upload do arquivo 80% Maiores Salários Carta", type="csv", key="carta_file")

with col1:
    uploaded_desconsiderados_file = st.file_uploader("🔽 Upload do arquivo Salários Desconsiderados na Carta", type="csv", key="desconsiderados_file")

# ===================== PROCESSAMENTO DOS DADOS =====================

if uploaded_cnis_file and uploaded_carta_file and uploaded_desconsiderados_file:
    # Organiza os dados
    df_cnis = organizar_cnis(uploaded_cnis_file)
    df_carta = organizar_80_maiores_salarios(uploaded_carta_file)
    df_desconsiderados = organizar_desconsiderados(uploaded_desconsiderados_file)
    
    # Exibindo as tabelas separadas
    st.subheader("📊 Tabela CNIS")
    st.dataframe(df_cnis, use_container_width=True)
    
    st.subheader("📊 Tabela Carta Benefício")
    st.dataframe(df_carta, use_container_width=True)
    
    st.subheader("📊 Tabela de Salários Desconsiderados")
    st.dataframe(df_desconsiderados, use_container_width=True)
    
    # Botões de download para cada tabela separada
    st.download_button("⬇️ Baixar CNIS CSV", data=df_cnis.to_csv(index=False).encode('utf-8'), file_name="Extrato_CNIS_Organizado.csv", mime='text/csv')
    st.download_button("⬇️ Baixar Carta CSV", data=df_carta.to_csv(index=False).encode('utf-8'), file_name="Carta_Beneficio_Organizada.csv", mime='text/csv')
    st.download_button("⬇️ Baixar Desconsiderados CSV", data=df_desconsiderados.to_csv(index=False).encode('utf-8'), file_name="Salarios_Desconsiderados_Carta.csv", mime='text/csv')

else:
    st.info("🔔 Faça upload dos arquivos CNIS, Carta Benefício e Salários Desconsiderados para iniciar o processamento.")
