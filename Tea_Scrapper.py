# Libraries
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np

# Functions
def ping(url):
    response = requests.get(url)
    
    if response.status_code == 200:
        print("Connected - " + url)
        return response
    elif response.status_code == 404:
        print("Page Not Found")
    else:
        print("Could Not Connect")
    
    return False

def html(page):
    return BeautifulSoup(page.text, 'html.parser')

def getExtParts(html):
    # Set up part url List
    itemExtList = []
    
    # Parse out part urls
    for link in html.find_all('a'):
        if link.get('href') is None:
            pass
        elif 'Item.aspx?FromNo' in link.get('href') and '-' not in link.get('href'):
            itemExtList.append(link.get('href'))
        
    return itemExtList

def qtyClean(string):
    return string.replace('\xa0', ' ').replace('à', '').replace('  ', ' ').split(' ')

def timeClean(string):
    string = string.replace('\xa0', '')
    string = string.replace('minutes', '')
    return [int(x) for x in string.split('-')]

def tempClean(string):
    string = string.replace('°F', '').replace('° F', '')
    lst = [int(x) for x in string.split('-')]
    
    if len(lst) == 2:
        return lst
    elif len(lst) == 1:
        return [lst[0], lst[0]]
    else:
        return [np.nan, np.nan]
    
def servingClean(string):
    return string.split('/')

def getItemInfo(page_html):
    
    # Grab Item Num
    num = page_html.find("div", class_="infos").find_all('div')[0].find('strong').text
    
    # Grab Item name 
    name = page_html.find("div", class_="itemCard").find('h3').text
    
    # Grab Quanity
    qty_temp = page_html.find("div", class_="infos").find_all('div')[1].find('strong').text
    [qty, subUnit, unit, weight ] = qtyClean(qty_temp)
    
    # Grab Brew Time
    try:
        time_temp = page_html.find("div", class_="card-body").find_all('div')[0].text
        [time_min, time_max] = timeClean(time_temp)
    except:
        [time_min, time_max] = [np.nan, np.nan]
    
    # Brew Heat
    try:
        heat_temp = page_html.find("div", class_="card-body").find_all('div')[1].text
        [heat_min, heat_max] = tempClean(heat_temp)
    except:
        [heat_min, heat_max] = [np.nan, np.nan]
    
    # Servering Size
    try:
        ss_temp = page_html.find("div", class_="card-body").find_all('div')[2].text
        [ss_tsp, ss_oz] = servingClean(ss_temp) 
    except:
        [ss_tsp, ss_oz] = [np.nan, np.nan]
        
    # Organic
    strlst = [str(x) for x in page_html.find_all('img')]
    organic = '''<img src="images/image/organic_frei.png"/>''' in  strlst
    
    # Description 
    desc = page_html.find("div", class_="card-body").find('p').text
    
    return [num, name, qty, subUnit, unit, weight, time_min, time_max, heat_min, heat_max, ss_tsp, ss_oz, organic, desc]

# Urls
urlHome = r'https://www.dethlefsen-balk.us/'
extPart = r'ENU/17732/ItemPage.aspx'
extPartNum = lambda x : extPart + r'?Merkmal=&Page=' + str(x)

# Scrape Item Pages
allItemUrls = []
pageNumMax = 63

for pageNum in range(0, pageNumMax):
    page = ping(urlHome+extPartNum(pageNum));
    
    if page == False:
        break
    
    page_html = html(page)
    allItemUrls = allItemUrls + getExtParts(page_html)
    
allItemUrls = list(set(allItemUrls))

# Scrape Info
infoList = []

for ext in allItemUrls:
    page = ping(urlHome+str(ext))
    page_html = html(page)
    infoList.append(getItemInfo(page_html))
    
# Build Data Frame
columns = ['num', 'name', 'qty', 'subUnit', 'unit', 'weight', 'time_min', 'time_max', 'heat_min', 'heat_max', 'ss_tsp', 'ss_oz', 'organic', 'desc']
df = pd.DataFrame(infoList, columns = columns)

df.to_csv('DBT.csv') # Save csv
