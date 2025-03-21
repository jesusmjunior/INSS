import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Dashboard Previdenciário Inteligente", layout="wide")
st.title("📑 Dashboard Previdenciário com Regras Fuzzy e LaTeX")

# Sidebar Upload
st.sidebar.header("🔽 Upload dos Arquivos")
cnis_file = st.sidebar.file_uploader("Upload - CNIS", type=["csv"])
carta_file = st.sidebar.file_uploader("Upload - Carta", type=["csv"])
desconsid_file = st.sidebar.file_uploader("Upload - Desconsiderados", type=["csv"])

# Funções Modularizadas
def organizar_cnis(file):
    df = pd.read_csv(file, delimiter=';', encoding='utf-8')
    df = df.iloc[:,0].str.split(',', expand=True)
    df.columns = ['Seq', 'Competência', 'Remuneração', 'Ano']
    df['Remuneração'] = pd.to_numeric(df['Remuneração'], errors='coerce')
    return df

def remover_outliers(df, limite_superior=50000):
    """γ (Gama) - Correção crítica para remover salários absurdos"""
    df_filtrado = df[df['Remuneração'] < limite_superior]
    return df_filtrado

def calcular_80_maiores(df):
    df_sorted = df.sort_values(by='Remuneração', ascending=False)
    qtd_80 = int(len(df_sorted) * 0.8)
    df_top = df_sorted.head(qtd_80)
    df_bottom = df_sorted.tail(len(df_sorted) - qtd_80)
    return df_top, df_bottom

def aplicar_fator_previdenciario(media, Tc=38, Es=21.8, Id=60, a=0.31):
    """θ (Theta) - Otimização matemática"""
    fator = (Tc * a / Es) * (1 + (Id + Tc * a)/100)
    fator = round(fator, 4)
    salario_beneficio = round(media * fator, 2)
    return fator, salario_beneficio

def apresentar_calculo_latex(media, fator, salario_beneficio):
    """θ (Theta) - LaTeX para apresentação"""
    st.latex(r'''
    Fator = \frac{T_c \times a}{E_s} \times \left(1 + \frac{I_d + T_c \times a}{100}\right)
    ''')
    st.latex(fr'''
    Salário\ de\ Benefício = {media:.2f} \times {fator} = {salario_beneficio:.2f}
    ''')

if cnis_file and carta_file and desconsid_file:
    # α (Alfa) - Organização
    df_cnis = organizar_cnis(cnis_file)
    df_cnis = remover_outliers(df_cnis, limite_superior=50000)

    df_top80, df_bottom10 = calcular_80_maiores(df_cnis)

    # Desconsiderados
    df_desconsiderados = pd.read_csv(desconsid_file, delimiter=';', encoding='utf-8')
    df_desconsiderados = df_desconsiderados.iloc[:,0].str.split(',', expand=True)
    df_desconsiderados.columns = ['Seq', 'Seq.', 'Data', 'Salário', 'Índice', 'Sal. Corrigido', 'Observação', 'Ano', 'Duplicado']
    df_desconsiderados['Sal. Corrigido'] = pd.to_numeric(df_desconsiderados['Sal. Corrigido'], errors='coerce')

    # Correção - reaproveitamento
    min_80 = df_top80['Remuneração'].min()
    df_vantajosos = df_desconsiderados[df_desconsiderados['Sal. Corrigido'] > min_80]

    # Resumo
    st.subheader("📊 Resumo do Cálculo com Controle Fuzzy")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total CNIS", len(df_cnis))
    col2.metric("80% Maiores Salários", len(df_top80))
    col3.metric("Desconsiderados Reaproveitados", len(df_vantajosos))

    # Gráficos
    st.bar_chart(data=df_top80, x='Competência', y='Remuneração', use_container_width=True)

    # Fator Previdenciário Aplicado
    media = df_top80['Remuneração'].mean()
    fator, salario_beneficio = aplicar_fator_previdenciario(media)

    st.subheader("🧮 Cálculo Previdenciário Detalhado")
    st.write(f"**Média dos 80% maiores salários:** R$ {media:,.2f}")
    st.write(f"**Fator Previdenciário aplicado:** {fator}")
    st.write(f"**Salário de Benefício:** R$ {salario_beneficio:,.2f}")
    
    apresentar_calculo_latex(media, fator, salario_beneficio)

    # Consolidado Final
    consolidado = df_top80.copy()
    consolidado['Considerado'] = 'Sim'
    df_vantajosos['Considerado'] = 'Reaproveitado'
    consolidado_final = pd.concat([consolidado, df_vantajosos[['Competência', 'Sal. Corrigido', 'Considerado']].rename(columns={'Sal. Corrigido':'Remuneração'})], ignore_index=True)
    st.dataframe(consolidado_final)

    # Download CSV
    st.sidebar.download_button(label="⬇️ Baixar Consolidação (CSV)", data=consolidado_final.to_csv(index=False).encode('utf-8'), file_name='Consolidado_Final.csv', mime='text/csv')

else:
    st.info("🔔 Faça o upload dos 3 arquivos obrigatórios para visualizar o dashboard.")
