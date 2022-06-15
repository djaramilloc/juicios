import numpy as np
import pandas as pd
from pathlib import Path
from pyprojroot import here
import sys
import warnings

# Set Paths
root = here()
proc = root/'data/proc'
raw = root/'data/raw'

# Load scraper
sys.path.insert(1, (root/'code').as_posix())
warnings.filterwarnings("ignore", category=DeprecationWarning)
from scrap_crimenes import scrap_procesos

# Obtener listado de crimenes
delitos = pd.read_csv(proc/'lista_delitos.csv')
delitos = list(delitos['NOMBRE DELITO'])

# Which part it will compute
cpu = 3

procesos = pd.read_csv(proc/f'procesos_incompletos_{cpu}.csv', dtype={'id_proceso': str})
procesos = procesos.loc[procesos['estado']==0].reset_index(drop=True)

# Start wscrap
print(f'Start running {cpu}')
res_dict = scrap_procesos(procesos, delitos, ventana=False, delay=2)

# Update results
if res_dict['df'].shape[0] > 0:
    completos = procesos.merge(res_dict['df'].drop_duplicates(), how='left', on='id_proceso', suffixes=('_x', '_y'))
    completos['estado'] = np.where((completos['estado_y']==1)|(completos['estado_x']==1), 1, 0)
    completos.drop(columns=['estado_x', 'estado_y'], inplace=True)
    completos.to_csv(proc/f'procesos_incompletos_{cpu}.csv', index=False)

    # Save data to documents
    for id_proceso, dict_proceso in res_dict['docs'].items():

        # Only for those with info
        if len(res_dict['docs'][id_proceso]) > 1:
            
            # Crear una carpeta con el nombre = id_proceso, dentro todos los archivos
            try: 
                Path(proc/f'delitos_web/files/{id_proceso}').mkdir()
            except FileExistsError:
                pass

            # Save files as txt
            for name_doc, cont_docs in dict_proceso.items():

                # No guardar datos generales
                if name_doc not in ['id_proceso', 'demandante', 'demandado']:
                    
                    name = name_doc.replace(" ", "_")
                    name = name.replace("/", "_")
                    name = name.replace(":", "_")

                    # Write file
                    with open(proc/f'delitos_web/files/{id_proceso}/{name}.txt', 'w+') as f:
                        _ = f.write(cont_docs)


while res_dict['estado'] == False:

    # Load procesos
    df_proc = pd.read_csv(proc/f'procesos_incompletos_{cpu}.csv', dtype={'id_proceso': str})
    procesos = df_proc.loc[df_proc['estado']==0].reset_index(drop=True)

    # Run scrapper
    res_dict = scrap_procesos(procesos, delitos, ventana=False, delay=3)
    
    # Update results
    if res_dict['df'].shape[0] > 0:
        completos = df_proc.merge(res_dict['df'].drop_duplicates(), how='left', on='id_proceso', suffixes=('_x', '_y'))
        completos['estado'] = np.where((completos['estado_y']==1)|(completos['estado_x']==1), 1, 0)
        completos.drop(columns=['estado_x', 'estado_y'], inplace=True)
        completos.to_csv(proc/f'procesos_incompletos_{cpu}.csv', index=False)

        # Save data to documents
        for id_proceso, dict_proceso in res_dict['docs'].items():

            # Only for those with info
            if len(res_dict['docs'][id_proceso]) > 1:
                
                # Crear una carpeta con el nombre = id_proceso, dentro todos los archivos
                try: 
                    Path(proc/f'delitos_web/files/{id_proceso}').mkdir()
                except FileExistsError:
                    pass

                # Save files as txt
                for name_doc, cont_docs in dict_proceso.items():

                    # No guardar datos generales
                    if name_doc not in ['id_proceso', 'demandante', 'demandado']:
                        
                        name = name_doc.replace(" ", "_")
                        name = name.replace("/", "_")
                        name = name.replace(":", "_")

                        # Write file
                        with open(proc/f'delitos_web/files/{id_proceso}/{name}.txt', 'w+') as f:
                            _ = f.write(cont_docs)

else:
    completos = df_proc.merge(res_dict['df'].drop_duplicates(), how='left', on='id_proceso', suffixes=('_x', '_y'))
    completos['estado'] = np.where((completos['estado_y']==1)|(completos['estado_x']==1), 1, 0)
    completos.drop(columns=['estado_x', 'estado_y'], inplace=True)
    completos.to_csv(proc/f'procesos_incompletos_{cpu}.csv', index=False)

    for id_proceso, dict_proceso in res_dict['docs'].items():

        # Only for those with info
        if len(res_dict['docs'][id_proceso]) > 1:
            
            # Crear una carpeta con el nombre = id_proceso, dentro todos los archivos
            try: 
                Path(proc/f'delitos_web/files/{id_proceso}').mkdir()
            except FileExistsError:
                pass

            # Save files as txt
            for name_doc, cont_docs in dict_proceso.items():

                # No guardar datos generales
                if name_doc not in ['id_proceso', 'demandante', 'demandado']:
                    
                    name = name_doc.replace(" ", "_")
                    name = name.replace("/", "_")
                    name = name.replace(":", "_")

                    # Write file
                    with open(proc/f'delitos_web/files/{id_proceso}/{name}.txt', 'w+') as f:
                        _ = f.write(cont_docs)

    print(f'Finally done!!')
