import numpy as np
import pandas as pd
import re

import sys
from pathlib import Path
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
idprov = '07'

# look over courts in prov
courts_status = pd.read_parquet(proc/f'estado/prov{idprov}/courts_status.parquet')
courts_status = courts_status.loc[courts_status['estado'].isna()] #Keep missing courts

# Define Session for webdriver
s = (Service(GeckoDriverManager().install()))

# loop over missing courts
for idcourt in np.unique(courts_status['id_dependencia']):
    
    # Look for file with status of download
    try:
        cases_court = pd.read_parquet(proc/f'estado/prov{idprov}/cases_court_{idcourt}.parquet')
    except FileNotFoundError:
        cases_court = pd.DataFrame(columns=['id_proceso', 'causa', 'demandado', 'demandante'])

    # Webscrap data for each court
    results_court = scrap_court(cases_court, [], idcourt, delitos_list, s, delay=3)

    # Save Summary
    results_court['df_estado'].to_parquet(proc/f"estado/prov{idprov}/cases_court_{idcourt}.parquet")

    # Save documentos
    for case_dict in results_court['docs']:

        # Access each dictionary
        for idcase, docs_dict in case_dict.items():

            # I only create folders for those with a doc downloaded
            if docs_dict:
                folder_name = idcase.replace('*', '_') # Set folder name
                folder_name = re.sub(' ', '', folder_name)

                # Create folders if they do not exist
                try:
                    Path(proc/f'docs/prov{idprov}/{folder_name}').mkdir(parents=True)
                except FileExistsError:
                    pass
                
                # Save docs
                for filename_raw, texto in docs_dict.items():
                    
                    # Create name
                    filename = filename_raw.replace(" ", "_")
                    filename = filename.replace("/", "_")
                    filename = filename.replace(":", "_")

                    with open(proc/f'docs/prov{idprov}/{folder_name}/{filename}.txt', "w+") as f_out:
                        _ = f_out.write(texto)

    # Update result of court
    courts_status = courts_status.loc[courts_status['id_dependencia']==idcourt, 'estado'] = 1
    courts_status.to_parquet(proc/f'estado/prov{idprov}/courts_status.parquet')