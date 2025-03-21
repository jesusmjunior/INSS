import streamlit as st
import pandas as pd
import pdfplumber
import tabula
import os

st.set_page_config(page_title="Jesus e INSS | Extrator CNIS + Carta Benefício", layout="centered")

st.title("📄 JESUS E INSS - Extrator CNIS & Carta Benefício")
st.write("**Processamento automatizado baseado em lógica fuzzy, com exportação em CSV/XLSX**")

# --------------- CONFIGURAÇÕES INICIAIS --------------------
uploaded_file = st.file_uploader("🔽 Faça o upload do arquivo PDF (CNIS ou Carta Benefício):", type="pdf")
output_format = st.radio("📁 Formato de Exportação:", ['CSV', 'XLSX'])

# ------------------ FUNÇÕES BASE --------------------------

def verificar_existencia(path):
    return os.path.exists(path)

def extrair_tabula(pdf_path):
    try:
        dfs = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True, lattice=True)
        return dfs
    except Exception:
        return None

def extrair_plumber(pdf_path):
    linhas = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            lines = page.extract_text().split('\n')
            linhas.extend(lines)
    return linhas

def estrutura_cnis(linhas):
    data = []
    for line in linhas:
        if '/' in line and any(char.isdigit() for char in line):
            parts = line.strip().split()
            if len(parts) >= 2:
                data.append({'Competência': parts[0], 'Remuneração': parts[1]})
    return pd.DataFrame(data)

def estrutura_carta(dfs):
    if dfs:
        for df in dfs:
            if len(df.columns) >= 5:
                df.columns = ['Seq.', 'Data', 'Salário', 'Índice', 'Sal. Corrigido', 'Observação'][:len(df.columns)]
                return df
    return None

def exportar_df(df, nome_base, formato):
    if formato == 'CSV':
        df.to_csv(f"{nome_base}.csv", index=False)
        return f"{nome_base}.csv"
    else:
        df.to_excel(f"{nome_base}.xlsx", index=False)
        return f"{nome_base}.xlsx"

# ------------------ EXECUÇÃO PRINCIPAL --------------------

if uploaded_file is not None:
    with st.spinner('🔍 Verificando e processando o PDF...'):
        temp_pdf_path = f"temp_{uploaded_file.name}"
        with open(temp_pdf_path, "wb") as f:
            f.write(uploaded_file.read())
        
        # Lógica fuzzy para escolha do método
        tabula_dfs = extrair_tabula(temp_pdf_path)
        if tabula_dfs and any(not df.empty for df in tabula_dfs):
            st.success("📑 Documento identificado como **Carta de Benefício** (Tabula detectou tabelas)")
            df_final = estrutura_carta(tabula_dfs)
            nome_output = "Carta_Beneficio_Extraida"
        else:
            st.warning("📝 Documento identificado como **Extrato CNIS** (Nenhuma tabela detectada)")
            linhas = extrair_plumber(temp_pdf_path)
            df_final = estrutura_cnis(linhas)
            nome_output = "Extrato_CNIS_Extraido"

        if df_final is not None and not df_final.empty:
            st.subheader("📊 Dados Extraídos:")
            st.dataframe(df_final)

            file_output = exportar_df(df_final, nome_output, output_format)
            st.success(f"✅ Exportação concluída! Arquivo gerado: {file_output}")
            with open(file_output, 'rb') as f:
                st.download_button("⬇️ Baixar Arquivo", data=f, file_name=file_output, mime='application/octet-stream')
            
            # Perguntas adicionais:
            st.divider()
            st.info("Deseja integrar com Google Sheets ou API? 🚀 (Futuro recurso)")
            st.info("Deseja validar dados fuzzy ou processar um novo documento?")

        else:
            st.error("❌ Não foi possível estruturar os dados.")

        os.remove(temp_pdf_path)

else:
    st.info("👆 Faça o upload de um arquivo PDF para iniciar o processamento.")

