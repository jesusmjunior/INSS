import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os

# === STREAMLIT APP ===
st.title("🔎 Scraper Automático Fuzzy - Multi Site")

# Entrada para URL Base
base_url = st.text_input("🌐 Digite a URL do site alvo (ex: https://exemplo.com):", value="https://")
# Entrada para extensões de arquivo desejadas
extensoes = st.text_input("📂 Extensões de arquivo desejadas (separadas por vírgula, ex: pdf,jpg,png):", value="pdf")
# Entrada para TAG HTML específica
tags = st.text_input("🏷️ Tags HTML alvo (separadas por vírgula, ex: img,a):", value="")

# Função para buscar links de arquivos com extensões desejadas
def buscar_links(url, exts):
    try:
        st.info(f"🔍 Acessando {url}...")
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        links = []
        for link_tag in soup.find_all('a', href=True):
            href = link_tag['href']
            if any(href.lower().endswith(f".{ext.strip()}") for ext in exts.split(',')):
                full_link = urljoin(url, href)
                links.append(full_link)
        return links
    except Exception as e:
        st.error(f"❌ Erro ao acessar {url}: {str(e)}")
        return []

# Função para buscar tags HTML específicas
def buscar_tags(url, tags):
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        resultado = {}
        for tag in tags.split(','):
            resultado[tag] = soup.find_all(tag.strip())
        return resultado
    except Exception as e:
        st.error(f"❌ Erro ao acessar {url}: {str(e)}")
        return {}

# Função para baixar arquivos encontrados
def baixar_arquivos(links):
    for link in links:
        try:
            filename = os.path.basename(urlparse(link).path)
            st.write(f"⬇️ Baixando: {filename}")
            resp = requests.get(link, timeout=10)
            with open(filename, 'wb') as f:
                f.write(resp.content)
            with open(filename, 'rb') as file:
                st.download_button(label=f"📥 Download {filename}", data=file, file_name=filename)
        except Exception as e:
            st.warning(f"❌ Falha ao baixar {link}: {str(e)}")

# EXECUÇÃO
if st.button("🔍 Iniciar Busca"):
    if not base_url.startswith('http'):
        st.error("Por favor, insira uma URL válida!")
    else:
        # Buscar links de arquivos
        links_encontrados = buscar_links(base_url, extensoes)
        if links_encontrados:
            st.success(f"✅ {len(links_encontrados)} arquivos encontrados!")
            baixar_arquivos(links_encontrados)
        else:
            st.warning("Nenhum arquivo encontrado com as extensões fornecidas.")

        # Buscar tags HTML
        if tags.strip():
            tags_result = buscar_tags(base_url, tags)
            for tag_name, elementos in tags_result.items():
                st.write(f"🔖 {len(elementos)} elementos <{tag_name}> encontrados:")
                for el in elementos[:10]:  # Limita preview
                    st.code(str(el))
