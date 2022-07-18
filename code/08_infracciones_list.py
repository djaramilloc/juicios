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
from scrap_crimenes import infraccion_lista_delitos

# Load/create summary file
process = 1
resumen = pd.read_excel(proc/f'delitos_web/sin_causa_{process}.xlsx', dtype=str)
all_procesos = list(resumen.loc[resumen['estado']==0, 'id_proceso'])

try: 
    results = pd.read_excel(proc/f'delitos_web/infracciones_{process}.xlsx', dtype=str)
    faltantes = list(set(all_procesos) - set(results['causa']))

except FileNotFoundError:
    # Create empty dataframe for results
    results = pd.DataFrame()

    # Set as faltantes todos
    faltantes = all_procesos.copy()

# Run the first time and store results
res = infraccion_lista_delitos(faltantes)
results = pd.concat([results, res['df']], ignore_index=True)
results.to_excel(proc/f'delitos_web/infracciones_{process}.xlsx', index=False)

# Loop while false
while res['estado'] == False:
    faltantes = list(set(all_procesos) - set(results['causa']))
    res = infraccion_lista_delitos(faltantes)
    results = pd.concat([results, res['df']], ignore_index=True)
    results.to_excel(proc/f'delitos_web/infracciones_{process}.xlsx', index=False)

# Save if true
else:
    results = pd.concat([results, res['df']], ignore_index=True).copy()
    results.to_excel(proc/f'delitos_web/infracciones_{process}.xlsx', index=False)

    print(f'Finally!!!')