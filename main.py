import time
from datetime import datetime
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    WebDriverException,
)

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=640,720")

try:
    browser = webdriver.Chrome(options=chrome_options)
    browser.get("https://www.google.com/finance/beta")
    time.sleep(3)
except Exception as e:
    print(f"URL INVÁLIDA ou Erro ao iniciar o navegador ⚠️: {e}")
print("> ACESSANDO GOOGLE FINANCE ...........")
print("########## INICIANDO COLETA ##########")

path_element_value = '//*[@id="yDmH0d"]/c-wiz[3]/div/div/div/div[2]/main/div/div/c-wiz/div/div[3]/c-wiz/div/div/div[1]/div/div[2]/div/div[1]/div[1]/span/span'
path_element_perc = '//*[@id="yDmH0d"]/c-wiz[3]/div/div/div/div[2]/main/div/div/c-wiz/div/div[3]/c-wiz/div/div/div[1]/div/div[2]/div/div[1]/div[2]/span/span'

def get_usd_quote():
    print("> Coletando informações do dolar...")
    time.sleep(2)
    browser.get(r'https://www.google.com/finance/beta/quote/USD-BRL')
    copy_text_usd = None
    copy_text_perc_usd = None
    try:
        time.sleep(3)
        copy_usd = browser.find_element('xpath', path_element_value)
        copy_text_usd = copy_usd.text.strip() or copy_usd.get_attribute("textContent").strip()
        if not copy_usd:
            raise NoSuchElementException("Elemento de cotação de USD não localizado com os seletores disponíveis.")
        print("Cotação Atual do USD(R$):", copy_text_usd)

        copy_perc_usd = browser.find_element('xpath', path_element_perc)
        copy_text_perc_usd = copy_perc_usd.text.strip() or copy_perc_usd.get_attribute("textContent").strip()
        if not copy_perc_usd:
            raise NoSuchElementException("Elemento de percentual de USD não localizado com os seletores disponíveis.")
        print("Percentual atual do USD(%):", copy_text_perc_usd)
        print("##################################")
    
        time.sleep(2)
        
    except NoSuchElementException as e:
        print(f"Erro: Elemento de cotação de USD não localizado. Detalhes: {e}")
    except ElementClickInterceptedException:
        print("Erro: Botão sobreposto na busca de USD.")
    except WebDriverException as e:
        print(f"Erro geral do Selenium ao buscar USD: {e}")
    except Exception as e:
        print(f"Erro inesperado durante a raspagem de USD: {e}")

    return copy_text_usd, copy_text_perc_usd

time.sleep(2)

def get_eur_quote():
    print("> Coletando informações do euro...")
    browser.get(r'https://www.google.com/finance/beta/quote/EUR-BRL')
    copy_text_eur = None
    copy_text_perc_eur = None
    try:
        time.sleep(3)
        copy_eur = browser.find_element('xpath', path_element_value)
        copy_text_eur = copy_eur.text.strip() or copy_eur.get_attribute("textContent").strip()
        if not copy_eur:
            raise NoSuchElementException("Elemento de cotação de USD não localizado com os seletores disponíveis.")
        print("Cotação Atual do EUR(R$):", copy_text_eur)
        
        copy_perc_eur = browser.find_element('xpath',path_element_perc)
        copy_text_perc_eur = copy_perc_eur.text.strip() or copy_perc_eur.get_attribute("textContent").strip()
        if not copy_perc_eur:
            raise NoSuchElementException("Elemento de percentual de USD não localizado com os seletores disponíveis.")
        print("Percentual atual do EUR(%):", copy_text_perc_eur)
        print("##################################")
            
        time.sleep(2)
    except NoSuchElementException as e:
        print(f"Erro: Elemento de cotação de EUR não localizado. Detalhes: {e}")
    except ElementClickInterceptedException:
        print("Erro: Botão sobreposto na busca de EUR.")
    except WebDriverException as e:
        print(f"Erro geral do Selenium ao buscar EUR: {e}")
    except Exception as e:
        print(f"Erro inesperado durante a raspagem de EUR: {e}")
    finally:
        try:
            browser.get("https://www.google.com/finance/beta")
        except Exception as e:
            print(f"Erro ao redirecionar: {e}")
    return copy_text_eur, copy_text_perc_eur

time.sleep(2)

