import streamlit as st
import requests
from urllib.parse import urljoin

st.set_page_config(page_title="Busca Automática de Arquivo", layout="centered")

st.title("🔍 Busca Automática de Arquivos Públicos em Sites")

st.write("Preencha os campos abaixo para iniciar a busca:")

# Entrada do site e nome do arquivo
base_url = st.text_input("Digite o URL base do site (ex: https://ava.domalberto.edu.br)", value="https://ava.domalberto.edu.br")
target_file_name = st.text_input("Digite o nome EXATO ou parte do arquivo (ex: certificado.pdf)", value="Ficha de Registro de Certificado")

# Opções padrões de diretórios
default_paths = ['/wp-content/uploads/', '/uploads/certificados/', '/certificados/']
ajax_actions = ['listar_certificados', 'get_certificados', 'baixar_pdf', 'certificados']

# Botão para iniciar busca
if st.button("🚀 Iniciar Busca"):

    st.info("Iniciando buscas...\n")

    # Função tentativa download direto
    def try_direct_download():
        st.write("Tentando download direto via URLs conhecidas...\n")
        for path in default_paths:
            test_url = urljoin(base_url, f"{path}{target_file_name.replace(' ', '%20')}")
            st.write(f"🔗 Testando: {test_url}")
            try:
                resp = requests.get(test_url, timeout=10)
                if resp.status_code == 200 and b'%PDF' in resp.content[:1024]:
                    with open('arquivo_encontrado.pdf', 'wb') as f:
                        f.write(resp.content)
                    st.success(f"✅ Arquivo encontrado e baixado: {test_url}")
                    with open('arquivo_encontrado.pdf', "rb") as file:
                        st.download_button(label="📥 Baixar Arquivo", data=file, file_name='arquivo_encontrado.pdf')
                    return True
            except Exception as e:
                st.warning(f"Erro ao acessar {test_url}: {e}")
        st.error("❌ Nenhuma URL direta localizou o arquivo.\n")
        return False

    # Função testar diretórios
    def try_open_directories():
        st.write("Verificando se diretórios públicos estão acessíveis...\n")
        for path in default_paths:
            dir_url = urljoin(base_url, path)
            st.write(f"🔍 Checando: {dir_url}")
            try:
                resp = requests.get(dir_url, timeout=10)
                if "Index of" in resp.text or '<title>Index' in resp.text:
                    st.success(f"⚠️ Diretório possivelmente aberto: {dir_url}")
                    return True
            except Exception as e:
                st.warning(f"Erro ao acessar {dir_url}: {e}")
        st.error("❌ Nenhum diretório aberto encontrado.\n")
        return False

    # Função testar AJAX
    def try_admin_ajax():
        st.write("Testando possíveis endpoints AJAX...\n")
        ajax_url = urljoin(base_url, '/wp-admin/admin-ajax.php')
        for action in ajax_actions:
            payload = {'action': action}
            st.write(f"🛠️ Testando action: {action}")
            try:
                resp = requests.post(ajax_url, data=payload, timeout=10)
                if resp.status_code == 200 and 'pdf' in resp.text.lower():
                    st.success(f"⚠️ Endpoint público respondeu:\n\n{resp.text[:400]}...")
                    return True
            except Exception as e:
                st.warning(f"Erro no POST action {action}: {e}")
        st.error("❌ Nenhum endpoint AJAX exposto sem login.\n")
        return False

    # EXECUÇÃO DAS FUNÇÕES
    result1 = try_direct_download()
    result2 = try_open_directories()
    result3 = try_admin_ajax()

    if not (result1 or result2 or result3):
        st.error("Nenhum método funcionou. O arquivo pode estar protegido ou em local não acessível publicamente.")
    else:
        st.success("✅ Alguma tentativa obteve sucesso!")

