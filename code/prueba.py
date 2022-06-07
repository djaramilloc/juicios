from lib2to3.pgen2.parse import ParseError
import pandas as pd
from pathlib import Path
from pyprojroot import here
import sys
import warnings

import time
from selenium import webdriver
from bs4 import BeautifulSoup

from fake_useragent import UserAgent

from selenium.common.exceptions import ElementNotInteractableException
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# Definir paths
root = here()
raw = root/'data/raw'
proc = root/'data/proc'


### Prueba
iddep = '09100'
year = '2010'
sec = '001'



# 2 - Run Webscraper

# Define options for browser
options = webdriver.FirefoxOptions()
options.headless = False # True= do not show browser window
options.page_load_strategy = 'none' # Dont wait page to be loaded
#options.set_preference("general.useragent.override", UserAgent().random)

# Start Driver
gecko_path = Path.home()/'Documents/geckodriver.exe'
driver = webdriver.Firefox(executable_path=gecko_path, options=options)
url = 'http://consultas.funcionjudicial.gob.ec/informacionjudicial/public/informacion.jsf'
driver.get(url)

driver.find_element(By.ID, 'form1:idJuicioJudicatura').send_keys(iddep)
driver.find_element(By.ID, 'form1:idJuicioAnio').send_keys(year)
driver.find_element(By.ID, 'form1:idJuicioNumero').send_keys(sec)
driver.find_element(By.ID, 'form1:butBuscarJuicios').click()

# Get data
soup = BeautifulSoup(driver.page_source, 'lxml')
r = soup.find('tbody', id='form1:dataTableJuicios2_data')

# Obtain results
if 'No se encuentran' in r.text:
    resultsdf = pd.DataFrame([r.text], columns=['descripcion'])
    resultsdf['causa'] = iddep + year + sec


else:

    # Save results in a list
    res = []

    # Loop over items
    for proc in r.contents:

        tx = proc.text.split('\n', 1)[0]
        tx = tx.rstrip(' ')
        res.append(tx)

    result_df = pd.DataFrame()
    for instancia in res:
        ins_df = pd.DataFrame([instancia], columns=['descripcion'])
        result_df = pd.concat([result_df, ins_df], ignore_index=True)



dflistos = pd.read_csv(proc/'resumenes/by_judicatura/nombres_09351.csv')

last_proceso = str(dflistos['causa'][dflistos.shape[0]-1])
year0 = int(last_proceso[4:8])
sec0 = int(last_proceso[-3:])
