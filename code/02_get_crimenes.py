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
from scrap_crimenes import obtener_archivos
from scrap_crimenes import scrap_crimenes


# Obtener listado de crimenes
delitos = pd.read_csv(proc/'lista_delitos.csv')
delitos = list(delitos['NOMBRE DELITO'])


#Obtener listado de dependencias judiciales
#db_depen = pd.read_csv(proc/'restantes_2015.csv', dtype={'id_judicatura': str})
db_depen = pd.read_csv(proc/'restantes_gye.csv', dtype={'id_judicatura': str})
listagye = list(db_depen['id_judicatura'])

num = 0
depnumber = listagye[num]

print(f'Running {depnumber} ({num})')

# Create file
try:
    df_start = pd.read_csv(proc/f'delitos_web/resumen_{depnumber}.csv', dtype={'id_proceso': str})
except FileNotFoundError:
    df_start = pd.DataFrame()

# First attempt
res = obtener_archivos(df_start, depnumber, delitos, ventana=False, delay=4, y0=2016, ylast=2020)

# Save resumen
resumendf = (pd
             .concat([df_start, res['resumen_df']], ignore_index=True)
             .copy())
resumendf.to_csv(proc/f'delitos_web/resumen_{depnumber}.csv', index=False)

# Loop over each case downloaded
for id_proceso, dict_proceso in res['docs'].items():

    # Only for those with info
    if len(res['docs'][id_proceso]) > 1:
        
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


# Loop while false
while res['estado'] == False:
    res = obtener_archivos(resumendf, depnumber, delitos, ventana=False, delay=3, y0=2016, ylast=2020)
    resumendf = (pd
                .concat([resumendf, res['resumen_df']], ignore_index=True)
                .copy())
    resumendf.to_csv(proc/f'delitos_web/resumen_{depnumber}.csv', index=False)

    # Loop over each case downloaded
    for id_proceso, dict_proceso in res['docs'].items():

        # Only for those with info
        if len(res['docs'][id_proceso]) > 1:
            
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

# Save if true
else:
    resumendf = (pd
                .concat([resumendf, res['resumen_df']], ignore_index=True)
                .copy())
    resumendf.to_csv(proc/f'delitos_web/resumen_{depnumber}.csv', index=False)
    
    # Loop over each case downloaded
    for id_proceso, dict_proceso in res['docs'].items():

        # Only for those with info
        if len(res['docs'][id_proceso]) > 1:
            
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

    print(f'Finally!!! {depnumber}')

