from attr import Attribute
import pandas as pd
from pathlib import Path
import re
import difflib

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
    except (ElementClickInterceptedException, ElementNotInteractableException, StaleElementReferenceException):
        try:
            time.sleep(espero)
            element.click()
        except (ElementClickInterceptedException, ElementNotInteractableException, StaleElementReferenceException) as exp:
            raise exp

# Scraper
def scrap_crimenes(driver, dependencia:str, year:str, secuencial:str, crimenes:list, delay=1, waits=20):
    """
    Scraper for judicial trials, using driver. 
    The function returs a tupple ```results``` which contains generaliteis of the case and 
    the text of sentencia and acta de sorteo.
    the output is a list with all the relevant information
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

        else:
            # Get infraccion name
            infraccion = proceso.find_all('td')[3].text.rstrip(' ')
            in_delitos = difflib.get_close_matches(infraccion, crimenes, n=1, cutoff=0.65)

            # Si el proceso no es crimen obtener diccionario
            if len(in_delitos) == 0:
                caract = {'id_proceso': proceso.find_all('td')[2].text.replace('-', '')}
                caract.update({'causa': infraccion})
                caracteristicas.append(caract)

            else:
                # Open process
                ingresar(driver.find_element(By.ID, proceso.button['id']), esperar)
                time.sleep(delay)

                # Loop over each instance
                page = BeautifulSoup(driver.page_source, 'lxml')
                instancias = page.find('tbody', id='formJuicioDialogo:dataTableMovimiento_data')
                
                trs = instancias.find_all('tr', class_='ui-widget-content')

                for tr in trs:
                    # Open instance
                    ingresar(driver.find_element(By.ID, tr.button['id']), esperar)
                    time.sleep(delay)
                 
                    # Get instance page source
                    pg = BeautifulSoup(driver.page_source, 'lxml')
                    general = pg.find('table', id=re.compile('formJuicioDetalle:j_idt(\d+)')).tbody

                    # Get Generalities about the case
                    caract = {}
                    for index, tr in enumerate(general):
                        td = tr.find_all('td', class_='ui-panelgrid-cell descripcion')
                        if index == 0:
                            caract.update({'id_proceso': td[0].text.rstrip(' ')})
                        elif index == 1:
                            caract.update({'causa': td[1].text.rstrip(' ')})
                        elif index == 2:
                            caract.update({'demandante': td[0].text.rstrip(' ')})
                            caract.update({'demandado': td[1].text.rstrip(' ')})

                    #Si tiene solo una pagina
                    if pg.find('span', class_='ui-paginator-pages') is None:
                        
                        actos = pg.find('tbody', id='formJuicioDetalle:dataTable_data')
                        for tr_actos in actos.find_all('tr'):
                            if tr_actos.legend is not None:
                                if ('SORTEO' in tr_actos.legend.text) & ('PERITO' not in tr_actos.legend.text):
                                    leyenda = tr_actos.legend.text.rstrip(' ')
                                    leyenda = leyenda + "_" + tr_actos.td.text
                                    caract.update({leyenda: (tr_actos.div.text).lstrip('\n').rstrip('\n')})

                                elif 'SENTENCIA' in tr_actos.legend.text:
                                    leyenda = tr_actos.legend.text.rstrip(' ')
                                    leyenda = leyenda + "_" + tr_actos.td.text
                                    caract.update({leyenda: (tr_actos.div.text).lstrip('\n').rstrip('\n')})

                                elif 'ACTA RESUMEN' in tr_actos.legend.text:
                                    leyenda = tr_actos.legend.text.rstrip(' ')
                                    leyenda = leyenda + "_" + tr_actos.td.text
                                    caract.update({leyenda: (tr_actos.div.text).lstrip('\n').rstrip('\n')})
                    
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
                                        leyenda = tr_actos.legend.text.rstrip(' ')
                                        leyenda = leyenda + "_" + tr_actos.td.text
                                        caract.update({leyenda: (tr_actos.div.text).lstrip('\n').rstrip('\n')})

                                    elif 'SENTENCIA' in tr_actos.legend.text:
                                        leyenda = tr_actos.legend.text.rstrip(' ')
                                        leyenda = leyenda + "_" + tr_actos.td.text
                                        caract.update({leyenda: (tr_actos.div.text).lstrip('\n').rstrip('\n')})

                                    elif 'ACTA RESUMEN' in tr_actos.legend.text:
                                        leyenda = tr_actos.legend.text.rstrip(' ')
                                        leyenda = leyenda + "_" + tr_actos.td.text
                                        caract.update({leyenda: (tr_actos.div.text).lstrip('\n').rstrip('\n')})

                            # Change page
                            ingresar(driver.find_element(By.CSS_SELECTOR, '.ui-icon-seek-next'), esperar)
                            time.sleep(delay)
                    
                    # Add unique instancia a resultado
                    caracteristicas.append(caract)

                    # Regresar
                    ingresar(driver.find_element(By.ID, 'formJuicioDetalle:btnCerrar'), esperar)
                    time.sleep(delay)

                # Return to procesos page
                ingresar(driver.find_element(By.XPATH, '//*[@id="formJuicioDialogo:btnCancelar"]'), esperar)
                time.sleep(delay)

    return caracteristicas

# Function to extract data from a single process
def juicios(driver, dep_judicial, year, n_attempt, list_crimenes, delay=2):
    """
    La funcion juicios llama al webscraper y da como resultado un data frame
    que contiene todos los resultados de los juicios 
    """

    # Create id_proceso
    id_proceso = (5-len(str(n_attempt)))*'0' + str(n_attempt)

    # Call function to webscrap
    result_list = scrap_crimenes(driver, dep_judicial, year, id_proceso, list_crimenes, delay=delay)

    # Convert results to pandas
    result_df = pd.DataFrame()
    for instancia in result_list:
        result_df = pd.concat([result_df, pd.DataFrame(instancia, index=[0])], ignore_index=True)

    return result_df

# Function to iterate over
def obtener_datos(dflistos, iddep, list_crimenes, ventana=True, delay=2):
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
        last_proceso = str(dflistos['id_proceso'][dflistos.shape[0]-1])
        yr_last = int(last_proceso[5:9])
        num_last = int(re.sub('\D', '', last_proceso[9:])) + 1

    # 2 - Run Webscraper

    # Define options for browser
    options = webdriver.FirefoxOptions()
    options.headless = ventana # do not show browser window
    options.page_load_strategy = 'none' # Dont wait page to be loaded
    #options.set_preference("general.useragent.override", UserAgent().random)

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
                results_df = juicios(driver, iddep, str(year), n_attempt, list_crimenes, delay)
                
                # Check if id_proceso existe
                if 'No existe este proceso' in results_df.causa[0]:
                    nfallidos +=1

                    if nfallidos >=10:
                        results = pd.concat([results, results_df], ignore_index=True) 
                        break

                else:
                    results = pd.concat([results, results_df], ignore_index=True)

            except:
                # If we cannot get the data, return the result up to that point
                driver.close()
                print(f'El proceso se interrumpio. {iddep+str(year)+str(n_attempt)}')
                return {'estado': False, 'df': results}
                
    # If all works good
    driver.close()
    return {'estado': True, 'df': results}

# Obtener archivos
def obtener_archivos(dflistos, iddep:str, list_crimenes:list, ventana=False, delay=2, y0=2015, ylast=2020):
    """
    La funcion toma como argumento un dataframe ```dflistos``` para la
    dependencia judicial ```iddep```. Calcula el ultimo numero de proceso en el
    dataframe, y llama a la funcion ```scrap crimenes``` para obtener los datos.

    El outcome es un dictionario con 3 elementos:
    1. ```estado```: True si todo el loop termino de correr
    2. ```resumen_df```: pd.DataFrame que contiene el id_proceso, y el nombre de la infraccion
    3. ```documentos```: diccionario con todos los documentos para cada id_proceso

    Inputs:
    ```y0```: Year to start looking. Default 2015
    ```ylast```: Last year. Default 2020
    """

    # 1 - Figure out last id of proceso: If it is the first iteration, start from 2014, and 1
    if dflistos.shape[0] == 0:
        yr_start = y0
        num_last = 1
        ndigits = 4

    else:
        last_proceso = str(dflistos['id_proceso'][dflistos.shape[0]-1])
        yrstr = last_proceso[5:9]
        yr_start = int(yrstr)

        secstr = last_proceso[9:]
        num_last = int(re.sub('\D', '', secstr)) + 1

        # N digits
        ndigits = dflistos['id_proceso'].apply(lambda x: len(re.sub('\D', '', str(x)[9:]))).max()

        

    # 2 - Run Webscraper

    # Define options for browser
    options = webdriver.FirefoxOptions()
    options.headless = ventana # do not show browser window
    options.page_load_strategy = 'none' # Dont wait page to be loaded
    #options.set_preference("general.useragent.override", UserAgent().random)

    # Start Driver
    gecko_path = Path.home()/'Documents/geckodriver.exe'
    driver = webdriver.Firefox(executable_path=gecko_path, options=options)
    url = 'http://consultas.funcionjudicial.gob.ec/informacionjudicial/public/informacion.jsf'
    driver.get(url)

    # 3 - Loop over years and numeros
    resumen = pd.DataFrame() # Empty data frame to store progress
    documentos = {} # Empty dict to save documents downloaded

    for year in range(yr_start, ylast + 1):
        
        n_start = 1 if year > yr_start else num_last

        # The number of digits in secuencial depende del year
        last_sec = int(ndigits*"9")

        # Loop over possible trials
        nfallidos = 0
        for n_attempt in range(n_start, last_sec):
            
            # Move to secuencial str
            sec_str = "0"*(ndigits - len(str(n_attempt))) + str(n_attempt)

            # I'll try to catch any erros in the webscrap
            try:

                # Scrap the data
                res_dict = scrap_crimenes(driver, iddep, str(year), sec_str, list_crimenes, delay=delay)

                # Check if id_proceso existe
                if 'No existe este proceso' in res_dict[0]['causa']:
                    nfallidos +=1

                    if nfallidos >=10:
                        resumen = pd.concat([resumen, pd.DataFrame(res_dict, index=[0])], ignore_index=True) 
                        break

                else:
                    for res in res_dict:
                        
                        # Split the dict between estado del caso y datos para guardar
                        general_set = set(res.keys()).intersection({'id_proceso', 'causa', 'demandante', 'demandado'})
                        general_dict = {key: [res[key]] for key in list(general_set)}
                        docs_dict = res.copy()
                        for key in ['causa', 'demandante', 'demandado']:
                            docs_dict.pop(key, None)
                        
                        # Save resumen
                        resumen=pd.concat([resumen, pd.DataFrame(general_dict)], ignore_index=True)

                        # Save each docs, as dict of dicts
                        documentos.update({res['id_proceso']: docs_dict})

            except (ElementNotInteractableException, ElementClickInterceptedException, StaleElementReferenceException, IndexError):
                # If we cannot get the data, return the result up to that point
                driver.close()
                print(f'El proceso se interrumpio. {iddep+str(year)+str(n_attempt)}')
                return {'estado': False, 'resumen_df': resumen, 'docs': documentos}

    # If all works good
    driver.close()
    return {'estado': True, 'resumen_df': resumen, 'docs': documentos}

# Funcion para extraer solo nombre de los procesos
def tabla_nombre_delitos(iddep:str, year:str, secuencial:str, driver, delay=1, waits=20):
    """
    Returns tabla of name of delitos with a given driver

    Output: a dataframe with the delitos
    """

    # Define waits
    wait = WebDriverWait(driver, waits)
    esperar = delay*10

    # Clean session
    wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="form1:butLimpiar"]'))).click()
    time.sleep(delay)

    # Send a query to the main page
    wait.until(EC.presence_of_element_located((By.ID, 'form1:idJuicioJudicatura'))).send_keys(iddep)
    driver.find_element(By.ID, 'form1:idJuicioAnio').send_keys(year)
    driver.find_element(By.ID, 'form1:idJuicioNumero').send_keys(secuencial)
    ingresar(driver.find_element(By.ID, 'form1:butBuscarJuicios'), esperar)
    time.sleep(delay)

    # Get data
    soup = BeautifulSoup(driver.page_source, 'lxml')
    r = soup.find('tbody', id='form1:dataTableJuicios2_data')

    # Obtain results
    if 'No se encuentran' in r.text:
        resultsdf = pd.DataFrame([r.text], columns=['descripcion'])
        resultsdf['causa'] = iddep + year + secuencial

        return resultsdf
    
    else:

        # Save results in a list
        res = []

        # Loop over items
        for proc in r.contents:

            tx = proc.text.split('\n', 1)[0]
            tx = tx.rstrip(' ')
            res.append(tx)


        # Convert results to pandas
        result_df = pd.DataFrame()
        for instancia in res:
            ins_df = pd.DataFrame([instancia], columns=['descripcion'])
            result_df = pd.concat([result_df, ins_df], ignore_index=True)
            result_df['causa'] = iddep + year + secuencial

        return result_df

def infraccion_lista_delitos(procesos_lst:list, ventana=True, delay=1):
    """
    La funcion toma como input una lista de id_procesos para sacar la infraccion
    """

    # 1. Set up the driver
    options = webdriver.FirefoxOptions()
    options.headless = ventana # True= do not show browser window
    options.page_load_strategy = 'none' # Dont wait page to be loaded

    # Start Driver
    gecko_path = Path.home()/'Documents/geckodriver.exe'
    driver = webdriver.Firefox(executable_path=gecko_path, options=options)
    url = 'http://consultas.funcionjudicial.gob.ec/informacionjudicial/public/informacion.jsf'
    driver.get(url)

    # Define base for results
    results = pd.DataFrame()

    # 2. Loop over procesos
    for proceso in procesos_lst:

        # Get iddep, year and secuencial
        iddep = proceso[:4+1]
        year = proceso[5:9]
        secuencial = proceso[9:]

        try:
            # Scrap the data
            res_df = tabla_nombre_delitos(iddep, year, secuencial, driver, delay)
            results = pd.concat([results, res_df], ignore_index=True)
        
        except (ElementNotInteractableException, ElementClickInterceptedException):
            # If we cannot get the data, return the result up to that point
            driver.close()
            print(f'El proceso se interrumpio. {iddep + str(year) + secuencial}')
            return {'estado': False, 'df': results}

    return {'estado': True, 'df': results}

def obtener_infraccion(dflistos, iddep:str, ventana=True, delay=2):
    """
    La funcion toma como argumento un dataframe ```dflistos``` para la
    dependencia judicial ```iddep```. Calcula el ultimo numero de proceso en el
    dataframe, y llama a la funcion de juicios para obtener los datos El
    resultado es un diccionario, en el cual el primer elemento es ul estado =
    {True, False} que define si se acabo ya con todos los procesos de una
    dependencia. Y el segundo elemento es el dataframe con el texto de cada
    proceso

    ventana: Si hago aparecer el browser 
    """

    # 1 - Figure out last id of proceso: If it is the first iteration, start from 2014, and 1
    if dflistos.shape[0] == 0:
        year0 = 2010
        sec0 = 0

    else:
        last_proceso = str(dflistos['causa'][dflistos.shape[0]-1])

        if len(last_proceso) == 11:
            last_proceso = "0"+last_proceso
        
        year0 = int(last_proceso[5:9])
        sec0 = int(last_proceso[-3:])
        

    # 2 - Run Webscraper

    # Define options for browser
    options = webdriver.FirefoxOptions()
    options.headless = ventana # True= do not show browser window
    options.page_load_strategy = 'none' # Dont wait page to be loaded
    #options.set_preference("general.useragent.override", UserAgent().random)

    # Start Driver
    gecko_path = Path.home()/'Documents/geckodriver.exe'
    driver = webdriver.Firefox(executable_path=gecko_path, options=options)
    url = 'http://consultas.funcionjudicial.gob.ec/informacionjudicial/public/informacion.jsf'
    driver.get(url)

    # Define base for results
    results = pd.DataFrame()

    # Loop over years
    for year in range(year0, 2014+1):

        n_start = 1 if year > year0 else sec0

        # Loop over possible trials
        nfallidos = 0
        for sec in range(n_start, 999+1):

            # Convert to string
            sec_str = "0"*(3 - len(str(sec))) + str(sec)
            
            try:
                # Scrap the data
                res_df = tabla_nombre_delitos(iddep, str(year), sec_str, driver, delay)
                
                # Check if id_proceso existe
                if 'No se encuentran' in res_df.descripcion[0]:
                    nfallidos +=1

                    if nfallidos >=3:
                        results = pd.concat([results, res_df], ignore_index=True) 
                        break

                else:
                    results = pd.concat([results, res_df], ignore_index=True)

            except (ElementNotInteractableException, ElementClickInterceptedException):
                # If we cannot get the data, return the result up to that point
                driver.close()
                print(f'El proceso se interrumpio. {iddep + str(year) + sec_str}')
                return {'estado': False, 'df': results}
                
    # If all works good
    driver.close()
    return {'estado': True, 'df': results}

# Get files from a list
def scrap_procesos(dflistos:pd.DataFrame, list_crimenes:list, ventana=False, delay=2):

    # 1 - Figure out next proceso:
    options = webdriver.FirefoxOptions()
    options.headless = ventana # do not show browser window
    options.page_load_strategy = 'none' # Dont wait page to be loaded
    #options.set_preference("general.useragent.override", UserAgent().random)

    # Start Driver
    gecko_path = Path.home()/'Documents/geckodriver.exe'
    driver = webdriver.Firefox(executable_path=gecko_path, options=options)
    url = 'http://consultas.funcionjudicial.gob.ec/informacionjudicial/public/informacion.jsf'
    driver.get(url)

    # 3 - Loop over years and numeros
    dfestado = pd.DataFrame()
    documentos = {} # Empty dict to save documents downloaded

    # Obtener listados
    procesos_lst = list(dflistos.loc[dflistos['estado']==0, 'id_proceso'])

    for proc in procesos_lst:
        
        # Get data about 
        iddep = proc[:5]
        year = proc[5:9]
        sec = proc[9:].rstrip(' ')

        # I'll try to catch any erros in the webscrap
        try:

            # Scrap the data
            res_dict = scrap_crimenes(driver, iddep, year, sec, list_crimenes, delay=delay)

            for res in res_dict:
                
                # Split the dict between estado del caso y datos para guardar
                for key in ['causa', 'demandante', 'demandado']:
                    res.pop(key, None)

                dfestado = pd.concat([dfestado, pd.DataFrame({'id_proceso': [res['id_proceso']], 'estado': [1]})], ignore_index=True)
                documentos.update({res['id_proceso']: res})

        except (ElementNotInteractableException, ElementClickInterceptedException, StaleElementReferenceException, AttributeError):
            # If we cannot get the data, return the result up to that point
            driver.close()
            print(f'El proceso se interrumpio. {iddep+year+sec}')
            return {'estado': False, 'df':dfestado, 'docs': documentos}

    # If all works good
    driver.close()
    return {'estado': True, 'df':dfestado, 'docs': documentos}


def scrap_2010_2014(dflistos:pd.DataFrame, list_crimenes:list, ventana=False, delay=2):
    
    options = webdriver.FirefoxOptions()
    options.headless = ventana # do not show browser window
    options.page_load_strategy = 'none' # Dont wait page to be loaded
    #options.set_preference("general.useragent.override", UserAgent().random)

    # Start Driver
    gecko_path = Path.home()/'Documents/geckodriver.exe'
    driver = webdriver.Firefox(executable_path=gecko_path, options=options)
    url = 'http://consultas.funcionjudicial.gob.ec/informacionjudicial/public/informacion.jsf'
    driver.get(url)

    # Loop over procesos
    resumen = pd.DataFrame()
    documentos = {}

    por_scrapear = dflistos.loc[dflistos['estado']==0].reset_index(drop=True).copy()

    for idx in range(por_scrapear.shape[0]):

        # Get data
        iddep = por_scrapear.loc[idx, 'id_judicatura']
        year = por_scrapear.loc[idx, 'year']
        sec = por_scrapear.loc[idx, 'id_sec']

        # I'll try to catch any erros in the webscrap
        try:

            # Scrap the data
            res_lst = scrap_crimenes(driver, iddep, year, sec, list_crimenes, delay=delay)

            for res_dict in res_lst:
                
                # Resumen caso
                general_set = set(res_dict.keys()).intersection({'id_proceso', 'causa', 'demandante', 'demandado'})
                general_dict = {key: [res_dict[key]] for key in list(general_set)}
                resumen=pd.concat([resumen, pd.DataFrame(general_dict)], ignore_index=True)

                # For documents
                docs_dict = res_dict.copy()
                for key in ['causa', 'demandante', 'demandado']:
                    docs_dict.pop(key, None)
                documentos.update({res_dict['id_proceso']: docs_dict})

        except:
            # If we cannot get the data, return the result up to that point
            driver.close()
            print(f'El proceso se interrumpio. {iddep+year+sec}')
            return {'estado': False, 'df':resumen, 'docs': documentos}

    # If all works good
    driver.close()
    return {'estado': True, 'df':resumen, 'docs': documentos}