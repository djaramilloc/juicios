import time

import pandas as pd
from pathlib import Path
from unidecode import unidecode
import re
import difflib

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.common.exceptions import ElementNotInteractableException
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import InvalidSessionIdException
# Define wait for button
def ingresar(element, espero):
    try:
        element.click()
    except (ElementClickInterceptedException, ElementNotInteractableException, StaleElementReferenceException):
        try:
            time.sleep(espero)
            element.click()
        except (ElementClickInterceptedException, ElementNotInteractableException, StaleElementReferenceException) as exp:
            raise exp


# Function to scrap one trial
def scrap_crimenes(driver, dependencia:str, year:str, secuencial:str, crimenes:list, delay=1, waits=10):
    """
    Scraper for judicial trial, using driver. 
    The function returs a dictionary ```results``` which contains generaliteis of the case and 
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
    driver.find_element(By.ID, 'form1:idJuicioJudicatura').send_keys(dependencia)
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
            print(f"scrap_crimenes: {caract['id_proceso']} No existe")
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
                                titulobox = unidecode(tr_actos.legend.text).upper().replace('  ', '')
                                if ('SORTEO' in titulobox) & ('PERITO' not in titulobox):
                                    leyenda = titulobox.rstrip(' ')
                                    leyenda = leyenda + "_" + tr_actos.td.text
                                    caract.update({leyenda: (tr_actos.div.text).lstrip('\n').rstrip('\n')})

                                elif 'SENTENCIA' in titulobox:
                                    leyenda = titulobox.rstrip(' ')
                                    leyenda = leyenda + "_" + tr_actos.td.text
                                    caract.update({leyenda: (tr_actos.div.text).lstrip('\n').rstrip('\n')})

                                elif 'ACTA RESUMEN' in titulobox:
                                    leyenda = titulobox.rstrip(' ')
                                    leyenda = leyenda + "_" + tr_actos.td.text
                                    caract.update({leyenda: (tr_actos.div.text).lstrip('\n').rstrip('\n')})

                                elif 'ARCHIVO' in titulobox:
                                    leyenda = titulobox.rstrip(' ')
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
                                    titulobox = unidecode(tr_actos.legend.text).upper().replace('  ', '')
                                    if ('SORTEO' in titulobox) & ('PERITO' not in titulobox):
                                        leyenda = titulobox.rstrip(' ')
                                        leyenda = leyenda + "_" + tr_actos.td.text
                                        caract.update({leyenda: (tr_actos.div.text).lstrip('\n').rstrip('\n')})

                                    elif 'SENTENCIA' in titulobox:
                                        leyenda = titulobox.rstrip(' ')
                                        leyenda = leyenda + "_" + tr_actos.td.text
                                        caract.update({leyenda: (tr_actos.div.text).lstrip('\n').rstrip('\n')})

                                    elif 'ACTA RESUMEN' in titulobox:
                                        leyenda = titulobox.rstrip(' ')
                                        leyenda = leyenda + "_" + tr_actos.td.text
                                        caract.update({leyenda: (tr_actos.div.text).lstrip('\n').rstrip('\n')})
                                    
                                    elif 'ARCHIVO' in titulobox:
                                        leyenda = titulobox.rstrip(' ')
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

            print(f"scrap_crimenes: {caract['id_proceso']} Existe y Descargado")
    return caracteristicas

def scrap_court(cases_court:pd.DataFrame, documentos:list, idcourt:str, list_crimenes:list, s, ventana=False, delay=2):
    """
    Parameters: 
    
    - cases_court: A Dataframe with a list of downloaded process. If
    it is an empty df, the program starts from y0==2014, and secuencial==1
    - documentos: A list containing dictionaries for each downloaded document.
      The first iteration it is empty.
    - s: Session of the form: Service(GeckoDriverManager().install())
    """

    # 1 - Start webdriver:
    options = webdriver.FirefoxOptions()
    options.headless = ventana # do not show browser window
    #options.page_load_strategy = 'none' # Dont wait page to be loaded
    #options.set_preference("general.useragent.override", UserAgent().random)

    print('Driver starting new session ------------------------------')
    driver = webdriver.Firefox(service=s, options=options)
    url = 'http://consultas.funcionjudicial.gob.ec/informacionjudicial/public/informacion.jsf'
    driver.get(url)

    # 2. Define start year and secuencial
    if cases_court.empty:
        y0 = 2014
        case0 = 1
        ndigits = 4
    else:
        last_proceso = cases_court.loc[cases_court.shape[0]-1, 'id_proceso']
        last_proceso = re.sub('[^0-9]', '', last_proceso)
        y0 = int(last_proceso[5:8+1])
        case0 = int(last_proceso[9:])
        ndigits = len(last_proceso[9:])


    # 3 - Loop over years and numeros
    for year in range(2014, 2021+1):

        yearstr = str(year) # Convert year to string
        noexists_counter = 0 # Start counter for inexistent cases

        for numid in range(case0, 99999+1):
            
            # Get out of loop if there are 5 or more non existent cases
            if noexists_counter>=5:
                break
            
            # Set number of ceros
            secstr = (ndigits - len(str(numid)))*"0" + str(numid)
        
            # I'll try to catch any erros in the webscrap
            try:

                # Scrap the data
                print('Starting Search New Case')
                res_list = scrap_crimenes(driver, idcourt, yearstr, secstr, list_crimenes, delay=delay)

                for res_dict in res_list:

                    # Add result to cases_court
                    if len(res_dict) > 2:
                        sumcaso = {key: res_dict[key] for key in ['id_proceso', 'causa', 'demandante', 'demandado']}
                    else:
                        sumcaso = {key: res_dict[key] for key in ['id_proceso', 'causa']}
                        
                        # Check if case exists
                        if 'No existe' in res_dict['causa']:
                            noexists_counter = noexists_counter + 1

                    # Concat status to dataframe
                    cases_court = pd.concat([cases_court, pd.DataFrame(sumcaso, index=[0])], ignore_index=True)

                    # Split the dict between estado del caso y datos para guardar
                    for key in ['causa', 'demandante', 'demandado']:
                        res_dict.pop(key, None)

                    documentos.append({res_dict['id_proceso']: {key: res_dict[key] for key in res_dict.keys() if key!='id_proceso'}})
                    
            except (ElementNotInteractableException, ElementClickInterceptedException, StaleElementReferenceException, AttributeError):
                # If we cannot get the data, return the result up to that point
                driver.close()
                print(f"Problemas con {res_dict['id_proceso']}, reiniciar")
                scrap_court(cases_court, documentos, idcourt, list_crimenes, s)

    # If all works good
    try:
        driver.close()
    except InvalidSessionIdException:
        pass
    
    print(f"Court {idcourt} done!!!")
    return {'df_estado':cases_court, 'docs': documentos}