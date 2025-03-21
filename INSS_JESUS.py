import streamlit as st
import pandas as pd
import numpy as np
import re
from io import StringIO

# ===================== CONFIGURAÇÃO DA PÁGINA =====================
st.set_page_config(page_title="Jesus e INSS | Sistema Completo", layout="wide")

# ===================== LOGIN ABA 1 =====================
def login():
    if 'login_visible' not in st.session_state:
        st.session_state.login_visible = True

    if st.session_state.login_visible:
        with st.expander("🔐 Área Protegida - Login Obrigatório", expanded=True):
            user = st.text_input("Usuário (Email)")
            password = st.text_input("Senha", type="password")

            usuarios = {
                "jesusmjunior2021@gmail.com": "jr010507",
                "joliveiramaccf@gmail.com": "cgti@383679"
            }

            if (user in usuarios and password == usuarios[user]):
                st.success("Login efetuado com sucesso ✅")
                if st.button("Ocultar Login"):
                    st.session_state.login_visible = False
                return True
            else:
                if user and password:
                    st.error("Usuário ou senha incorretos ❌")
                st.stop()
    else:
        st.info("Login ocultado. Clique abaixo para reexibir.")
        if st.button("Mostrar Login"):
            st.session_state.login_visible = True
            st.experimental_rerun()

# ===================== EXECUTA LOGIN =====================
login()

# ===================== SELEÇÃO DE ABA =====================
aba = st.sidebar.radio("Selecione a Aba:", [
    "Dashboard Previdenciário",
    "Extrator CNIS & Carta Benefício",
    "Inserção Manual de Dados",
    "Relatório Final Unificado"
])

# ===================== FUNÇÕES COMUNS =====================
def exportar_csv(df, nome_base):
    df.to_csv(f"{nome_base}.csv", index=False)
    st.session_state[nome_base + '.csv'] = f"{nome_base}.csv"
    return f"{nome_base}.csv"

def ler_texto(uploaded_file):
    stringio = StringIO(uploaded_file.getvalue().decode("utf-8", errors='ignore'))
    return stringio.read()

def estrutura_cnis(texto):
    linhas = texto.split('\n')
    data = []
    for line in linhas:
        match = re.search(r"(\d{2}/\d{4})\s+([0-9.]+,[0-9]{2})", line)
        if match:
            competencia = match.group(1)
            remuneracao = match.group(2).replace('.', '').replace(',', '.')
            data.append({'Competência': competencia, 'Remuneração': remuneracao})
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
                'Observação': observacao
            })
    return pd.DataFrame(data)

def filtrar_salarios_desconsiderados_carta(df_carta):
    df_filtrado = df_carta[df_carta['Observação'].str.upper().str.contains("DESCONSIDERADO")].copy()
    df_filtrado['Origem'] = "Carta"
    if not df_filtrado.empty:
        nome_arquivo = exportar_csv(df_filtrado, "Salarios_Desconsiderados_Carta")
        st.success(f"Arquivo gerado: {nome_arquivo}")
        st.dataframe(df_filtrado)
    return df_filtrado

# Filtragem de Salários Desconsiderados no CNIS
def filtrar_salarios_desconsiderados_cnis(df_cnis):
    df_filtrado = df_cnis[df_cnis['Remuneração'] < 1000].copy()  # Exemplo, ajuste conforme sua lógica
    df_filtrado['Origem'] = "CNIS"
    if not df_filtrado.empty:
        nome_arquivo = exportar_csv(df_filtrado, "Salarios_Desconsiderados_Cnis")
        st.success(f"Arquivo gerado: {nome_arquivo}")
        st.dataframe(df_filtrado)
    return df_filtrado

