import streamlit as st
import pandas as pd

st.set_page_config(page_title="Dashboard Previdenciário Completo", layout="wide")

st.title("📑 Dashboard Previdenciário Completo com Reprocessamento")

# Sidebar para upload
st.sidebar.header("🔽 Upload dos Arquivos")
cnis_file = st.sidebar.file_uploader("Upload - 80% Maiores Salários CNIS", type=["csv"])
carta_file = st.sidebar.file_uploader("Upload - 80% Maiores Salários Carta", type=["csv"])
desconsid_file = st.sidebar.file_uploader("Upload - Salários Desconsiderados", type=["csv"])

if cnis_file and carta_file and desconsid_file:
    # Leitura dos arquivos
    df_cnis = pd.read_csv(cnis_file, delimiter=';', encoding='utf-8')
    df_carta = pd.read_csv(carta_file, delimiter=';', encoding='utf-8')
    df_desconsiderados = pd.read_csv(desconsid_file, delimiter=';', encoding='utf-8')

    # Organizando CNIS
    df_cnis = df_cnis.iloc[:,0].str.split(',', expand=True)
    df_cnis.columns = ['Seq', 'Competência', 'Remuneração', 'Ano']
    df_cnis['Remuneração'] = pd.to_numeric(df_cnis['Remuneração'], errors='coerce')

    # 80% maiores salários CNIS
    df_cnis_sorted = df_cnis.sort_values(by='Remuneração', ascending=False)
    qtd_80 = int(len(df_cnis_sorted) * 0.8)
    df_top80 = df_cnis_sorted.head(qtd_80)
    df_bottom10 = df_cnis_sorted.tail(len(df_cnis_sorted) - qtd_80)

    # Organizando desconsiderados
    df_desconsiderados = df_desconsiderados.iloc[:,0].str.split(',', expand=True)
    df_desconsiderados.columns = ['Seq', 'Seq.', 'Data', 'Salário', 'Índice', 'Sal. Corrigido', 'Observação', 'Ano', 'Duplicado']
    df_desconsiderados['Sal. Corrigido'] = pd.to_numeric(df_desconsiderados['Sal. Corrigido'], errors='coerce')

    # Verificando vantagem
    min_80 = df_top80['Remuneração'].min()
    df_vantajosos = df_desconsiderados[df_desconsiderados['Sal. Corrigido'] > min_80]

    # Métrica Resumo
    st.subheader("Resumo do Cálculo Aplicado")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total CNIS", len(df_cnis))
    col2.metric("80% Maiores Salários", len(df_top80))
    col3.metric("Desconsiderados Reaproveitados", len(df_vantajosos))

    # Gráficos com Streamlit Charts
    st.subheader("📊 Comparativo CNIS - 80% Maiores Salários")
    st.bar_chart(data=df_top80, x='Competência', y='Remuneração', use_container_width=True)

    st.subheader("📈 Evolução Média Salarial - CNIS")
    st.line_chart(data=df_top80, x='Competência', y='Remuneração', use_container_width=True)

    # Tabelas detalhadas
    st.subheader("📄 80% Maiores Salários")
    st.dataframe(df_top80)
    st.subheader("📄 10% Salários Descartados")
    st.dataframe(df_bottom10)
    st.subheader("📄 Salários Desconsiderados Reaproveitados")
    st.dataframe(df_vantajosos)

    # Aplicação Fator Previdenciário (exemplo baseado nos dados)
    st.subheader("🧮 Cálculo Fator Previdenciário e Benefício")
    media = df_top80['Remuneração'].mean()
    Tc = 38
    Es = 21.8
    Id = 60
    a = 0.31
    fator = (Tc * a / Es) * (1 + (Id + Tc * a)/100)
    fator = round(fator, 4)
    salario_beneficio = round(media * fator, 2)
    st.write(f"**Média dos 80% maiores salários:** R$ {media:,.2f}")
    st.write(f"**Fator Previdenciário aplicado:** {fator}")
    st.write(f"**Salário de Benefício (corrigido):** R$ {salario_beneficio:,.2f}")

    # Tabela consolidada para download
    st.subheader("📥 Planilha Consolidação Final")
    consolidado = df_top80.copy()
    consolidado['Considerado'] = 'Sim'
    df_vantajosos['Considerado'] = 'Reaproveitado'
    consolidado_final = pd.concat([consolidado, df_vantajosos[['Competência', 'Sal. Corrigido', 'Considerado']].rename(columns={'Sal. Corrigido':'Remuneração'})], ignore_index=True)
    st.dataframe(consolidado_final)

    # Download da planilha consolidada
    st.sidebar.download_button(label="⬇️ Baixar Consolidação Final (CSV)", data=consolidado_final.to_csv(index=False).encode('utf-8'), file_name='Consolidado_Final.csv', mime='text/csv')

else:
    st.info("🔔 Faça o upload dos 3 arquivos obrigatórios para visualizar o dashboard.")
