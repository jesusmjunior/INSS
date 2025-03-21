import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Cálculo Previdenciário INSS", layout="wide")
st.title("📑 Cálculo Previdenciário Proporcional com Regras INSS")

# Sidebar para uploads
st.sidebar.header("🔽 Upload Arquivo CNIS (CSV)")
cnis_file = st.sidebar.file_uploader("Upload - CNIS", type=["csv"])

# Função para cálculo Fator Previdenciário
def fator_previdenciario(Tc, Es, Id, a=0.31):
    fator = (Tc * a / Es) * (1 + ((Id + Tc * a) / 100))
    return round(fator, 4)

# Função para organizar CNIS
def organizar_cnis(file):
    df = pd.read_csv(file, delimiter=';', encoding='utf-8')
    df = df.iloc[:,0].str.split(',', expand=True)
    df.columns = ['Seq', 'Competência', 'Remuneração', 'Ano']
    df['Remuneração'] = pd.to_numeric(df['Remuneração'], errors='coerce')
    return df

# Aplicação
if cnis_file:
    df_cnis = organizar_cnis(cnis_file)

    # Remover salários discrepantes (gamma fuzzy block)
    df_cnis = df_cnis[df_cnis['Remuneração'] < 50000]

    # Calcular média dos 80% maiores salários
    df_cnis_sorted = df_cnis.sort_values(by='Remuneração', ascending=False)
    qtd_80 = int(len(df_cnis_sorted) * 0.8)
    df_top80 = df_cnis_sorted.head(qtd_80)
    media_salarios = df_top80['Remuneração'].mean()

    # Parâmetros do cálculo
    Tc = 38
    Es = 21.8
    Id = 60
    a = 0.31

    # Cálculo Fator Previdenciário
    fator = fator_previdenciario(Tc, Es, Id, a)

    # Cálculo Salário Benefício
    salario_beneficio = round(media_salarios * fator, 2)

    # Resultados
    st.subheader("📊 Resultados do Cálculo Previdenciário")
    st.write(f"**Média dos 80% maiores salários:** R$ {media_salarios:,.2f}")
    st.write(f"**Fator Previdenciário:** {fator}")
    st.write(f"**Salário de Benefício:** R$ {salario_beneficio:,.2f}")
    st.write(f"**Renda Mensal Inicial (coeficiente 1.0):** R$ {salario_beneficio:,.2f}")

    # Fórmula LaTeX
    st.subheader("🧮 Fórmula Matemática Aplicada (LaTeX)")
    st.latex(r'''
    Fator\ Previdenciário = \frac{T_c \times a}{E_s} \times \left(1 + \frac{I_d + T_c \times a}{100}\right)
    ''')
    st.latex(fr'''
    Salário\ de\ Benefício = {media_salarios:.2f} \times {fator} = {salario_beneficio:.2f}
    ''')

    # Mostrar tabelas
    st.subheader("📄 Detalhamento dos Salários Considerados")
    st.dataframe(df_top80)
else:
    st.info("🔔 Faça upload do arquivo CNIS para iniciar o cálculo.")

