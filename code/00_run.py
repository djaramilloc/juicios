# Master Script

# PACKAGES -----------------------------------------------------------
from pathlib import Path
from pyprojroot import here

# RUN SCRIPTS---------------------------------------------------------
root = here()
codes = root/'code'

program_list = []

# RUN SCRIPTS --------------------------------------------------------

program_list.append(codes/'01_codes_dependencias.py') # Obtain Dependencias/crime codes
# INPUTS
# root/'data/raw/judicaturas/1123_Causas_delitos.xlsx'
# OUTPUT
# root/'data/proc/id_depend_judiciales.csv'