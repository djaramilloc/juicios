import pandas as pd
from pyprojroot import here
import sys
import warnings


# Set Paths
root = here()
db = root/'data'

# Load scraper
sys.path.insert(1, (root/'code').as_posix())
warnings.filterwarnings("ignore", category=DeprecationWarning)
from scrap_crimenes import obtener_datos

# Obtener listado de crimenes
delitos = pd.read_csv(db/'proc/lista_delitos.csv')
delitos = list(delitos['NOMBRE DELITO'])

#Obtener listado de dependencias judiciales
db_depen = pd.read_csv(db/'proc/codes_judicaturas.csv')
db_depen = (db_depen
            .loc[db_depen['nombre'] !=  'No se encuentra']
            .reset_index(drop=True)
            .copy())
db_depen['id_dependencia'] = (db_depen['id_dependencia']
                              .apply(lambda x: str(x) if len(str(x))==5 else '0'+str(x)))

# Relevant provinces
guayas = list(db_depen.loc[db_depen['id_dependencia'].apply(lambda x: x.startswith('09')), 'id_dependencia'])
pichincha = list(db_depen.loc[db_depen['id_dependencia'].apply(lambda x: x.startswith('17')), 'id_dependencia'])

num = 17
depnumber = guayas[num]

print(f'Running {depnumber} ({num})')

# Create file
try:
    df_start = pd.read_excel(db/f'proc/delitos_web/delitos_{depnumber}.xls')
except FileNotFoundError:
    df_start = pd.DataFrame()

# First attempt
res = obtener_datos(df_start, depnumber, delitos, ventana=False, delay=3)
df_procesos = pd.concat([df_start, res['df']], ignore_index=True).copy()
df_procesos.to_excel(db/f'proc/delitos_web/delitos_{depnumber}.xls', index=False)

# Loop while false
while res['estado'] == False:
    res = obtener_datos(df_procesos, depnumber, delitos, ventana=False, delay=3)
    df_procesos = pd.concat([df_procesos, res['df']], ignore_index=True).copy()
    df_procesos.to_excel(db/f'proc/delitos_web/delitos_{depnumber}.xls', index=False)

# Save if true
else:
    df_procesos = pd.concat([df_procesos, res['df']], ignore_index=True).copy()
    df_procesos.to_excel(db/f'proc/delitos_web/delitos_{depnumber}.xls', index=False)
    print(f'Finally!!! {depnumber}')