import numpy as np
import fuzzymatcher as fz
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
from scrap_crimenes import scrap_2010_2014

# Obtener listado de crimenes
delitos = pd.read_excel(proc/'delitos_lists/delitos_2010_2014_gye.xlsx')
delitos = list(delitos.loc[delitos['eliminar']!=1, 'accion'])

# Listado a procesar
dep  = '09122'
procesos = pd.read_excel(proc/f'scrap_lists/2010_2014/{dep}.xlsx',
                dtype={'id_judicatura': str, 'id_sec': str, 'year': str, 'id_matched':str, 'proceso_long':str})
# Resumen of casos
try:
    resumen = pd.read_excel(proc/f'delitos_web/resumenes/2010_2014/{dep}.xlsx', dtype={'id_proceso': str})
except FileNotFoundError:
    resumen = pd.DataFrame()


# Start wscrap
print(f'Start running {dep}')
res_dict = scrap_2010_2014(procesos, delitos, ventana=False, delay=2)

# Update results
if res_dict['df'].shape[0] > 0:
    
    # Save resumen of complete cases
    resumen = pd.concat([resumen, res_dict['df'].drop_duplicates()], ignore_index=True)
    resumen.to_excel(proc/f'delitos_web/resumenes/2010_2014/{dep}.xlsx', index=False)

    # Save docs
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

    # Update estado
    dfestado = res_dict['df'][['id_proceso']].drop_duplicates(ignore_index=True).copy()
    dfestado['estado'] = 1

    matched = fz.fuzzy_left_join(procesos, dfestado, left_on='proceso_long', right_on='id_proceso')
    matched.loc[(~matched['id_proceso'].isna()) & (matched['id_matched'].isna()), 'id_matched'] = matched['id_proceso']
    matched['estado'] = np.where((matched['estado_left']==1)|(matched['estado_right']==1), 1, 0)
    matched.drop(columns=['__id_left', '__id_right', 'best_match_score', 'estado_left', 'estado_right', 'id_proceso'], inplace = True)
    matched.to_excel(proc/f'scrap_lists/2010_2014/{dep}.xlsx', index=False)

while res_dict['estado'] == False:

    # Volver a correr
    procesos = pd.read_excel(proc/f'scrap_lists/2010_2014/{dep}.xlsx',
            dtype={'id_judicatura': str, 'id_sec': str, 'year': str, 'id_matched':str, 'proceso_long':str})
    resumen = pd.read_excel(proc/f'delitos_web/resumenes/2010_2014/{dep}.xlsx', dtype={'id_proceso': str})
    res_dict = scrap_2010_2014(procesos, delitos, ventana=False, delay=2)

    # Update results
    if res_dict['df'].shape[0] > 0:
    
        # Save resumen of complete cases
        resumen = pd.concat([resumen, res_dict['df'].drop_duplicates()], ignore_index=True)
        resumen.to_excel(proc/f'delitos_web/resumenes/2010_2014/{dep}.xlsx', index=False)

        # Save docs
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

        # Update estado
        dfestado = res_dict['df'][['id_proceso']].drop_duplicates(ignore_index=True).copy()
        dfestado['estado'] = 1

        matched = fz.fuzzy_left_join(procesos, dfestado, left_on='proceso_long', right_on='id_proceso')
        matched.loc[(~matched['id_proceso'].isna()) & (matched['id_matched'].isna()), 'id_matched'] = matched['id_proceso']
        matched['estado'] = np.where((matched['estado_left']==1)|(matched['estado_right']==1), 1, 0)
        matched.drop(columns=['__id_left', '__id_right', 'best_match_score', 'estado_left', 'estado_right', 'id_proceso'], inplace = True)
        matched.to_excel(proc/f'scrap_lists/2010_2014/{dep}.xlsx', index=False)

else:
    procesos = pd.read_excel(proc/f'scrap_lists/2010_2014/{dep}.xlsx',
                dtype={'id_judicatura': str, 'id_sec': str, 'year': str, 'id_matched':str, 'proceso_long':str})
    resumen = pd.read_excel(proc/f'delitos_web/resumenes/2010_2014/{dep}.xlsx', dtype={'id_proceso': str})

    # Save resumen of complete cases
    resumen = pd.concat([resumen, res_dict['df'].drop_duplicates()], ignore_index=True)
    (resumen
    .drop_duplicates()
    .to_excel(proc/f'delitos_web/resumenes/2010_2014/{dep}.xlsx', index=False))

    # Save docs
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

    # Update estado
    dfestado = res_dict['df'][['id_proceso']].drop_duplicates(ignore_index=True).copy()
    dfestado['estado'] = 1

    matched = fz.fuzzy_left_join(procesos, dfestado, left_on='proceso_long', right_on='id_proceso')
    matched.loc[(~matched['id_proceso'].isna()) & (matched['id_matched'].isna()), 'id_matched'] = matched['id_proceso']
    matched['estado'] = np.where((matched['estado_left']==1)|(matched['estado_right']==1), 1, 0)
    matched.drop(columns=['__id_left', '__id_right', 'best_match_score', 'estado_left', 'estado_right', 'id_proceso'], inplace = True)
    matched.to_excel(proc/f'scrap_lists/2010_2014/{dep}.xlsx', index=False)

    print(f'Finally!!! {dep}')