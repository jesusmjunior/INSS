import streamlit as st
import requests
from urllib.parse import urljoin, urlparse
from html.parser import HTMLParser
import os
import time
import re

# === STREAMLIT CONFIG ===
st.title("🕸️ Scraper Nativo - Nome & Extensão Configuráveis")

st.write("🔧 Configure abaixo e encontre arquivos diretamente ou via links do site.")

# Entradas do Usuário
base_url = st.text_input("🌐 URL base do site:", value="https://")
palavra_chave = st.text_input("🔑 Palavra-chave ou nome do arquivo (regex):", value="certificado")
extensoes = st.text_input("📂 Extensões desejadas (pdf,jpg,mp4):", value="pdf,jpg,mp4")
crawl_profundo = st.checkbox("🌐 Crawl Profundo (links internos)?", value=True)
paths_extra = st.text_area("📁 Diretórios adicionais (1 por linha):", "/uploads/\n/files/\n/downloads/")
delay = st.number_input("⏲️ Delay entre requisições (segundos):", 0, 5, 1)

# Estrutura para salvar
DOWNLOADS_DIR = 'arquivos_encontrados'
if not os.path.exists(DOWNLOADS_DIR):
    os.makedirs(DOWNLOADS_DIR)

VISITED = set()

# ==== FUNÇÃO SALVAR ====
def salvar_arquivo(url, content):
    filename = os.path.basename(urlparse(url).path)
    path = os.path.join(DOWNLOADS_DIR, filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(content)
    with open(path, 'rb') as file:
        st.download_button(f"📥 Baixar {filename}", file, filename=filename)

# ==== PARSER NATIVO ====
class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        for attr in attrs:
            if attr[0] == 'href' or attr[0] == 'src':
                self.links.append(attr[1])

# ==== TENTAR CAMINHOS DIRETOS ====
def testar_caminhos_diretos():
    st.info("🚀 Testando caminhos diretos conhecidos...")
    for path in paths_extra.strip().splitlines():
        for ext in extensoes.split(','):
            tentativa = urljoin(base_url, f"{path.strip()}{palavra_chave}.{ext.strip()}")
            try:
                resp = requests.get(tentativa, timeout=10)
                if resp.status_code == 200:
                    st.success(f"🎯 Arquivo encontrado diretamente: {tentativa}")
                    salvar_arquivo(tentativa, resp.content)
            except:
                pass

# ==== ANALISAR PÁGINA ====
def analisar_pagina(url, nivel=1):
    if url in VISITED or nivel > 5:
        return
    try:
        VISITED.add(url)
        resp = requests.get(url, timeout=10)
        parser = LinkParser()
        parser.feed(resp.text)

        # Busca arquivos matching
        for link in parser.links:
            full_url = urljoin(url, link)
            if re.search(palavra_chave, link, re.IGNORECASE) and any(link.lower().endswith(ext.strip()) for ext in extensoes.split(',')):
                try:
                    file_resp = requests.get(full_url)
                    if file_resp.status_code == 200:
                        st.success(f"📄 Arquivo localizado: {full_url}")
                        salvar_arquivo(full_url, file_resp.content)
                except:
                    continue

        # Crawl Profundo
        if crawl_profundo:
            for link in parser.links:
                next_link = urljoin(url, link)
                if base_url in next_link:
                    time.sleep(delay)
                    analisar_pagina(next_link, nivel+1)

    except Exception as e:
        st.warning(f"⚠️ Erro ao acessar {url}: {str(e)}")

# ==== EXECUÇÃO PRINCIPAL ====
if st.button("🚀 Iniciar Busca"):
    testar_caminhos_diretos()
    analisar_pagina(base_url)
    st.success("✅ Processo finalizado!")

