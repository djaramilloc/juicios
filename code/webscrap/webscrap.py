from scrap_juicios import scrap_juicios
import time

from bs4 import BeautifulSoup
from selenium import webdriver

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Define options for browser
options = webdriver.FirefoxOptions()
options.page_load_strategy = 'none' # Dont wait page to be loaded
#options.headless = True # do not show browser window

# Start Driver
gecko_path = 'C:/Users/DanielJaramillo/Documents/geckodriver.exe'
driver = webdriver.Firefox(executable_path=gecko_path, options=options)

# Send a request
