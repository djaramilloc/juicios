from pathlib import Path
from pyprojroot import here
import sys
import warnings

import time
from selenium import webdriver
from bs4 import BeautifulSoup

from fake_useragent import UserAgent

from selenium.common.exceptions import ElementNotInteractableException
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd

# Set Paths
root = here()
db = root/'data'

here()

# Load scraper
sys.path.insert(1, (root/'code').as_posix())
warnings.filterwarnings("ignore", category=DeprecationWarning)
from scrap_crimenes import obtener_datos
from scrap_crimenes import ingresar
from scrap_crimenes import tabla_nombre_delitos

# Imagina que antes va a haber una lista de dependencias

