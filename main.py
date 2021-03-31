from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from requests import get
from selenium.common.exceptions import NoSuchElementException
import os
import json
import re
import logging

def waitForLoad(driver):
    cir_path = r'/html/body/app-root/html/body/div/main/app-search/div/div'
    WebDriverWait(driver,60).until(EC.presence_of_element_located((By.XPATH,cir_path)))
    WebDriverWait(driver,60).until_not(EC.presence_of_element_located((By.XPATH,cir_path)))
    return True

def getEnts(driver):

    cpn_path = r'/html/body/app-root/html/body/div/main/app-search/section[1]/div[3]/div/div/div/table/caption/div/mat-toolbar/div[1]/mat-form-field/div/div[1]/div/mat-select/div/div[1]'
    maxpn_path = r'/html/body/app-root/html/body/div/main/app-search/section[1]/div[3]/div/div/div/table/caption/div/mat-toolbar/div[1]/div[2]'
    
    # get max page number
    try:
        maxpn = driver.find_element_by_xpath(maxpn_path).text.split(" ")[1]
    except NoSuchElementException:
        maxpn = -1

    rval = {}
    while True:
        # get Date, File name, and File ID for each element
        # TODO better error handling
        for elt in driver.find_elements_by_xpath(r'/html/body/app-root/html/body/div/main/app-search/section[1]/div[3]/div/div/div/table/tbody/tr'):
            catagory = elt.find_element_by_xpath(r'./td[1]/span').text
            accession = elt.find_element_by_xpath(r'./td[2]/div/button').text

            fdate = elt.find_element_by_xpath(r'./td[3]/span').text
            ddate = elt.find_element_by_xpath(r'./td[4]/span').text
            
            felt = elt.find_element_by_xpath(r'./td[9]/div/a')
            flink = felt.get_attribute('href')
            fid = flink.split("=")[1]
            fname = felt.text

            ftype = elt.find_element_by_xpath(r'./td[7]/span').text
            ftypeSplit = ftype.split(" | ")
            ftypeMajor = ftypeSplit[0]
            ftypeMinor = ftypeSplit[1]
            desc = elt.find_element_by_xpath(r'./td[6]/span').text
            if ftypeMajor == "Comments/Protest":
                name = re.search(r'Comment?s? of (.*) (?:in|under)', desc).group(1)
            elif ftypeMajor == "Intervention":
                name = re.search(r'Motion to Intervene of (.*) under', desc).group(1)
            else: 
                name = None

            rval[fid]= {"catagory":catagory, 
                        "accession":accession, 
                        "fdate":fdate, 
                        "ddate":ddate, 
                        "link":flink, 
                        "fname":fname, 
                        'name':name, 
                        'desc':desc, 
                        'type':{
                            'major':ftypeMajor,
                            'minor':ftypeMinor, 
                            'full':ftype}
                        }

        if maxpn == -1: break

        # get current page number
        cpn = driver.find_element_by_xpath(cpn_path).text
        if cpn == maxpn: break

        # go to next page
        driver.find_element_by_xpath(r'/html/body/app-root/html/body/div/main/app-search/section[1]/div[3]/div/div/div/table/caption/div/mat-toolbar/mat-paginator/div/div/div[2]/button[2]').click()
        waitForLoad(driver)

    return rval

def downloadEnts(ents, path):
    #ents 0: fname, 1: fdate, 2: fid, 3: flink
    for ent in ents:
        try: reply=get(r'https://elibrary.ferc.gov/eLibraryWebAPI/api/File/DownloadFileNetFile/' + ent[2], stream=True)
        except: print("Couldn't get file", ent)
        with open(os.path.join(path, ents[ent]['fname']), 'wb') as file:
            for chunk in reply.iter_content(chunk_size=1024): 
                if chunk:
                    file.write(chunk)
            
def organizeFiles(path):
    # with open(os.path.join(path,"manifest.json"),'r') as file: dic = json.loads(file)
    for file in os.listdir(path):

        srcpath = os.path.join(path,file)
        if os.path.isdir(srcpath) or file == "manifest.json": continue
        newfolder = os.path.join(path,file.split(".")[1].lower())
        newpath = os.path.join(newfolder,file)

        if not os.path.exists(newfolder):
            os.makedirs(newfolder)
        
        if os.path.exists(newpath): os.remove(newpath)
        os.rename(srcpath, newpath)

def createManifest(ents, path):
    with open(os.path.join(path,"manifest.json"), 'w') as file: 
        file.write(json.dumps(ents, indent=4, sort_keys=True))


path = os.path.abspath("download") # path to download folder
options = Options()
options.add_experimental_option("prefs", {
  "download.default_directory": path,
  "download.prompt_for_download": False,
  "download.directory_upgrade": True,
  "safebrowsing.enabled": True
})
driver = webdriver.Chrome(chrome_options=options)
driver.get("https://elibrary.ferc.gov/eLibrary/search")
driver.find_element_by_xpath(r'//*[@id="mat-input-6"]').send_keys("P-15056-000")
# driver.find_element_by_xpath(r'//*[@id="main"]/app-search/section[2]/div/div/div/div/form/fieldset/div/div[3]/fieldset/div/mat-form-field[2]').click()
# driver.find_element_by_xpath(r'//*[@id="mat-option-17"]').click()
driver.find_element_by_xpath(r'//*[@id="submit"]').click()
waitForLoad(driver)

ents = getEnts(driver)
downloadEnts(ents, path)
organizeFiles(path)
createManifest(ents, path)


driver.quit()
