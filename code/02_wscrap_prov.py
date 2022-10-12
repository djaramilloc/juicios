import numpy as np
import pandas as pd
import re

import sys
from pyprojroot import here

from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager

# Load webscrapper
sys.path.append((here()/'code').as_posix())
from wscrap_cases import scrap_court

# Set paths
proc = here()/'data/proc'
raw = here()/'data/raw'

# Load list of crimenes to download
delitos_list = pd.read_csv(raw/'lista_delitos_15_20.csv')
delitos_list = list(delitos_list['NOMBRE DELITO'])

# Input a province
idprov = '09'

# look over courts in prov
courts_status = pd.read_parquet(proc/f'estado/prov{idprov}/courts_status.parquet')

# Define Session for webdriver
s = (Service(GeckoDriverManager().install()))

# loop over missing courts
for idcourt in np.unique(courts_status.loc[courts_status['estado'].isna(), 'id_dependencia']):
    
    # Look for file with status of download
    try:
        cases_court = pd.read_parquet(proc/f'estado/prov{idprov}/cases_court_{idcourt}.parquet')
    except FileNotFoundError:
        cases_court = pd.DataFrame(columns=['id_proceso', 'causa', 'demandado', 'demandante'])

    # Webscrap data for each court
    print(f'BEGIN COURT: {idcourt} -----------------------')
    results_court = scrap_court(cases_court, idcourt, idprov, proc, delitos_list, s, delay=3)
    
    last_caso = ''

    # Loop hasta finalizar con una court
    while results_court['estado']==False:
        
        # check if the webscrapper is stuck in a value
        if last_caso == "": # Primer errror en caso c, setear last_caso
            last_caso = results_court['id_proceso']
            nerrores_caso = 1
        
        elif last_caso == results_court['id_proceso']: # Si el error es el mismo aumentar counter
            print(f"Intento N: {nerrores_caso}")
            nerrores_caso = nerrores_caso + 1
        
        else: 
            last_caso = ''
            nerrores_caso = 0

        # Keep looking if nerrores bellow threshold
        if nerrores_caso <=10:
            cases_court = pd.read_parquet(proc/f'estado/prov{idprov}/cases_court_{idcourt}.parquet')
            results_court = scrap_court(cases_court, idcourt, idprov, proc, delitos_list, s, delay=3)
        
        else:
            # Input data on not downloaded case
            cases_court = pd.read_parquet(proc/f'estado/prov{idprov}/cases_court_{idcourt}.parquet')
            # Find last case available
            lastc = re.sub('[^0-9]', '', cases_court.loc[cases_court.shape[0]-1, 'id_proceso'])
            # Add one to that value
            inputc = lastc[0:9] + ((len(lastc) - 9) - len(str(int(lastc[9:]) + 1)))*"0" + str(int(lastc[9:]) + 1)
            # Add that to the court being downloaded
            cases_court = pd.concat([cases_court,
                pd.DataFrame({'id_proceso': inputc, 'causa': 'No se puede descargar'}, index=[0])], ignore_index=True)
            # Look again
            results_court = scrap_court(cases_court, idcourt, idprov, proc, delitos_list, s, delay=3)
    
    # Update result of court
    courts_status.loc[courts_status['id_dependencia']==idcourt, 'estado'] = 1
    courts_status.to_parquet(proc/f'estado/prov{idprov}/courts_status.parquet', index=False)