def get_cny_quote():
    print("> Coletando informações do iene ...")
    browser.get(r'https://www.google.com/finance/beta/quote/CNY-BRL')
    copy_text_cny = None
    copy_text_perc_cny = None
    try:
        time.sleep(3)
        copy_cny = browser.find_element('xpath', path_element_value)
        copy_text_cny = copy_cny.text.strip() or copy_cny.get_attribute("textContent").strip()
        if not copy_cny:
            raise NoSuchElementException("Elemento de cotação de USD não localizado com os seletores disponíveis.")
        print("Cotação Atual do CNY(R$):", copy_text_cny)
                
        copy_perc_cny = browser.find_element('xpath',path_element_perc)
        copy_text_perc_cny = copy_perc_cny.text.strip() or copy_perc_cny.get_attribute("textContent").strip()
        if not copy_perc_cny:
            raise NoSuchElementException("Elemento de percentual de USD não localizado com os seletores disponíveis.")
        print("Percentual atual do CNY(%):", copy_text_perc_cny)
        print("##################################")
        
    except NoSuchElementException as e:
        print(f"Erro: Elemento de cotação de CNY não localizado. Detalhes: {e}")
    except ElementClickInterceptedException:
        print("Erro: Botão sobreposto na busca de CNY.")
    except WebDriverException as e:
        print(f"Erro geral do Selenium ao buscar CNY: {e}")
    except Exception as e:
        print(f"Erro inesperado durante a raspagem de CNY: {e}")
    finally:
        try:
            browser.get("https://www.google.com/finance/beta")
        except Exception as e:
            print(f"Erro ao redirecionar: {e}")

    return copy_text_cny, copy_text_perc_cny

time.sleep(2)

def get_btc_quote():
    print("> Coletando informações do bitcoin...")
    browser.get(r'https://www.google.com/finance/beta/quote/BTC-BRL')
    copy_text_btc = None
    copy_text_perc_btc = None
    try:
        time.sleep(3)
        copy_btc = browser.find_element('xpath', path_element_value)
        copy_text_btc = copy_btc.text.strip() or copy_btc.get_attribute("textContent").strip()
        if not copy_btc:
            raise NoSuchElementException("Elemento de cotação de USD não localizado com os seletores disponíveis.")
        print("Cotação Atual do BTC(R$):", copy_text_btc)
        
        copy_perc_btc = browser.find_element('xpath',path_element_perc)
        copy_text_perc_btc = copy_perc_btc.text.strip() or copy_perc_btc.get_attribute("textContent").strip()
        if not copy_perc_btc:
            raise NoSuchElementException("Elemento de percentual de USD não localizado com os seletores disponíveis.")
        print("Percentual atual do EUR(%):", copy_text_perc_btc)
        print("##################################")
        
    except NoSuchElementException as e:
        print(f"Erro: Elemento de cotação de BTC não localizado. Detalhes: {e}")
    except ElementClickInterceptedException:
        print("Erro: Botão sobreposto na busca de BTC.")
    except WebDriverException as e:
        print(f"Erro geral do Selenium ao buscar BTC: {e}")
    except Exception as e:
        print(f"Erro inesperado durante a raspagem de BTC: {e}")
    finally:
        try:
            browser.get("https://www.google.com/finance/beta")
        except Exception as e:
            print(f"Erro ao redirecionar: {e}")

    return copy_text_btc, copy_text_perc_btc

time.sleep(2)

def get_eth_quote():
    print("> Coletando informações do ether...")
    browser.get(r'https://www.google.com/finance/beta/quote/ETH-BRL')
    copy_text_eth = None
    copy_text_perc_eth = None
    try:
        time.sleep(3)
        copy_eth = browser.find_element('xpath', path_element_value)
        copy_text_eth = copy_eth.text.strip() or copy_eth.get_attribute("textContent").strip()
        if not copy_eth:
            raise NoSuchElementException("Elemento de cotação de USD não localizado com os seletores disponíveis.")
        print("Cotação Atual do EUR(R$):", copy_text_eth)
        
        copy_perc_eth = browser.find_element('xpath',path_element_perc)
        copy_text_perc_eth = copy_perc_eth.text.strip() or copy_perc_eth.get_attribute("textContent").strip()
        if not copy_perc_eth:
            raise NoSuchElementException("Elemento de percentual de USD não localizado com os seletores disponíveis.")
        print("Percentual atual do EUR(%):", copy_text_perc_eth)
        print("##################################")

    except NoSuchElementException as e:
        print(f"Erro: Elemento de cotação de ETH não localizado. Detalhes: {e}")
    except ElementClickInterceptedException:
        print("Erro: Botão sobreposto na busca de ETH.")
    except WebDriverException as e:
        print(f"Erro geral do Selenium ao buscar ETH: {e}")
    except Exception as e:
        print(f"Erro inesperado durante a raspagem de ETH: {e}")
    finally:
        try:
            browser.get("https://www.google.com/finance/beta")
        except Exception as e:
            print(f"Erro ao redirecionar: {e}")
    return copy_text_eth, copy_text_perc_eth

