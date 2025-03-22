import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
import time
import re
from concurrent.futures import ThreadPoolExecutor

st.title("🕸️ Scraper Inteligente - Nome + Tipo Personalizado")

# === Configurações Personalizáveis ===
base_url = st.text_input("🌐 URL do site:", value="https://")
palavra_chave = st.text_input("🔑 Palavra-chave ou parte do nome do arquivo (Regex):", value="certificado")
extensoes = st.text_input("📂 Extensões desejadas (pdf, jpg, mp4, etc):", value="pdf,jpg,mp4")
crawl_profundo = st.checkbox("🌐 Ativar Crawl Profundo?", value=True)
paths_extra = st.text_area("📁 Diretórios adicionais (1 por linha):", "/uploads/\n/files/\n/downloads/")
delay = st.number_input("⏲️ Delay entre requisições:", 0, 5, 1)

DOWNLOADS_DIR = 'arquivos_encontrados'
if not os.path.exists(DOWNLOADS_DIR):
    os.makedirs(DOWNLOADS_DIR)

VISITED = set()

# ==== Funções ====

def testar_caminhos_diretos():
    st.info("🛠️ Testando caminhos diretos...")
    for path in paths_extra.strip().splitlines():
        for ext in extensoes.split(','):
            tentativa = urljoin(base_url, f"{path.strip()}{palavra_chave}.{ext.strip()}")
            try:
                resp = requests.get(tentativa, timeout=10)
                if resp.status_code == 200:
                    st.success(f"🎯 Encontrado direto: {tentativa}")
                    salvar_arquivo(tentativa, resp.content)
            except:
                pass

def salvar_arquivo(url, content):
    filename = os.path.basename(urlparse(url).path)
    with open(os.path.join(DOWNLOADS_DIR, filename), 'wb') as f:
        f.write(content)
    with open(os.path.join(DOWNLOADS_DIR, filename), 'rb') as file:
        st.download_button(f"📥 Download {filename}", file, filename=filename)

def analisar_pagina(url, nivel=1):
    if url in VISITED or nivel > 5:
        return
    try:
        VISITED.add(url)
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        # Busca arquivos que contenham a palavra-chave + extensão
        for tag in soup.find_all('a', href=True):
            href = tag['href']
            full_url = urljoin(url, href)
            if re.search(palavra_chave, href, re.IGNORECASE) and any(href.lower().endswith(ext.strip()) for ext in extensoes.split(',')):
                try:
                    file_resp = requests.get(full_url)
                    if file_resp.status_code == 200:
                        st.success(f"📄 Arquivo encontrado: {full_url}")
                        salvar_arquivo(full_url, file_resp.content)
                except:
                    continue
        # Crawl Profundo
        if crawl_profundo:
            for a in soup.find_all('a', href=True):
                next_link = urljoin(url, a['href'])
                if base_url in next_link:
                    time.sleep(delay)
                    analisar_pagina(next_link, nivel+1)
    except Exception as e:
        st.warning(f"⚠️ Erro em {url}: {str(e)}")

# ==== EXECUÇÃO ====
if st.button("🚀 Iniciar Busca e Download"):
    testar_caminhos_diretos()
    analisar_pagina(base_url)
    st.success("✅ Processo finalizado!")