# ===================== ABA 1: Dashboard Previdenciário =====================
if aba == "Dashboard Previdenciário":
    st.title("📑 Dashboard Previdenciário Profissional")

    # Funções Utilitárias
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

    # Upload dos arquivos
    st.sidebar.header("🔽 Upload dos Arquivos")
    cnis_file = st.sidebar.file_uploader("Upload - CNIS", type=["csv"])
    carta_file = st.sidebar.file_uploader("Upload - Carta", type=["csv"])
    desconsid_file = st.sidebar.file_uploader("Upload - Desconsiderados", type=["csv"])

    aba_dash = st.sidebar.radio("Navegação", ["Dashboard", "Gráficos", "Explicação", "Simulador", "Relatório"])

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

        if aba_dash == "Dashboard":
            st.subheader("🧮 Resultados Previdenciários")
            col1, col2, col3 = st.columns(3)
            col1.metric("Total CNIS", len(df_cnis))
            col2.metric("80% Maiores Salários", len(df_top80))
            col3.metric("Desconsid. Reaproveitados", len(df_vantajosos))
            st.write(f"**Média dos 80% maiores salários:** {formatar_moeda(media_salarios)}")
            st.write(f"**Fator Previdenciário:** {fator}")
            st.write(f"**Salário de Benefício:** {formatar_moeda(salario_beneficio)}")
            st.subheader("📄 Tabelas Detalhadas")
            st.dataframe(df_top80)
            st.dataframe(df_vantajosos)

        elif aba_dash == "Gráficos":
            st.title("📊 Visualização Gráfica")
            df_grafico = df_cnis_sorted.head(qtd_80)
            st.bar_chart(data=df_grafico, x='Competência', y='Remuneração')
            st.line_chart(data=df_grafico, x='Competência', y='Remuneração')

        elif aba_dash == "Explicação":
            st.title("📖 Explicação Detalhada")
            st.markdown("### Fórmulas Aplicadas:")
            st.latex(r'''Fator\ Previdenci\u00e1rio = \frac{T_c \times a}{E_s} \times \left(1 + \frac{I_d + T_c \times a}{100}\right)''')
            st.markdown(f"""
            Onde:
            - $T_c = 38$ anos (Tempo de Contribuição)
            - $E_s = 21,8$ anos (Expectativa Sobrevida)
            - $I_d = 60$ anos (Idade)
            - $a = 0,31$ (Alíquota)
            """)
            st.latex(r'''Sal\u00e1rio\ de\ Benef\u00edcio = M\u00e9dia_{80\%} \times Fator''')
            st.markdown(f"**Média = {formatar_moeda(media_salarios)}, Fator = {fator}, Resultado = {formatar_moeda(salario_beneficio)}**")

        elif aba_dash == "Simulador":
            st.title("⚙️ Simulador Previdenciário")
            Tc_input = st.number_input("Tempo de Contribuição (anos)", value=38)
            Es_input = st.number_input("Expectativa Sobrevida", value=21.8)
            Id_input = st.number_input("Idade", value=60)
            a_input = st.number_input("Alíquota", value=0.31)
            fator_simulado = fator_previdenciario(Tc_input, Es_input, Id_input, a_input)
            salario_simulado = round(media_salarios * fator_simulado, 2)
            st.write(f"**Fator Previdenciário Simulado:** {fator_simulado}")
            st.write(f"**Salário Benefício Simulado:** {formatar_moeda(salario_simulado)}")

        elif aba_dash == "Relatório":
            st.title("📄 Relatório Previdenciário Consolidado")
            st.markdown(""" ## Relatório Consolidado
            Este relatório apresenta os resultados detalhados do processamento previdenciário conforme os dados enviados e as regras aplicadas. 
            """)
            st.markdown(f"**Total de registros CNIS:** {len(df_cnis)}")
            st.markdown(f"**80% maiores salários considerados:** {len(df_top80)}")
            st.markdown(f"**Salários desconsiderados reaproveitados:** {len(df_vantajosos)}")
            st.markdown("---")
            st.subheader("📌 Detalhamento dos 80% Maiores Salários")
            st.dataframe(df_top80)
            st.subheader("📌 Salários Desconsiderados Reaproveitados")
            st.dataframe(df_vantajosos)
            st.subheader("📌 Fórmula Previdenciária Aplicada")
            st.latex(r'''Fator\ Previdenci\u00e1rio = \frac{T_c \times a}{E_s} \times \left(1 + \frac{I_d + T_c \times a}{100}\right)''')
            st.markdown(f"**Fator aplicado:** {fator}")
            st.markdown(f"**Média dos salários:** {formatar_moeda(media_salarios)}")
            st.markdown(f"**Salário de Benefício Final:** {formatar_moeda(salario_beneficio)}")
            st.markdown("---")
            st.markdown("📎 **Este relatório pode ser impresso diretamente em PDF.**")

    else:
        st.info("🔔 Faça upload dos 3 arquivos obrigatórios para liberar o dashboard.")
