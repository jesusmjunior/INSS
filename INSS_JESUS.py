import streamlit as st
import pandas as pd
import numpy as np

# ================================
# CONFIGURAÇÃO INICIAL
# ================================
st.set_page_config(page_title="Dashboard Previdenciário Profissional", layout="wide")

# ================================
# LOGIN SIMPLES
# ================================
def login():
    st.title("🔐 Área Protegida - Login Obrigatório")
    user = st.text_input("Usuário (Email)")
    password = st.text_input("Senha", type="password")

    # Definindo os usuários e senhas válidos
    if (user == "jesusmjunior2021@gmail.com" and password == "jr010507") or (user == "joliveiramaccf@gmail.com" and password == "cgti@383679"):
        st.success("Login efetuado com sucesso ✅")
        return True
    else:
        if user and password:
            st.error("Usuário ou senha incorretos ❌")
        return False

# ================================
# FUNÇÕES DE PROCESSAMENTO
# ================================

# Organiza o CNIS (para os dados exportados em CSV ou XLSX)
def organizar_cnis(file):
    df = pd.read_csv(file, delimiter=';', encoding='utf-8')

    # Divide a primeira coluna em várias partes com base na vírgula
    df_split = df.iloc[:, 0].str.split(',', expand=True)
    df_split.columns = ['Seq', 'Competência', 'Remuneração', 'Ano'][:df_split.shape[1]]

    # Converte a coluna 'Remuneração' para numérico e aplica o filtro fuzzy
    df_split['Remuneração'] = pd.to_numeric(df_split['Remuneração'], errors='coerce')
    df_split = df_split[df_split['Remuneração'] < 50000]  # Filtro fuzzy
    return df_split

# Organiza os dados da Carta Benefício
def organizar_desconsiderados(file):
    df = pd.read_csv(file, delimiter=';', encoding='utf-8')
    df = df.iloc[:, 0].str.split(',', expand=True)
    df.columns = ['Seq', 'Seq.', 'Data', 'Salário', 'Índice', 'Sal. Corrigido', 'Observação', 'Ano', 'Duplicado']
    df['Sal. Corrigido'] = pd.to_numeric(df['Sal. Corrigido'], errors='coerce')
    return df

# Calcula o fator previdenciário
def fator_previdenciario(Tc, Es, Id, a=0.31):
    return round((Tc * a / Es) * (1 + ((Id + Tc * a) / 100)), 4)

