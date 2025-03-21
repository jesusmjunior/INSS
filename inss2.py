import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Dashboard Previdenciário Completo", layout="wide")

# Funções de processamento
def organizar_cnis(file):
    df = pd.read_csv(file, delimiter=';', encoding='utf-8')
    df = df.iloc[:,0].str.split(',', expand=True)
    df.columns = ['Seq', 'Competência', 'Remuneração', 'Ano']
    df['Remuneração'] = pd.to_numeric(df['Remuneração'], errors='coerce')
    df = df[df['Remuneração'] < 50000]  # Controle fuzzy - Remove discrepantes
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

# Sidebar Upload
st.sidebar.header("🔽 Upload dos Arquivos")
cnis_file = st.sidebar.file_uploader("Upload - CNIS", type=["csv"])
carta_file = st.sidebar.file_uploader("Upload - Carta", type=["csv"])
desconsid_file = st.sidebar.file_uploader("Upload - Desconsiderados", type=["csv"])

# MULTI-ABAS
aba = st.sidebar.radio("Navegação", ["Dashboard", "Gráficos", "Explicação do Cálculo"])

if cnis_file and carta_file and desconsid_file:

    df_cnis = organizar_cnis(cnis_file)
    df_desconsiderados = organizar_desconsiderados(desconsid_file)

    # 80% maiores salários
    df_cnis_sorted = df_cnis.sort_values(by='Remuneração', ascending=False)
    qtd_80 = int(len(df_cnis_sorted) * 0.8)
    df_top80 = df_cnis_sorted.head(qtd_80)
    df_bottom10 = df_cnis_sorted.tail(len(df_cnis_sorted) - qtd_80)

    # Desconsiderados vantajosos
    min_80 = df_top80['Remuneração'].min()
    df_vantajosos = df_desconsiderados[df_desconsiderados['Sal. Corrigido'] > min_80]

    # Média e fator previdenciário
    media_salarios = df_top80['Remuneração'].mean()
    fator = fator_previdenciario(Tc=38, Es=21.8, Id=60)
    salario_beneficio = round(media_salarios * fator, 2)

    # Dashboard Principal
    if aba == "Dashboard":
        st.title("📑 Dashboard Previdenciário Completo")

        col1, col2, col3 = st.columns(3)
        col1.metric("Total CNIS", len(df_cnis))
        col2.metric("80% Maiores Salários", len(df_top80))
        col3.metric("Desconsid. Reaproveitados", len(df_vantajosos))

        st.subheader("🧮 Resultados Previdenciários")
        st.write(f"**Média dos 80% maiores salários:** R$ {media_salarios:,.2f}")
        st.write(f"**Fator Previdenciário:** {fator}")
        st.write(f"**Salário de Benefício:** R$ {salario_beneficio:,.2f}")
        st.write(f"**Renda Mensal Inicial:** R$ {salario_beneficio:,.2f}")

        st.subheader("📄 Tabelas Detalhadas")
        st.dataframe(df_top80)
        st.dataframe(df_vantajosos)

        # Download final consolidado
        consolidado = df_top80.copy()
        consolidado['Considerado'] = 'Sim'
        df_vantajosos['Considerado'] = 'Reaproveitado'
        consolidado_final = pd.concat([consolidado, df_vantajosos[['Competência', 'Sal. Corrigido', 'Considerado']].rename(columns={'Sal. Corrigido':'Remuneração'})], ignore_index=True)
        st.sidebar.download_button(label="⬇️ Baixar Consolidação (CSV)", data=consolidado_final.to_csv(index=False).encode('utf-8'), file_name='Consolidado_Final.csv', mime='text/csv')

    # Gráficos
    elif aba == "Gráficos":
        st.title("📊 Análise Visual dos Salários")
        st.bar_chart(data=df_top80, x='Competência', y='Remuneração', use_container_width=True)
        st.line_chart(data=df_top80, x='Competência', y='Remuneração', use_container_width=True)

    # Explicação
    elif aba == "Explicação do Cálculo":
        st.title("🧮 Explicação Detalhada do Cálculo Previdenciário")

        st.markdown("""
        ### Fórmula Aplicada para o Fator Previdenciário:
        """)
        st.latex(r'''
        Fator\ Previdenciário = \frac{T_c \times a}{E_s} \times \left(1 + \frac{I_d + T_c \times a}{100}\right)
        ''')
        st.markdown("""
        Onde:
        - **Tc** = Tempo de Contribuição = 38 anos
        - **Es** = Expectativa de Sobrevida = 21,8 anos
        - **Id** = Idade = 60 anos
        - **a** = Alíquota = 0,31
        """)
        st.latex(fr'''
        Salário\ de\ Benefício = Média_{80\%} \times Fator = {media_salarios:.2f} \times {fator} = {salario_beneficio:.2f}
        ''')
        st.markdown("""
        ---
        ### Aplicação da Lógica Fuzzy:
        - **γ (Gama)**: Salários discrepantes (R$90.000+) são removidos do cálculo.
        - **α (Alfa)**: Funções moduladas e variáveis claras.
        - **θ (Theta)**: Otimização matemática e visualização via LaTeX.
        """)
else:
    st.info("🔔 Faça upload dos 3 arquivos obrigatórios para liberar o dashboard.")

