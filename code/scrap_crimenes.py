import pandas as pd
from pathlib import Path
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

# function to wait for element to appear
def ingresar(element, espero):
    try:
        element.click()
    except (ElementClickInterceptedException, ElementNotInteractableException):
        try:
            time.sleep(espero)
            element.click()
        except (ElementClickInterceptedException, ElementNotInteractableException) as exp:
            raise exp

# Scraper
def scrap_crimenes(driver, dependencia:str, year:str, secuencial:str, crimenes:list, delay=1, waits=20):
    """
    Scraper for judicial trials, using driver. 
    The function returs a tupple ```results``` which contains generaliteis of the case and 
    the text of sentencia and acta de sorteo
    """

    # Define waits
    wait = WebDriverWait(driver, waits)
    esperar = delay*10

    # Clean session
    wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="form1:butLimpiar"]'))).click()
    time.sleep(delay)

    # Send a query to the main page
    wait.until(EC.presence_of_element_located((By.ID, 'form1:idJuicioJudicatura'))).send_keys(dependencia)
    driver.find_element(By.ID, 'form1:idJuicioAnio').send_keys(year)
    driver.find_element(By.ID, 'form1:idJuicioNumero').send_keys(secuencial)
    ingresar(driver.find_element(By.ID, 'form1:butBuscarJuicios'), esperar)
    time.sleep(delay)

    # See if the process exists
    soup = BeautifulSoup(driver.page_source, 'lxml')
    r = soup.find('tbody', id='form1:dataTableJuicios2_data')

    # Variables to return
    caracteristicas = []

    # Loop over process
    for proceso in r.find_all('tr'):

        if 'No se encuentran' in proceso.text:
            caract = {'id_proceso': dependencia + year + secuencial}
            caract.update({'causa': 'No existe este proceso'})
            return [caract]


        elif proceso.find_all('td')[3].text not in crimenes:
            caract = {'id_proceso': proceso.find_all('td')[2].text}
            caract.update({'causa': proceso.find_all('td')[3].text})
            return [caract]

        else:
            # Open process
            ingresar(driver.find_element(By.ID, proceso.button['id']), esperar)
            time.sleep(delay)

            # Loop over each instance
            page = BeautifulSoup(driver.page_source, 'lxml')
            instancias = page.find('tbody', id='formJuicioDialogo:dataTableMovimiento_data')
            
            for tr in instancias.find_all('tr', class_='ui-widget-content'):
                
                # Open instance
                ingresar(driver.find_element(By.ID, tr.button['id']), esperar)
                time.sleep(delay)
                
                # Get instance page source 
                pg = BeautifulSoup(driver.page_source, 'lxml')

                # Get Generalities about the case
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
                        time.sleep(delay)
                
                # Add unique instancia a resultado
                caracteristicas.append(caract)

                # Regresar
                ingresar(driver.find_element(By.XPATH, '/html/body/div[1]/div[4]/div/div/div[1]/div[1]/a'), esperar)
                time.sleep(delay)

            # Return to procesos page
            ingresar(driver.find_element(By.XPATH, '//*[@id="formJuicioDialogo:btnCancelar"]'), esperar)
            time.sleep(delay)

    return caracteristicas

# Function to extract data from a single process
def juicios(driver, dep_judicial, year, n_attempt, list_crimenes):
    """
    La funcion juicios llama al webscraper y da como resultado un data frame
    que contiene todos los resultados de los juicios 
    """

    # Create id_proceso
    id_proceso = (5-len(str(n_attempt)))*'0' + str(n_attempt)

    # Call function to webscrap
    result_list = scrap_crimenes(driver, dep_judicial, year, id_proceso, list_crimenes, delay=2)

    # Convert results to pandas
    result_df = pd.DataFrame()
    for instancia in result_list:
        result_df = pd.concat([result_df, pd.DataFrame(instancia, index=[0])], ignore_index=True)

    return result_df

# Function to iterate over
def obtener_datos(dflistos, iddep, list_crimenes, ventana=True):
    """
    La funcion toma como argumento un dataframe ```dflistos``` para la
    dependencia judicial ```iddep```. Calcula el ultimo numero de proceso en el
    dataframe, y llama a la funcion de juicios para obtener los datos El
    resultado es un dictionario, en el cual el primer elemento es ul estado =
    {True, False} que define si se acabo ya con todos los procesos de una
    dependencia. Y el segundo elemento es el dataframe con el texto de cada
    proceso

    ventana: Si hago aparecer el browser 
    """


    # 1 - Figure out last id of proceso: If it is the first iteration, start from 2014, and 1
    if dflistos.shape[0] == 0:
        yr_last = 2014
        num_last = 1

    else:
        last_proceso = dflistos['id_proceso'][dflistos.shape[0]-1] 
        yr_last = int(last_proceso[5:9])
        num_last = int(re.sub('\D', '', last_proceso[9:])) + 1

    # 2 - Run Webscraper

    # Define options for browser
    options = webdriver.FirefoxOptions()
    options.headless = ventana # do not show browser window
    options.page_load_strategy = 'none' # Dont wait page to be loaded
    options.set_preference("general.useragent.override", UserAgent().random)

    # Start Driver
    gecko_path = Path.home()/'Documents/geckodriver.exe'
    driver = webdriver.Firefox(executable_path=gecko_path, options=options)
    url = 'http://consultas.funcionjudicial.gob.ec/informacionjudicial/public/informacion.jsf'
    driver.get(url)

    # Define base for results
    results = pd.DataFrame()

    # Loop over years
    for year in range(yr_last, 2021):

        n_start = 1 if year > yr_last else num_last

        # Loop over possible trials
        nfallidos = 0
        for n_attempt in range(n_start, 99999+1):
            try:
                # Scrap the data
                results_df = juicios(driver, iddep, str(year), n_attempt, list_crimenes)
                
                # Check if id_proceso existe
                if 'No existe este proceso' in results_df.causa[0]:
                    nfallidos +=1

                    if nfallidos >=5: 
                        break

                else:
                    results = pd.concat([results, results_df], ignore_index=True)

            except (TypeError, ElementNotInteractableException, StaleElementReferenceException):
                # If we cannot get the data, return the result up to that point
                driver.close()
                print('El proceso se interrumpio, seguir corriendo')
                return {'estado': False, 'df': results}
                
    # If all works good
    driver.close()
    return {'estado': True, 'df': results}