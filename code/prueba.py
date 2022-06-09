import pandas as pd
from pathlib import Path
from pyprojroot import here
import sys
import warnings
import re


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


# Load scraper
sys.path.insert(1, (root/'code').as_posix())
warnings.filterwarnings("ignore", category=DeprecationWarning)
from scrap_crimenes import obtener_datos
from scrap_crimenes import scrap_crimenes


### Prueba
iddep = '09266'
year = '2015'
sec = '0001'

# Obtener listado de crimenes
delitos = pd.read_csv(proc/'lista_delitos.csv')
delitos = list(delitos['NOMBRE DELITO'])


# 2 - Run Webscraper

# Define options for browser
options = webdriver.FirefoxOptions()
options.headless = False # True= do not show browser window
options.page_load_strategy = 'none' # Dont wait page to be loaded
#options.set_preference("general.useragent.override", UserAgent().random)

# Start Driver
gecko_path = Path.home()/'Documents/geckodriver.exe'
url = 'http://consultas.funcionjudicial.gob.ec/informacionjudicial/public/informacion.jsf'


driver = webdriver.Firefox(executable_path=gecko_path, options=options)
driver.get(url)
res_dict = scrap_crimenes(driver, iddep, str(year), sec, delitos, delay=2)


general_dict = {key: res_dict[key] for key in ['id_proceso', 'causa']}


resumen = pd.DataFrame()

for res in res_dict:               
    # Split the dict between estado del caso y datos para guardar
    general_dict = {key: [res[key]] for key in ['id_proceso', 'causa']}
    docs_dict = res.copy()
    docs_dict.pop('causa', None)
    
    # Save resumen
    resumen=pd.concat([resumen, pd.DataFrame(general_dict)], ignore_index=True)


res_dict[0]