def clean_percentage_value(perc_str):
    if not perc_str or pd.isna(perc_str):
        return ""
    s = str(perc_str).replace("%", "").replace("+", "").replace("(", "").replace(")", "").strip()
    if "." in s and "," in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        val = float(s)
        return f"{val:.2f}".replace(".", ",")
    except ValueError:
        return str(perc_str).replace("%", "").replace(".", ",").strip()

def save_quote_by_columns(
    sheet, 
    currency_symbol, 
    value, 
    percentage, 
    expected_headers=None
):

    if expected_headers is None:
        expected_headers = ["DATA", "MOEDA", "COTAÇÃO", "PERCENTUAL"]

    all_values = sheet.get_all_values()
    
    if not all_values:
        sheet.append_row(expected_headers)
        headers = expected_headers
        all_values = [headers]
    else:
        headers = [str(h).strip().upper() for h in all_values[0]]
        
    col_map = {}
    for req_header in expected_headers:
        if req_header in headers:
            col_map[req_header] = headers.index(req_header) + 1
        else:
            new_col_idx = len(headers) + 1
            sheet.update_cell(1, new_col_idx, req_header)
            headers.append(req_header)
            col_map[req_header] = new_col_idx
    next_row = len(all_values) + 1
    current_date = datetime.now().strftime("%d/%m/%Y")
    row_data = {
        "DATA": current_date,
        "MOEDA": currency_symbol,
        "COTAÇÃO": value,
        "PERCENTUAL": clean_percentage_value(percentage)
    }
    for header, col_idx in col_map.items():
        val = row_data.get(header, "")
        sheet.update_cell(next_row, col_idx, val)

    print(f" Dados da moeda '{currency_symbol}'✅")


credencial_json = r"API JSON"
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

try:
    creds = ServiceAccountCredentials.from_json_keyfile_name(credencial_json, scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open("quote_db")
    sheet = spreadsheet.sheet1
except Exception as e:
    print(f"Erro de autenticação/conexão com Google Sheets: {e}")
    sheet = None


if __name__ == "__main__":
    value_usd, var_usd = get_usd_quote()
    time.sleep(5)

    value_eur, var_eur = get_eur_quote()
    time.sleep(5)

    # Coleta cotação do Yuan Chinês
    value_cny, var_cny = get_cny_quote()
    time.sleep(5)

    # Coleta cotação do Bitcoin
    value_btc, var_btc = get_btc_quote()
    time.sleep(5)

    # Coleta cotação do Ether
    value_eth, var_eth = get_eth_quote()
    time.sleep(2)

    browser.quit()

    if sheet:
        # Insere dados do Dólar (USD)
        if value_usd:
            save_quote_by_columns(
                sheet=sheet,
                currency_symbol="USD",
                value=value_usd,
                percentage=var_usd
            )
        
        # Insere dados do Euro (EUR)
        if value_eur:
            save_quote_by_columns(
                sheet=sheet,
                currency_symbol="EUR",
                value=value_eur,
                percentage=var_eur
            )
        
        # Insere dados do Yuan Chinês (CNY)
        if value_cny:
            save_quote_by_columns(
                sheet=sheet,
                currency_symbol="CNY",
                value=value_cny,
                percentage=var_cny
            )

        # Insere dados do Bitcoin (BTC)
        if value_btc:
            save_quote_by_columns(
                sheet=sheet,
                currency_symbol="BTC",
                value=value_btc,
                percentage=var_btc
            )

        # Insere dados do Ether (ETH)
        if value_eth:
            save_quote_by_columns(
                sheet=sheet,
                currency_symbol="ETH",
                value=value_eth,
                percentage=var_eth
            )
        
        # Exibe os dados atualizados como DataFrame no terminal
        data_updated = sheet.get_all_records()
        df = pd.DataFrame(data_updated)
        print("\n--- Tabela Atualizada no Google Sheets ---")
        print(df)
