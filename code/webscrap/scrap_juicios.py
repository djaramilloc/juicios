import time
from bs4 import BeautifulSoup

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def scrap_juicios(driver, dependencia, year, secuencial, url, delay = 1):
    """
    Scraper for judicial trials, using driver. 
    The function returs a tupple ```results``` which contains generaliteis of the case and 
    the text of sentencia and acta de sorteo
    """

    # Define waits
    wait = WebDriverWait(driver, 10)

    # Send a query to the main page
    wait.until(EC.presence_of_element_located((By.ID, 'form1:idJuicioJudicatura'))).send_keys(dependencia)
    driver.find_element(By.ID, 'form1:idJuicioAnio').send_keys(year)
    driver.find_element(By.ID, 'form1:idJuicioNumero').send_keys(secuencial)
    driver.find_element(By.ID, 'form1:butBuscarJuicios').click()
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
            # Open process
            driver.find_element(By.ID, proceso.button['name']).click()
            time.sleep(delay)

            # Loop over each instance
            page = BeautifulSoup(driver.page_source, 'lxml')
            instancias = page.find('tbody', id='formJuicioDialogo:dataTableMovimiento_data')
            
            for tr in instancias.find_all('tr', class_='ui-widget-content'):
                
                # Open instance
                driver.find_element(By.ID, tr.button['name']).click()
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
                    driver.find_element(By.CSS_SELECTOR, "a.ui-paginator-page:nth-child(1)").click()
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
                        driver.find_element(By.CSS_SELECTOR, '.ui-icon-seek-next').click()
                        time.sleep(delay)
                
                # Add unique instancia a resultado
                caracteristicas.append(caract)

                # Regresar
                driver.find_element(By.XPATH, '/html/body/div[1]/div[4]/div/div/div[1]/div[1]/a').click()
                time.sleep(delay)

            # Return to procesos page
            driver.find_element(By.XPATH, '//*[@id="formJuicioDialogo:btnCancelar"]').click()
            time.sleep(delay)

    # Click en boton limpiar
    driver.find_element(By.XPATH, '//*[@id="form1:butLimpiar"]').click()

    return caracteristicas