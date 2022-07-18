import pandas as pd
from pathlib import Path
from pyprojroot import here
import sys
import warnings
import re
from selenium import webdriver
from code.scrap_crimenes import tabla_nombre_delitos

# Set Paths
root = here()
proc = root/'data/proc'
raw = root/'data/raw'

# Load scraper
sys.path.insert(1, (root/'code').as_posix())
warnings.filterwarnings("ignore", category=DeprecationWarning)
from scrap_crimenes import obtener_archivos
from scrap_crimenes import scrap_crimenes


# Obtener listado de crimenes
delitos = pd.read_excel(proc/'delitos_lists/delitos_2010_2014_gye.xlsx')
delitos = list(delitos.loc[delitos['eliminar']!=1, 'accion'])


#######################################################
# Start driver
options = webdriver.FirefoxOptions()
options.headless = False # do not show browser window
options.page_load_strategy = 'none' # Dont wait page to be loaded
#options.set_preference("general.useragent.override", UserAgent().random)

# Start Driver
gecko_path = Path.home()/'Documents/geckodriver.exe'
driver = webdriver.Firefox(executable_path=gecko_path, options=options)
url = 'http://consultas.funcionjudicial.gob.ec/informacionjudicial/public/informacion.jsf'
driver.get(url)

waits = 20
delay = 1
iddep = '09284'
year = '2015'
secuencial = '02836'

proc = r.contents[0]

proc.text.split('\n', 1)[0]


r = tabla_nombre_delitos('09284', '2015', '02836', driver)
r
dflistos = pd.read_excel(proc/'scrap_lists/2010_2014/09100.xlsx', dtype={'id_judicatura': str, 'id_sec': str, 'year': str})

dfestado = pd.DataFrame()
documentos = {}

for idx in range(4):

    # Get data
    iddep = dflistos.loc[idx, 'id_judicatura']
    year = dflistos.loc[idx, 'year']
    sec = dflistos.loc[idx, 'id_sec']

    # I'll try to catch any erros in the webscrap

        # Scrap the data
    res_lst = scrap_crimenes(driver, iddep, year, sec, delitos, delay=2)

    for res_dict in res_lst:
        
        # Split the dict between estado del caso y datos para guardar
        for key in ['causa', 'demandante', 'demandado']:
            res_dict.pop(key, None)

        dfestado = pd.concat([dfestado, pd.DataFrame({'id_proceso': [res_dict['id_proceso']], 'estado': [1]})], ignore_index=True)
        documentos.update({res_dict['id_proceso']: res_dict})


dflistos
dfestado.drop_duplicates(ignore_index=True)

encontrado = dfestado.drop_duplicates(ignore_index=True).loc[1, 'id_proceso']

import fuzzymatcher as fz
import numpy as np

matched = fz.fuzzy_left_join(dflistos, dfestado.drop_duplicates(ignore_index=True), left_on='proceso_long', right_on='id_proceso')

# Save matched id
matched.loc[(~matched['id_proceso'].isna()) & (matched['id_matched'].isna()), 'id_matched'] = matched['id_proceso']
matched['estado'] = np.where((matched['estado_left']==1)|(matched['estado_right']==1), 1, 0)


matched.drop(columns=['__id_left', '__id_right', 'best_match_score', 'estado_left', 'estado_right', 'id_proceso'], inplace = True)

matched

