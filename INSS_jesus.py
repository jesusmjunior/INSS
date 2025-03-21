import streamlit as st
import pandas as pd
import numpy as np

# CONFIGURAÇÃO INICIAL
st.set_page_config(page_title="Dashboard Previdenciário Profissional", layout="wide")

# FUNÇÕES UTILITÁRIAS
def organizar_cnis(file):
    df = pd.read_csv(file, delimiter=';', encoding='utf-8')
    df = df.iloc[:,0].str.split(',', expand=True)
    df.columns = ['Seq', 'Competência', 'Remuneração', 'Ano']
    df['Remuneração'] = pd.to_numeric(df['Remuneração'], errors='coerce')
    df = df[df['Remuneração'] < 50000]  # Remover discrepantes - lógica fuzzy
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

# SIDEBAR UPLOAD
st.sidebar.header("🔽 Upload dos Arquivos")
cnis_file = st.sidebar.file_uploader("Upload - CNIS", type=["csv"])
carta_file = st.sidebar.file_uploader("Upload - Carta", type=["csv"])
desconsid_file = st.sidebar.file_uploader("Upload - Desconsiderados", type=["csv"])

# ABAS DO APP
aba = st.sidebar.radio("Navegação", ["Dashboard", "Gráficos", "Explicação", "Simulador", "Relatório"])

# PROCESSAMENTO PRINCIPAL
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

    # ABA DASHBOARD
    if aba == "Dashboard":
        st.title("📑 Dashboard Previdenciário Profissional")

        col1, col2, col3 = st.columns(3)
        col1.metric("Total CNIS", len(df_cnis))
        col2.metric("80% Maiores Salários", len(df_top80))
        col3.metric("Desconsid. Reaproveitados", len(df_vantajosos))

        st.subheader("🧮 Resultados Previdenciários")
        st.write(f"**Média dos 80% maiores salários:** R$ {media_salarios:,.2f}")
        st.write(f"**Fator Previdenciário:** {fator}")
        st.write(f"**Salário de Benefício:** R$ {salario_beneficio:,.2f}")

        st.subheader("📄 Tabelas Detalhadas")
        st.dataframe(df_top80)
        st.dataframe(df_vantajosos)

        # AJUSTE PARA CONCATENAR
        df_vantajosos['Competência'] = df_vantajosos['Data']
        df_vantajosos['Remuneração'] = df_vantajosos['Sal. Corrigido']
        df_vantajosos['Considerado'] = 'Reaproveitado'
        consolidado = df_top80.copy()
        consolidado['Considerado'] = 'Sim'
        consolidado_final = pd.concat(
            [consolidado[['Competência', 'Remuneração', 'Considerado']],
             df_vantajosos[['Competência', 'Remuneração', 'Considerado']]],
            ignore_index=True
        )

        st.sidebar.download_button(
            label="⬇️ Baixar Consolidado CSV",
            data=consolidado_final.to_csv(index=False).encode('utf-8'),
            file_name='Consolidado_Final.csv',
            mime='text/csv'
        )

    # ABA GRÁFICOS
    elif aba == "Gráficos":
        st.title("📊 Visualização Gráfica")
        st.bar_chart(data=df_top80, x='Competência', y='Remuneração')
        st.line_chart(data=df_top80, x='Competência', y='Remuneração')

    # ABA EXPLICAÇÃO
    elif aba == "Explicação":
        st.title("📖 Explicação Detalhada")
        st.markdown("### Fórmula Utilizada:")
        st.latex(r'''
        Fator\ Previdenciário = \frac{T_c \times a}{E_s} \times \left(1 + \frac{I_d + T_c \times a}{100}\right)
        ''')
        st.markdown(f"""
        Onde:
        - $T_c = 38$ anos (Tempo de Contribuição)
        - $E_s = 21,8$ anos (Expectativa Sobrevida)
        - $I_d = 60$ anos (Idade)
        - $a = 0,31$ (Alíquota)
        """)
        st.latex(fr'''
        Salário\ Benefício = Média_{{80\%}} \times {fator} = {salario_beneficio:,.2f}
        ''')
        st.markdown("""
        ### Aplicação Lógica Fuzzy:
        - γ (Gama): Eliminação de salários discrepantes (> R$50.000)
        - α (Alfa): Modularização clara
        - θ (Theta): Visualização matemática otimizada via LaTeX
        """)

    # ABA SIMULADOR
    elif aba == "Simulador":
        st.title("⚙️ Simulador Previdenciário")
        Tc_input = st.number_input("Tempo de Contribuição (anos)", value=38)
        Es_input = st.number_input("Expectativa Sobrevida", value=21.8)
        Id_input = st.number_input("Idade", value=60)
        a_input = st.number_input("Alíquota", value=0.31)
        fator_simulado = fator_previdenciario(Tc_input, Es_input, Id_input, a_input)
        salario_simulado = round(media_salarios * fator_simulado, 2)
        st.write(f"**Fator Previdenciário Simulado:** {fator_simulado}")
        st.write(f"**Salário Benefício Simulado:** R$ {salario_simulado:,.2f}")

    # ABA RELATÓRIO
    elif aba == "Relatório":
        st.title("📄 Relatório Consolidado Completo")
        st.dataframe(consolidado_final)
        st.sidebar.download_button(
            label="⬇️ Download Relatório CSV",
            data=consolidado_final.to_csv(index=False).encode('utf-8'),
            file_name='Relatorio_Completo.csv',
            mime='text/csv'
        )

else:
    st.info("🔔 Faça upload dos 3 arquivos obrigatórios para liberar o dashboard.")
