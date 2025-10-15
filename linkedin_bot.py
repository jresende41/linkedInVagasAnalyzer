import pandas as pd
import csv
import time
import os
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# === CONFIGURAÇÕES ===
CHROME_PROFILE_PATH = "C:/LinkedInBot/ChromeProfile"
LOCALIZACAO = "Bragança Paulista, SP"
ARQUIVO_CSV = "relatorioVagas.csv"

# === INICIA NAVEGADOR COM PERFIL PERSISTENTE ===
options = Options()
options.add_argument(f"user-data-dir={CHROME_PROFILE_PATH}")
driver = webdriver.Chrome(options=options)

# === CARREGA IDs JÁ SALVOS (se houver) ===
ids_coletados = set()
if os.path.exists(ARQUIVO_CSV):
    try:
        with open(ARQUIVO_CSV, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                link = row.get("Link", "").strip()
                match = re.search(r"/view/(\d+)", link)
                if match:
                    ids_coletados.add(match.group(1))
    except Exception as e:
        print(f"⚠️ Erro ao ler IDs existentes: {e}")

# === PREPARA ARQUIVO CSV (se não existir) ===
if not os.path.exists(ARQUIVO_CSV):
    with open(ARQUIVO_CSV, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Palavra-chave", "Título", "Empresa", "Localização", "Tipo de trabalho", "Link"])

# === LÊ PALAVRAS-CHAVE ===
palavras_df = pd.read_csv("palavrasChaveBuscaVagas.csv", encoding="utf-8")
total_salvo = len(ids_coletados)

# === LOOP DE BUSCA ===
for index, row in palavras_df.iterrows():
    termo = row.iloc[0]
    print(f"\n🔍 Buscando vagas para: {termo}")

    base_url = f"https://www.linkedin.com/jobs/search/?keywords={termo.replace(' ', '%20')}&location={LOCALIZACAO.replace(' ', '%20')}"
    driver.get(base_url)
    time.sleep(5)

    pagina_atual = 1
    paginas_visitadas = set()

    while True:
        # === ROLA O PAINEL LATERAL SUAVEMENTE ===
        try:
            painel_vagas = driver.find_element(By.CSS_SELECTOR, "#main > div > div.scaffold-layout__list-detail-inner.scaffold-layout__list-detail-inner--grow > div.scaffold-layout__list > div")
        except:
            print("⚠️ Painel de vagas não encontrado.")
            break

        ultimo_total = 0
        tentativas = 0
        passo = 500

        while tentativas < 5:
            driver.execute_script("arguments[0].scrollBy(0, arguments[1])", painel_vagas, passo)
            time.sleep(1)
            vagas = painel_vagas.find_elements(By.CSS_SELECTOR, "div.job-card-container")
            atual_total = len(vagas)

            if atual_total == ultimo_total:
                tentativas += 1
            else:
                tentativas = 0
                ultimo_total = atual_total

        print(f"📄 Página {pagina_atual}: {len(vagas)} vagas visíveis")

        salvos_nesta_pagina = 0

        for vaga in vagas:
            try:
                titulo_element = vaga.find_element(By.CSS_SELECTOR, "a.job-card-container__link.job-card-list__title--link")
                titulo = titulo_element.text.strip()
                link = titulo_element.get_attribute("href").strip()

                match = re.search(r"/view/(\d+)", link)
                if not match:
                    continue
                id_vaga = match.group(1)

                if id_vaga in ids_coletados:
                    continue  # descarta a vaga inteira
                ids_coletados.add(id_vaga)

                empresa = vaga.find_element(By.CSS_SELECTOR, "div.artdeco-entity-lockup__subtitle span").text.strip()
                local = vaga.find_element(By.CSS_SELECTOR, "ul.job-card-container__metadata-wrapper li span").text.strip()

                tipo_trabalho = "Não identificado"
                if "Remoto" in local:
                    tipo_trabalho = "Remoto"
                elif "Híbrido" in local:
                    tipo_trabalho = "Híbrido"
                elif "Presencial" in local:
                    tipo_trabalho = "Presencial"

                with open(ARQUIVO_CSV, mode="a", newline="", encoding="utf-8") as file:
                    writer = csv.writer(file)
                    writer.writerow([termo, titulo, empresa, local, tipo_trabalho, link])
                    salvos_nesta_pagina += 1
                    total_salvo += 1

            except Exception as e:
                print(f"⚠️ Erro ao extrair vaga: {e}")

        print(f"✅ Página {pagina_atual}: {salvos_nesta_pagina} vagas salvas | Total acumulado: {total_salvo}")
        paginas_visitadas.add(pagina_atual)

        # === VERIFICA SE HÁ MAIS PÁGINAS ===
        try:
            botoes = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Página')]")
            botoes_validos = [btn for btn in botoes if btn.text.isdigit()]
            paginas_disponiveis = sorted(set(int(btn.text) for btn in botoes_validos))

            proxima = next((p for p in paginas_disponiveis if p not in paginas_visitadas), None)

            if proxima:
                for btn in botoes_validos:
                    if btn.text == str(proxima):
                        driver.execute_script("arguments[0].click();", btn)
                        time.sleep(5)
                        pagina_atual = proxima
                        break
            else:
                break

        except Exception as e:
            print(f"⚠️ Erro ao navegar para próxima página: {e}")
            break

driver.quit()
print(f"\n✅ Busca finalizada. Total de vagas salvas: {total_salvo}")
