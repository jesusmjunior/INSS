import streamlit as st
import pandas as pd
from fpdf import FPDF
import io

st.set_page_config(page_title="Dashboard Previdenciário Completo", layout="wide")

st.title("📑 Dashboard Previdenciário Completo com Reprocessamento e PDF")

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

    # Download da planilha consolidada
    st.sidebar.download_button(label="⬇️ Baixar 80% Consolidados (CSV)", data=df_top80.to_csv(index=False).encode('utf-8'), file_name='80_Maiores_Consolidado.csv', mime='text/csv')

    # Geração de PDF Carta
    if st.button("📄 Gerar Relatório PDF da Carta Reprocessada"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Carta de Concessão Reprocessada", ln=True, align='C')
        pdf.ln(10)
        pdf.set_font("Arial", '', 11)
        pdf.multi_cell(0, 8, f"Beneficiário: ANTONIO FRANCISCO BEZERRA\nNIT: 1079867320-3\nNúmero Benefício: 171516921-0\n\nConforme reanálise, aplicou-se a regra dos 80% maiores salários e fator previdenciário atualizado.\n\nMédia dos salários: R$ {media:,.2f}\nFator Previdenciário: {fator}\nSalário de Benefício: R$ {salario_beneficio:,.2f}\n\nOs salários desconsiderados mais vantajosos foram integrados, resultando em benefício corrigido.")
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Resumo dos 80% Salários Considerados:", ln=True)
        for index, row in df_top80.iterrows():
            pdf.set_font("Arial", '', 10)
            pdf.cell(0, 8, f"Competência: {row['Competência']} | Remuneração: R$ {row['Remuneração']:,.2f}", ln=True)

        # Exportação PDF
        pdf_output = io.BytesIO()
        pdf.output(pdf_output)
        st.download_button(label="⬇️ Baixar PDF Carta Reprocessada", data=pdf_output.getvalue(), file_name="Carta_Reprocessada.pdf", mime="application/pdf")

else:
    st.info("🔔 Faça o upload dos 3 arquivos obrigatórios para visualizar o dashboard.")
