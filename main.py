import os
import time
import pandas as pd
from typing import List
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from drivers.chrome import selenium_chrome_driver
import dotenv

# TODO: Implementar depois...
def importa_preços(Filename: str) -> List:
    if Filename.endswith(".xlsx"):
        df = pd.read_excel(Filename)
        lista_de_preços = df.values.tolist()
        return lista_de_preços

# Determina Quais lojas vão receber a altreção do produto da lista/excel etc...
def determina_lojas() -> str:
    return "1,2,3" #Lista o nº das filiais atraves do seu numero de cadastro no Visual Store.


def process(
    data_list: List | None, url: str, selenium_webdriver: selenium_chrome_driver
) -> None:

    driver = selenium_webdriver
    # driver.maximize_window()
    driver.get(url)

    # TODO ALterar campos hardcoded de senha e usuario para variaveis de ambiente
    driver.find_element(By.ID, "usuarios").send_keys(VSTORE_USER)
    driver.find_element(By.ID, "senha").send_keys(VSTORE_PASS)
    driver.find_element(By.ID, "btnEnviar").submit()

    try:
        # Opções > Cadastro
        cadastro_menu_hover = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, "/html[1]/body[1]/a[6]/div[1]"))
        )
        cadastro_hover = ActionChains(driver).move_to_element(cadastro_menu_hover)
        cadastro_hover.perform()

        # Opções > Cadastro > Preço Imediato
        preco_imediato_menu_hover = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located(
                (By.XPATH, "/html[1]/body[1]/a[32]/div[1]")
            )
        )
        preco_imediato_hover = ActionChains(driver).move_to_element(
            preco_imediato_menu_hover
        )
        preco_imediato_hover.perform()

        # Opções > Cadastro > Preço Imediato > Clube
        preco_clube_menu_hover = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located(
                (By.XPATH, "/html[1]/body[1]/a[36]/div[1]")
            )
        )
        preco_clube_hover = (
            ActionChains(driver).move_to_element(preco_clube_menu_hover).click()
        )
        preco_clube_hover.perform()
    except Exception as e:
        print(e)
        # Mudando pro Iframe carregado do menu Cadastro > Preço Imediato > Varejo e Promoção
    driver.switch_to.frame("desktop")

    
    # TODO: Implementar os lançamentos de valores a partir de um excel de forma ASSINCRONA (V2)?
    # TODO: Implementar parseamento das entradas de informações (txt, xls e etc..)_
    arquivo = "alteracoes.xlsx"
    local_dir = os.getcwd()
    filepath = os.path.join(local_dir, arquivo)
    dados = pd.read_excel(filepath)
    
    try:
        for _, row in dados.iterrows():
            # Acessando input Produto ID e Enviando tecla ENTER para carrecar o produto e a embalagem
            print(f'ITEM -->{ str(row["CODIGO"])[:-4].strip()}  PRECO --> {str(row["PRECO"]).strip()}') 
            produto_id = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "txtProdutoId"))
            )
            produto_keys = (
                ActionChains(driver)
                .send_keys_to_element(produto_id, str(row["CODIGO"])[:-4])
                .send_keys(Keys.ENTER)
            )
            produto_keys.perform()
            # Incluir as lojas que receberão a alteração:

            list_lojas = determina_lojas()
            input_lojas = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "txtLojas"))
            )
            input_lojas_keys = (
                ActionChains(driver)
                .send_keys_to_element(input_lojas, list_lojas)
                .send_keys(Keys.TAB)
                .send_keys(Keys.SPACE)
            )
            input_lojas_keys.perform()

            list_lojas = list(map(int, list_lojas.split(",")))
            
            for index in range(len(list_lojas)):
                try:
                    tr = WebDriverWait(driver, 2).until(
                        EC.presence_of_element_located((By.ID, f"dtgLista_line{index}"))
                    )
                    tds = tr.find_elements(By.TAG_NAME, "td")
                    tds[2].find_element(By.TAG_NAME, "input").clear()
                    tds[2].find_element(By.TAG_NAME, "input").send_keys(
                        datetime.now().date().strftime("%d/%m/%Y")
                    )
                    tds[3].find_element(By.TAG_NAME, "input").clear()
                    tds[3].find_element(By.TAG_NAME, "input").send_keys(
                        datetime.now().date().strftime("%d/%m/%Y")
                    )
                    tds[4].find_element(By.TAG_NAME, "input").clear()
                    tds[4].find_element(By.TAG_NAME, "input").send_keys(
                        str(row["PRECO"]).lstrip().replace('.', ',')
                    )
                except Exception as e:
                    print(e)
                    continue
            ActionChains(driver).click(driver.find_element(By.NAME, 'btnSalvar')).perform()
            ActionChains(driver).click(driver.find_element(By.NAME, 'cmdOK')).perform()
            ActionChains(driver).click(driver.find_element(By.NAME, 'btnLimpar')).perform()
            
            
    except Exception as e :
        print(f'ITEM: {row["CODIGO"]} --> Exception: {e}')
        
if __name__ == "__main__":

    # Carregando dados do Ambiente:
    dotenv.load_dotenv()

    VSTORE_URL = os.getenv('VSTORE_URL')
    VSTORE_ADM = os.getenv('VSTORE_ADM')
    VSTORE_PORT = os.getenv('VSTORE_PORT')
    VSTORE_USER = os.getenv('VSTORE_USER')
    VSTORE_PASS = os.getenv('VSTORE_PASS')

    url = f"{VSTORE_URL}:{VSTORE_PORT}/{VSTORE_ADM}"
    browser = selenium_chrome_driver()
    process(None, url, browser)
