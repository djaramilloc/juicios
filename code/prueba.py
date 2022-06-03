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

# Set Paths
root = here()
db = root/'data'

# Load scraper
sys.path.insert(1, (root/'code').as_posix())
warnings.filterwarnings("ignore", category=DeprecationWarning)
from scrap_crimenes import obtener_datos
from scrap_crimenes import ingresar


gecko_path = Path.home()/'Documents/geckodriver.exe'
driver = webdriver.Firefox(executable_path=gecko_path)
url = 'http://consultas.funcionjudicial.gob.ec/informacionjudicial/public/informacion.jsf'
driver.get(url)

wait = WebDriverWait(driver, 20)
esperar = 2*10

wait.until(EC.presence_of_element_located((By.ID, 'form1:idJuicioJudicatura'))).send_keys('17294')
driver.find_element(By.ID, 'form1:idJuicioAnio').send_keys('2016')
driver.find_element(By.ID, 'form1:idJuicioNumero').send_keys('00080')
ingresar(driver.find_element(By.ID, 'form1:butBuscarJuicios'), esperar)

soup = BeautifulSoup(driver.page_source, 'lxml')
r = soup.find('tbody', id='form1:dataTableJuicios2_data')

proceso =  r.find('tr')

ingresar(driver.find_element(By.ID, proceso.button['id']), esperar)

page = BeautifulSoup(driver.page_source, 'lxml')
instancias = page.find('tbody', id='formJuicioDialogo:dataTableMovimiento_data')

tr_all = instancias.find_all('tr', class_='ui-widget-content')
tr = tr_all[1]

ingresar(driver.find_element(By.ID, tr.button['id']), esperar)
pg = BeautifulSoup(driver.page_source, 'lxml')

caract = {}
general = pg.find('table', id='formJuicioDetalle:j_idt73').tbody
for index, tr in enumerate(general):
    td = tr.find_all('td', class_='ui-panelgrid-cell descripcion')
    if index == 0:
        caract.update({'id_proceso': td[0].text})
    elif index == 1:
        caract.update({'causa': td[1].text})
    elif index == 2:
        caract.update({'demandante': td[0].text})
        caract.update({'demandado': td[1].text})

#Si tiene solo una pagina
if pg.find('span', class_='ui-paginator-pages') is None:
    
    actos = pg.find('tbody', id='formJuicioDetalle:dataTable_data')
    for tr_actos in actos.find_all('tr'):
        if tr_actos.legend is not None:
            if ('SORTEO' in tr_actos.legend.text) & ('PERITO' not in tr_actos.legend.text):
                caract.update({'fecha_sorteo': tr_actos.td.text})
                caract.update({'sorteo': (tr_actos.div.text).lstrip('\n').rstrip('\n')})

            elif 'SENTENCIA' in tr_actos.legend.text:
                caract.update({'fecha_sentencia': tr_actos.td.text})
                caract.update({'sentencia': (tr_actos.div.text).lstrip('\n').rstrip('\n')})

            elif 'RESOLUC' in tr_actos.legend.text:
                caract.update({'fecha_resolucion': tr_actos.td.text})
                caract.update({'resolucion': (tr_actos.div.text).lstrip('\n').rstrip('\n')})

# Si tiene varias paginas, loop sobre todas
else:
    npag = len(pg.find('span', class_='ui-paginator-pages'))
    ingresar(driver.find_element(By.CSS_SELECTOR, "a.ui-paginator-page:nth-child(1)"), esperar)
    time.sleep(delay)

    for j in range(npag):
        # Get text of sorteo y sentencia
        pg = BeautifulSoup(driver.page_source, 'lxml')
        actos = pg.find('tbody', id='formJuicioDetalle:dataTable_data')
        
        for tr_actos in actos.find_all('tr'):
            if tr_actos.legend is not None:
                if ('SORTEO' in tr_actos.legend.text) & ('PERITO' not in tr_actos.legend.text):
                    caract.update({'fecha_sorteo': tr_actos.td.text})
                    caract.update({'sorteo': (tr_actos.div.text).lstrip('\n').rstrip('\n')})
                
                elif 'SENTENCIA' in tr_actos.legend.text:
                    caract.update({'fecha_sentencia': tr_actos.td.text})
                    caract.update({'sentencia': (tr_actos.div.text).lstrip('\n').rstrip('\n')})

                elif 'RESOLUC' in tr_actos.legend.text:
                    caract.update({'fecha_resolucion': tr_actos.td.text})
                    caract.update({'resolucion': (tr_actos.div.text).lstrip('\n').rstrip('\n')})

        # Change page
        ingresar(driver.find_element(By.CSS_SELECTOR, '.ui-icon-seek-next'), esperar)    

ingresar(driver.find_element(By.XPATH, '/html/body/div[1]/div[4]/div/div/div[1]/div[1]/a'), esperar)
