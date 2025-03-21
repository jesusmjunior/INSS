import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="Dashboard Previdenciário Profissional", layout="wide")

# ================================
# LOGIN SIMPLES
# ================================
def login():
    st.title("🔐 Área Protegida - Login Obrigatório")
    user = st.text_input("Usuário (Email)")
    password = st.text_input("Senha", type="password")

    usuarios = {
        "jesusmjunior2021@gmail.com": "jr010507",
        "joliveiramaccf@gmail.com": "cgti@383679"
    }

    if (user in usuarios and password == usuarios[user]):
        st.success("Login efetuado com sucesso ✅")
        return True
    else:
        if user and password:
            st.error("Usuário ou senha incorretos ❌")
        st.stop()

# EXECUTA LOGIN
login()

# ================================
# UPLOAD CSV
# ================================
st.sidebar.header("🔽 Upload dos Arquivos")
uploaded_file = st.sidebar.file_uploader("Upload do arquivo CSV de salários", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.subheader("Dados Carregados")
    st.dataframe(df)

    st.subheader("Índices Econômicos por Período (Ajustáveis)")
    indices_ano = {
        '1980': st.number_input("Índice 1980-1990", value=5000.0),
        '1990': st.number_input("Índice 1990-1994", value=1000.0),
        '1994': st.number_input("Índice 1994-2000", value=2.75),
        '2000': st.number_input("Índice 2000-2010", value=1.3),
        '2010': st.number_input("Índice 2010-2020", value=1.1),
        '2020': st.number_input("Índice 2020+", value=1.05),
    }

    def atualizar_valor_plano(competencia, salario):
        ano = int(competencia.split('/')[-1])
        if ano < 1990:
            fator = indices_ano['1980']
        elif ano < 1994:
            fator = indices_ano['1990']
        elif ano < 2000:
            fator = indices_ano['1994']
        elif ano < 2010:
            fator = indices_ano['2000']
        elif ano < 2020:
            fator = indices_ano['2010']
        else:
            fator = indices_ano['2020']
        salario_corrigido = salario * fator
        return round(salario_corrigido, 2)

    df['Remuneração Corrigida'] = df.apply(
        lambda row: atualizar_valor_plano(str(row['Competência']), row['Remuneração']), axis=1
    )

    st.subheader("Salários Corrigidos")
    st.dataframe(df[['Competência', 'Remuneração', 'Remuneração Corrigida']])

    salarios_corrigidos = df['Remuneração Corrigida'].dropna().astype(float)
    salarios_ordenados = salarios_corrigidos.sort_values(ascending=False)
    n = int(len(salarios_ordenados) * 0.8)
    media_80 = round(salarios_ordenados.iloc[:n].mean(), 2)

    fator_previdenciario = 0.9322
    salario_beneficio = round(media_80 * fator_previdenciario, 2)

    st.subheader("Resultados")
    st.write(f"**Média dos 80% maiores salários corrigidos:** R$ {media_80:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    st.write(f"**Fator Previdenciário Aplicado:** {fator_previdenciario}")
    st.write(f"**Salário de Benefício Final:** R$ {salario_beneficio:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    log = {
        'Índices Econômicos Aplicados': indices_ano,
        'Média 80%': media_80,
        'Fator Previdenciário': fator_previdenciario,
        'Salário Benefício Final': salario_beneficio
    }
    log_json = json.dumps(log, indent=4)

    st.download_button("Baixar Log Auditável", log_json, file_name="log_auditoria_previdenciario.json")

    # ================================
    # RELATÓRIO FINAL ONLINE
    # ================================
    st.subheader("📄 Relatório Final: Carta de Concessão")
    st.markdown("""
    #### Nome: <NOME>
    #### NIT: <NIT>
    #### APS: <APS>
    #### Benefício: <Número do Benefício>
    #### Data de Concessão: <Data>
    
    Explicação: Apresenta-se abaixo detalhamento dos salários considerados e desconsiderados com observações.
    """)

    st.dataframe(df[['Competência', 'Remuneração', 'Remuneração Corrigida']])

    st.markdown("""
    **Observação:** Valores considerados conforme cálculo realizado. Para campos desconsiderados, verificar tabela anexa.

    **Anexo 1:** Dados CNIS Originais - [Download CSV](Link_CSV_Cnis)

    **Anexo 2:** Dados Desconsiderados - [Download CSV](Link_CSV_Desconsiderados)

    ----

    **Salve também estes arquivos no Google Drive e abra como Google Planilha para controle futuro.**

    **Tutorial Rápido:**
    1. Faça download dos arquivos acima.
    2. Acesse [Google Drive](https://drive.google.com/).
    3. Clique em **Novo** > **Upload de Arquivo**.
    4. Após subir, clique com o botão direito e escolha "Abrir com Google Planilhas".
    5. Salve.
    
    ----
    """)

    # Personalização visual - cabeçalho e bot mascot
    st.markdown("""
    <style>
    .header {font-size:35px; text-align:center; border:1px solid #ccc; padding:10px; background-color:#f0f0f0; margin-bottom:20px;}
    .floating {position: fixed; bottom: 50px; right: 10px; background: #333; color: white; padding: 10px; border-radius: 10px; cursor: pointer;}
    </style>
    <div class="header">Jesus 🤖</div>
    <div class="floating" onclick="window.alert('Fale com Jesus: 98 98304-4543!')">Jesus 📞</div>
    """, unsafe_allow_html=True)

    st.success("Relatório Final gerado e pronto para impressão ou envio digital!")

else:
    st.info("🔔 Faça upload do arquivo de salários para iniciar o cálculo.")
