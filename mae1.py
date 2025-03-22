import streamlit as st
import requests
from urllib.parse import urljoin

# CONFIGURAÇÃO
BASE_URL = 'https://ava.domalberto.edu.br'
DOC_PAGE = f'{BASE_URL}/solicitacao-de-documentos/'

UPLOADS_PATHS = [
    '/wp-content/uploads/',
    '/uploads/certificados/',
    '/certificados/',
]

TARGET_FILE_NAME = 'Ficha de Registro de Certificado - DOM (atualizada) - ROSEMARY SANTOS RODRIGUES OLIVEIRA - ANDRAGOGIA E FORMAÇÃO DE ADULTOS - 750 HORAS.pdf'

# Função para tentar download direto via URLs previsíveis
def try_direct_download():
    st.write("Tentando download direto via URLs conhecidas...\n")
    for path in UPLOADS_PATHS:
        test_url = urljoin(BASE_URL, f"{path}{TARGET_FILE_NAME.replace(' ', '%20')}")
        st.write(f"🔗 Testando: {test_url}")
        resp = requests.get(test_url)
        if resp.status_code == 200 and b'%PDF' in resp.content[:1024]:
            with open('certificado_rosemary.pdf', 'wb') as f:
                f.write(resp.content)
            st.success(f"✅ Certificado encontrado e baixado: {test_url}")
            with open('certificado_rosemary.pdf', "rb") as file:
                st.download_button(label="📥 Baixar Certificado", data=file, file_name='certificado_rosemary.pdf')
            return True
    st.error("❌ Nenhuma URL direta localizou o arquivo.\n")
    return False

# Função para verificar diretórios públicos
def try_open_directories():
    st.write("Verificando se diretórios públicos estão acessíveis...\n")
    for path in UPLOADS_PATHS:
        dir_url = urljoin(BASE_URL, path)
        st.write(f"🔍 Checando: {dir_url}")
        resp = requests.get(dir_url)
        if "Index of" in resp.text or '<title>Index' in resp.text:
            st.success(f"⚠️ Diretório possivelmente aberto: {dir_url}")
            return True
    st.error("❌ Nenhum diretório aberto encontrado.\n")
    return False

# Função para testar endpoints AJAX expostos
def try_admin_ajax():
    st.write("Testando possíveis endpoints AJAX...\n")
    ajax_url = urljoin(BASE_URL, '/wp-admin/admin-ajax.php')
    actions = ['listar_certificados', 'get_certificados', 'baixar_pdf', 'certificados']
    for action in actions:
        payload = {'action': action}
        st.write(f"🛠️ Testando action: {action}")
        resp = requests.post(ajax_url, data=payload)
        if resp.status_code == 200 and 'pdf' in resp.text.lower():
            st.success(f"⚠️ Endpoint público respondeu:\n\n{resp.text[:400]}...")
            return True
    st.error("❌ Nenhum endpoint AJAX exposto sem login.\n")
    return False

# APP Streamlit
st.title("🔎 Busca Automática de Certificado - DOM Alberto")

st.write("Este app tenta localizar e baixar seu certificado sem necessidade de login, testando caminhos públicos possíveis.")

if st.button("🔍 Buscar Certificado"):
    st.write("Iniciando buscas...\n")

    result1 = try_direct_download()
    result2 = try_open_directories()
    result3 = try_admin_ajax()

    if not (result1 or result2 or result3):
        st.error("Nenhum método funcionou. O certificado pode estar protegido por login.")
    else:
        st.success("✅ Alguma tentativa retornou resultado!")

