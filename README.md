# Webscrap Juicios Ecuador
Web Scrap de los juicios del consejo de la judicatura

## Raw data description
- ```data/raw/clasification_plea_delitos15_20.xlsx```
    -   List of delitos with manual inputation of min and max penalty
- ```data/raw/delitos_2010_2014_gye.xlsx```
    - List with crimes before 2014
- ```data/raw/lista_deliots_15_20.csv```
    - List with penal crimes for 2015-2020

## Folder Structure

The scripts generates two set of files: 1st docs to keep track of the webscrap process, and 2nd the webscraped files itself. The next descrives the folder organization.

```
+-- data/proc
|   +-- estado
|   |   +-- prov_p
|   |   |   +-- courts_status.parquet # One file
|   |   |   +-- cases_court_{c}.parquet # Several files
|   +-- docs
|   |   +-- prov_p
|   |   |   +-- {case_id}
```
The file ```courts_status.parquet``` is a df made for each province, with a list of ids for each courts within the province, and a status column -called ```estado```- to check if the whole province was scrapped or not. 

The file ```cases_court_{c}.parquet``` is a df made for each court c. It is a df with an observation for each case web-scrapped. It has a variable -called ```no_existe```- to indicate if the case exists.

Each downloaded file is stored in the folder {case_id}, which is located within each province folder ```docs/prov_p```

## Download Process

The general idea is to take a court (dependencia judicial) and loop over year
and process id downloading the data. This has to be done in two steps. First for years after 2014 up to 2022. Then between 2010 and 2014. The distinction is because the cases before 2014 are recorded differently.

For each case (proceso) that I download, I need a summary data, containing:
    - Dummy of existence
    - Names
    - Criminal Case
    - Sentencia
    - Acta resumen

If a case appear in this file, it means that I looked for it online and it either appear (dummy of existence ==1) or not, and whether it has relevant data.

Also, I need a file to keep track of the judicaturas. Once a judicatura is done, move the process to the next one.