# Formatação para moeda
def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ================================
# EXECUÇÃO DO APP
# ================================
if login():  # Executa o login

    # UPLOAD DOS ARQUIVOS
    st.sidebar.header("🔽 Upload dos Arquivos")
    cnis_file = st.sidebar.file_uploader("Upload - CNIS", type=["csv"])
    carta_file = st.sidebar.file_uploader("Upload - Carta", type=["csv"])
    desconsid_file = st.sidebar.file_uploader("Upload - Desconsiderados", type=["csv"])

    # Navegação
    aba = st.sidebar.radio("Navegação", ["Dashboard", "Gráficos", "Explicação", "Simulador", "Relatório"])

    # Verificando se os arquivos foram carregados
    if cnis_file and carta_file and desconsid_file:
        # Processando os arquivos
        df_cnis = organizar_cnis(cnis_file)
        df_desconsiderados = organizar_desconsiderados(desconsid_file)

        # Processamento para os 80% maiores salários
        df_cnis_sorted = df_cnis.sort_values(by='Remuneração', ascending=False)
        qtd_80 = int(len(df_cnis_sorted) * 0.8)
        df_top80 = df_cnis_sorted.head(qtd_80)

        # Calculando os parâmetros
        Tc_default, Es_default, Id_default, a_default = 38, 21.8, 60, 0.31
        media_salarios = df_top80['Remuneração'].mean()
        fator = fator_previdenciario(Tc_default, Es_default, Id_default, a_default)
        salario_beneficio = round(media_salarios * fator, 2)

        # Formatação monetária
        df_top80['Remuneração'] = df_top80['Remuneração'].apply(formatar_moeda)

        # ================================
        # ABAS PRINCIPAIS
        # ================================
        if aba == "Dashboard":
            st.title("📑 Dashboard Previdenciário Profissional")

            col1, col2, col3 = st.columns(3)
            col1.metric("Total CNIS", len(df_cnis))
            col2.metric("80% Maiores Salários", len(df_top80))
            col3.metric("Salário de Benefício", formatar_moeda(salario_beneficio))

            st.subheader("🧮 Resultados Previdenciários")
            st.write(f"**Média dos 80% maiores salários:** {formatar_moeda(media_salarios)}")
            st.write(f"**Fator Previdenciário:** {fator}")
            st.write(f"**Salário de Benefício:** {formatar_moeda(salario_beneficio)}")

            st.subheader("📄 Tabelas Detalhadas")
            st.dataframe(df_top80)

        elif aba == "Gráficos":
            st.title("📊 Visualização Gráfica")
            df_grafico = df_cnis_sorted.head(qtd_80)
            st.bar_chart(data=df_grafico, x='Competência', y='Remuneração')
            st.line_chart(data=df_grafico, x='Competência', y='Remuneração')

        elif aba == "Explicação":
            st.title("📖 Explicação Detalhada")
            st.markdown("### Fórmulas Aplicadas:")
            st.latex(r'''
            Fator\ Previdenci\u00e1rio = \frac{T_c \times a}{E_s} \times \left(1 + \frac{I_d + T_c \times a}{100}\right)
            ''')
            st.markdown(f"""
            Onde:
            - $T_c = 38$ anos (Tempo de Contribuição)
            - $E_s = 21,8$ anos (Expectativa Sobrevida)
            - $I_d = 60$ anos (Idade)
            - $a = 0,31$ (Alíquota)
            """)
            st.latex(r'''
            Salário\ de\ Benefício = Média_{80\%} \times Fator
            ''')
            st.markdown(f"**Média = {formatar_moeda(media_salarios)}, Fator = {fator}, Resultado = {formatar_moeda(salario_beneficio)}**")

        elif aba == "Simulador":
            st.title("⚙️ Simulador Previdenciário")
            Tc_input = st.number_input("Tempo de Contribuição (anos)", value=38)
            Es_input = st.number_input("Expectativa Sobrevida", value=21.8)
            Id_input = st.number_input("Idade", value=60)
            a_input = st.number_input("Alíquota", value=0.31)
            fator_simulado = fator_previdenciario(Tc_input, Es_input, Id_input, a_input)
            salario_simulado = round(media_salarios * fator_simulado, 2)
            st.write(f"**Fator Previdenciário Simulado:** {fator_simulado}")
            st.write(f"**Salário Benefício Simulado:** {formatar_moeda(salario_simulado)}")

        elif aba == "Relatório":
            st.title("📄 Relatório Previdenciário Consolidado")

            st.markdown("""
            ## Relatório Consolidado
            
            Este relatório apresenta os resultados detalhados do processamento previdenciário conforme os dados enviados e as regras aplicadas.
            """)
            st.markdown(f"**Total de registros CNIS:** {len(df_cnis)}")
            st.markdown(f"**80% maiores salários considerados:** {len(df_top80)}")
            st.markdown(f"**Salários desconsiderados reaproveitados:** {len(df_desconsiderados)}")
            st.markdown("---")

            st.subheader("📌 Detalhamento dos 80% Maiores Salários")
            st.dataframe(df_top80)

            st.subheader("📌 Salários Desconsiderados Reaproveitados")
            st.dataframe(df_desconsiderados)

            st.subheader("📌 Fórmula Previdenciária Aplicada")
            st.latex(r'''
            Fator\ Previdenci\u00e1rio = \frac{T_c \times a}{E_s} \times \left(1 + \frac{I_d + T_c \times a}{100}\right)
            ''')
            st.markdown(f"**Fator aplicado:** {fator}")
            st.markdown(f"**Média dos salários:** {formatar_moeda(media_salarios)}")
            st.markdown(f"**Salário de Benefício Final:** {formatar_moeda(salario_beneficio)}")
            st.markdown("---")

            st.markdown("📎 **Este relatório pode ser impresso diretamente em PDF.**")

    else:
        st.info("🔔 Faça upload dos 3 arquivos obrigatórios para liberar o dashboard.")
