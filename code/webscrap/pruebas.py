import pandas as pd
from pathlib import Path

import time
from bs4 import BeautifulSoup
from selenium import webdriver

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Define options for browser
options = webdriver.FirefoxOptions()
#options.headless = True # do not show browser window
#options.page_load_strategy = 'none' # Dont wait page to be loaded

# Start Driver
gecko_path = 'C:/Users/DanielJaramillo/Documents/geckodriver.exe'
driver = webdriver.Firefox(executable_path=gecko_path, options=options)
url = 'http://consultas.funcionjudicial.gob.ec/informacionjudicial/public/informacion.jsf'
driver.get(url)

wait = WebDriverWait(driver, 10)
delay = 1

for i in range(1, 10):

    wait.until(EC.presence_of_element_located((By.ID, 'form1:idJuicioJudicatura'))).send_keys('09100')
    driver.find_element(By.ID, 'form1:idJuicioAnio').send_keys('2019')
    driver.find_element(By.ID, 'form1:idJuicioNumero').send_keys('0000' + str(i))
    driver.find_element(By.ID, 'form1:butBuscarJuicios').click()

    time.sleep(delay)
    soup = BeautifulSoup(driver.page_source, 'lxml')
    r = soup.find('tbody', id='form1:dataTableJuicios2_data')

    proceso = r.find('tr')
    driver.find_element(By.ID, proceso.button['name']).click()
    time.sleep(delay)


    driver.find_element(By.XPATH, '//*[@id="formJuicioDialogo:btnCancelar"]').click()
    time.sleep(delay)

    driver.find_element(By.XPATH, '//*[@id="form1:butLimpiar"]').click()

