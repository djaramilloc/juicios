import pandas as pd
from pyprojroot import here
import sys
import warnings

# Definir paths
raw = here()/'data/raw'
proc = here()/'data/proc'

# Load programs
sys.path.insert(1, (here()/'code').as_posix())
warnings.filterwarnings("ignore", category=DeprecationWarning)
from scrap_crimenes import obtener_infraccion

# Load/create summary file
process = 1
# python code/03_get_infracciones_12_14.py
faltan = True

while faltan == True:
    resumen = pd.read_excel(proc/f'delitos_web/sin_causa_{process}.xlsx', dtype=str)
    listos = resumen.loc[resumen['estado']==1].reset_index(drop=True)
    faltantes = resumen.loc[resumen['estado']==0].reset_index(drop=True)

    if faltantes.shape[0] == 0:
        faltan = False
        break

    else:
        depnumber = faltantes.loc[0, 'iddep']
        depnumber = "0"*(5 - len(str(depnumber))) + str(depnumber)

        # Run file
        print(f'Running {depnumber} {process}')

        # Create file
        try:
            df_start = pd.read_csv(proc/f'resumenes/by_judicatura/nombres_{depnumber}.csv')
        except (FileNotFoundError, pd.errors.EmptyDataError):
            df_start = pd.DataFrame()

        # First attempt
        res = obtener_infraccion(df_start, depnumber, ventana=False, delay=2)
        df_procesos = pd.concat([df_start, res['df']], ignore_index=True)
        df_procesos.to_csv(proc/f'resumenes/by_judicatura/nombres_{depnumber}.csv', index=False)

        # Loop while false
        while res['estado'] == False:
            res = obtener_infraccion(df_procesos, depnumber, ventana=False, delay=2)
            df_procesos = pd.concat([df_procesos, res['df']], ignore_index=True).copy()
            df_procesos.to_csv(proc/f'resumenes/by_judicatura/nombres_{depnumber}.csv', index=False)

        # Save if true
        else:
            df_procesos = pd.concat([df_procesos, res['df']], ignore_index=True).copy()
            df_procesos.to_csv(proc/f'resumenes/by_judicatura/nombres_{depnumber}.csv', index=False)


            faltantes.loc[0, 'estado'] = 'listo'
            (pd
            .concat([listos, faltantes], ignore_index=True)
            .to_csv(proc/f'resumenes/resumen_10_14_{process}.csv', index=False))

            print(f'Finally!!! {depnumber}')