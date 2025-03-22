import streamlit as st
import requests
from urllib.parse import urljoin

# CONFIG
BASE_URL = 'https://ava.domalberto.edu.br'
DOC_PAGE = f'{BASE_URL}/solicitacao-de-documentos/'

UPLOADS_PATHS = [
    '/wp-content/uploads/',
    '/uploads/certificados/',
    '/certificados/',
]

TARGET_FILE_NAME = 'Ficha de Registro de Certificado - DOM (atualizada) - ROSEMARY SANTOS RODRIGUES OLIVEIRA - ANDRAGOGIA E FORMAÇÃO DE ADULTOS - 750 HORAS.pdf'


# Função para tentar download direto via URL conhecida
def try_direct_download():
    st.info("Tentando download direto via URLs conhecidas...")
    for path in UPLOADS_PATHS:
        test_url = urljoin(BASE_URL, f"{path}{TARGET_FILE_NAME.replace(' ', '%20')}")
        st.write(f"🔗 Testando: {test_url}")
        resp = requests.get(test_url)
        if resp.status_code == 200 and b'%PDF' in resp.content[:1024]:
            with open('certificado_encontrado.pdf', 'wb') as f:
                f.write(resp.content)
            st.success(f"✅ Certificado encontrado e baixado: {test_url}")
            with open('certificado_encontrado.pdf', "rb") as file:
                st.download_button(label="📥 Baixar Certificado", data=file, file_name='certificado_rosemary.pdf')
            return True
    st.warning("❌ Nenhuma URL direta localizou o arquivo.")
    return False


# Função para tentar acesso ao admin-ajax.php sem autenticação
def try_admin_ajax():
    st.info("Testando possíveis endpoints AJAX...")
    ajax_url = urljoin(BASE_URL, '/wp-admin/admin-ajax.php')
    actions = ['listar_certificados', 'get_certificados', 'baixar_pdf', 'certificados']
    for action in actions:
        payload = {'action': action}
        st.write(f"🛠️ Testando action: `{action}`")
        resp = requests.post(ajax_url, data=payload)
        if resp.status_code == 200 and 'pdf' in resp.text.lower():
            st.success(f"⚠️ Endpoint público respondeu com sucesso!\n\n{resp.text[:400]}...")
            return True
    st.warning("❌ Nenhum endpoint AJAX exposto sem login.")
    return False


# Função para testar diretórios abertos
def try_open_directories():
    st.info("Verificando se diretórios públicos estão acessíveis...")
    for path in UPLOADS_PATHS:
        dir_url = urljoin(BASE_URL, path)
        st.write(f"🔍 Checando: {dir_url}")
        resp = requests.get(dir_url)
        if "Index of" in resp.text or '<title>Index' in resp.text:
            st.success(f"⚠️ Diretório possivelmente aberto: {dir_url}")
            return True
    st.warning("❌ Nenhum diretório aberto encontrado.")
    return False


# === STREAMLIT APP ===
st.title("🔎 Busca Automática de Certificado - DOM Alberto")

st.write("Este app tenta localizar e baixar seu certificado sem necessidade de login, usando métodos diretos e públicos.")

if st.button("🔍 Buscar Certificado"):
    st.write("Iniciando buscas...")
    result1 = try_direct_download()
    result2 = try_open_directories()
    result3 = try_admin_ajax()

    if not (result1 or result2 or result3):
        st.error("Nenhum método funcionou. O certificado pode estar protegido por login.")
    else:
        st.success("✅ Alguma tentativa obteve resultado! Verifique acima.")

