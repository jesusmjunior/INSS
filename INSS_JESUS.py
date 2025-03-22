import streamlit as st
import pandas as pd
import re
import json
from io import StringIO

# ===================== CONFIG PÁGINA =====================
st.set_page_config(page_title="Dashboard Previdenciário Profissional", layout="wide")

# ===================== LOGIN SIMPLES =====================
def login():
    st.title("🔐 Área Protegida - Login Obrigatório")
    user = st.text_input("Usuário (Email)")
    password = st.text_input("Senha", type="password")

    if user == "jesusmjunior2021@gmail.com" and password == "jr010507":
        st.success("Login efetuado com sucesso ✅")
        return True
    else:
        if user and password:
            st.error("Usuário ou senha incorretos ❌")
        st.stop()  # Para bloquear acesso caso não logado

# ===================== EXECUTA LOGIN =====================
login()

# ===================== FUNÇÕES UTILITÁRIAS =====================
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

# ===================== UPLOAD =====================
st.sidebar.header("🔽 Upload dos Arquivos")
cnis_file = st.sidebar.file_uploader("Upload - CNIS", type=["csv"])
carta_file = st.sidebar.file_uploader("Upload - Carta", type=["csv"])
desconsid_file = st.sidebar.file_uploader("Upload - Desconsiderados", type=["csv"])

aba = st.sidebar.radio("Navegação", ["Dashboard", "Gráficos", "Explicação", "Simulador", "Relatório", "Atualização Monetária", "Relatório Consolidado"])

# ===================== PROCESSAMENTO PRINCIPAL =====================
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

    # ===================== GERAÇÃO DE RELATÓRIO FINAL EM HTML =====================
    if aba == "Relatório Consolidado":
        # Títulos para as caixas de texto
        titulo_input = st.text_area("🔹 Título do Relatório", height=30)
        fundamentacao_input = st.text_area("🔹 Fundamentação do Pedido", height=150)

        # Gerar o relatório em HTML com base nos inputs do usuário
        if titulo_input and fundamentacao_input:
            html_content = f"""
            <html>
            <head>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        margin: 0;
                        padding: 0;
                        width: 100%;
                        box-sizing: border-box;
                    }}
                    .container {{
                        padding: 20px;
                        width: 75%;
                        margin: 0 auto;
                        font-size: 0.8em;
                        line-height: 1.6;
                    }}
                    .title {{
                        text-align: center;
                        font-size: 2em;
                        margin-bottom: 20px;
                    }}
                    .section-title {{
                        font-size: 1.5em;
                        margin-top: 20px;
                        color: #2F4F4F;
                    }}
                    .section-content {{
                        margin: 10px 0;
                        font-size: 1em;
                    }}
                    table {{
                        width: 100%;
                        border-collapse: collapse;
                    }}
                    th, td {{
                        padding: 8px;
                        text-align: left;
                        border: 1px solid #ddd;
                    }}
                    th {{
                        background-color: #f2f2f2;
                    }}
                    .note {{
                        font-style: italic;
                        color: #555;
                    }}
                    .footer {{
                        margin-top: 40px;
                        font-size: 0.9em;
                        text-align: center;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="title">
                        {titulo_input}
                    </div>

                    <div class="section-title">Fundamentação do Pedido</div>
                    <div class="section-content">{fundamentacao_input}</div>

                    <div class="section-title">📊 Dados Consolidado de CNIS</div>
                    <div class="section-content">
                        {df_cnis.to_html(index=False, escape=False)}
                    </div>

                    <div class="section-title">📄 Carta Benefício</div>
                    <div class="section-content">
                        {df_carta.to_html(index=False, escape=False)}
                    </div>

                    <div class="section-title">💰 Salários Desconsiderados</div>
                    <div class="section-content">
                        {df_desconsiderados.to_html(index=False, escape=False)}
                    </div>

                    <div class="footer">
                        📎 **Este relatório pode ser impresso diretamente em PDF.**
                    </div>
                </div>
            </body>
            </html>
            """

            st.markdown(html_content, unsafe_allow_html=True)

            # Botão de impressão
            st.markdown("""
                <div style="text-align:center;">
                    <button onclick="window.print()">🖨️ Imprimir Relatório</button>
                </div>
            """, unsafe_allow_html=True)

        else:
            st.info("👆 Preencha o título e a fundamentação do pedido antes de gerar o relatório.")

    # ===================== OUTRAS ABA =====================
    elif aba == "Dashboard":
        # ... código já existente de dashboard e gráficos
        pass

    elif aba == "Gráficos":
        # ... código já existente de gráficos
        pass

    elif aba == "Simulador":
        # ... código já existente de simulador
        pass

    elif aba == "Relatório":
        # ... código já existente de relatórios
        pass

else:
    st.info("🔔 Faça upload dos 3 arquivos obrigatórios para liberar o dashboard.")
