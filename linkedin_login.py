from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import subprocess

# Seus dados de login
EMAIL = "jef.rsd.contato@gmail.com"
PASSWORD = "mLadro1T"

# Abre o navegador Chrome
driver = webdriver.Chrome()

# Acessa a página de login do LinkedIn
driver.get("https://www.linkedin.com/login")
time.sleep(2)

# Preenche o campo de e-mail
driver.find_element(By.ID, "username").send_keys(EMAIL)

# Preenche o campo de senha
driver.find_element(By.ID, "password").send_keys(PASSWORD)

# Clica no botão de login
driver.find_element(By.XPATH, "//button[@type='submit']").click()
time.sleep(3)

# Aguarda confirmação manual
input("✅ Login enviado. Verifique o acesso no navegador e pressione ENTER para continuar...")

# Fecha o navegador (opcional — pode comentar se quiser manter aberto)
# driver.quit()

# Chama o script de busca de vagas
print("🚀 Iniciando busca de vagas...")
subprocess.run(["python", "busca_vagas_linkedin.py"])
