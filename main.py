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
import shutil
from time import sleep
import argparse, sys

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
            fdid = flink.split("=")[1]
            fname = felt.text
            fid = fname.split(".")[0]
            form = fname.split(".")[1]

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

            rval[fdid]= {"category":catagory, 
                        "accession":accession, 
                        "fdate":fdate, 
                        "ddate":ddate, 
                        "link":flink, 
                        "fname":fname, 
                        'name':name, 
                        'format':form,
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
    path = os.path.join(path,"temp")
    os.mkdir(path)
    count = 0
    for ent in ents:
        downloadEnt(ent, path, ents[ent]['format'])

def downloadEnt(ent, path, form, count=0):
    try: reply=get(r'https://elibrary.ferc.gov/eLibraryWebAPI/api/File/DownloadFileNetFile/' + ent, stream=True)
    except: print("Couldn't get file", ent)
    fname = ent + "." + form
    with open(os.path.join(path, fname), 'wb') as file:
            val = file.write(reply.content)
    if val == 0:
        if count == 3:
            print("tried 10 times but couldnt get file breaking")
            return
        print("empty file trying again in 10 seconds", ent)
        sleep(10)
        downloadEnt(ent, path, form, count+1)

def organizeFiles(path, date=False):
    
    with open(os.path.join(path,"manifest.json"),'r') as file: dic = json.load(file)
    for file in os.listdir(os.path.join(path,"temp")):
        srcpath = os.path.join(path,"temp",file)
        if os.path.isdir(srcpath) or file == "manifest.json": continue

        fid = file.split(".")[0]
        if not fid in dic: continue

        if not date: newfolder = os.path.join(path,dic[fid]['format'].lower())
        if date: newfolder = os.path.join(path,dic[fid]['fdate'].replace("/","."), dic[fid]['format'].lower())
        newpath = os.path.join(newfolder,file)  
        print("Moving file", srcpath, "to", newpath)

        if not os.path.exists(newfolder):
            os.makedirs(newfolder)
        
        if os.path.exists(newpath): os.remove(newpath)
        os.rename(srcpath, newpath)
    os.removedirs(os.path.join(path,"temp"))

def createManifest(ents, path):
    with open(os.path.join(path,"manifest.json"), 'w') as file: 
        file.write(json.dumps(ents, indent=4, sort_keys=True))

def splitManifest(path):
    with open(os.path.join(path,"manifest.json"),'r') as file: main = json.load(file)
    for fol in os.listdir(path):
        ids = []
        fjson = {}
        fpath = os.path.join(path,fol)
        if not os.path.isdir(fpath): continue

        for subfol in os.listdir(fpath):
            if not os.path.isdir(os.path.join(fpath,subfol)): continue
            for file in os.listdir(os.path.join(fpath,subfol)):
                ids.append(file.split(".")[0])
        for fid in ids:
            fjson[fid] = main[fid]
        
        with open(os.path.join(fpath,"manifest.json"),'w') as file: 
            file.write(json.dumps(fjson, indent=4, sort_keys=True))
    os.remove(os.path.join(path,"manifest.json"))

parser=argparse.ArgumentParser()
parser.add_argument('--headless', default=False, type=bool)
parser.add_argument('--rootDir', default=os.getcwd(), type=str)
parser.add_argument('--folder', default="downloads", type=str)
parser.add_argument('--type', default="daily", type=str)
parser.add_argument('--folderDelimit', default="\\", type=str)


args=parser.parse_args()
print(args)

print("hi im running")
path = os.path.abspath(args.folder) # path to download folder
if not os.path.exists(path):
    os.makedirs(path)
options = Options()

if args.headless: options.add_argument('--headless')


driver = webdriver.Chrome(chrome_options=options)
driver.get("https://elibrary.ferc.gov/eLibrary/search")
driver.find_element_by_xpath(r'//*[@id="mat-input-6"]').send_keys("P-15056-000")
driver.find_element_by_xpath(r'//*[@id="main"]/app-search/section[2]/div/div/div/div/form/fieldset/div/div[3]/fieldset/div/mat-form-field[2]').click()
if args.type == 'daily':
    driver.find_element_by_xpath(r'//*[@id="mat-option-17"]').click()
if args.type == 'weekly':
    driver.find_element_by_xpath(r'//*[@id="mat-option-18"]').click()
if args.type == 'monthly':
    driver.find_element_by_xpath(r'//*[@id="mat-option-19"]').click()
if args.type == 'all':
    driver.find_element_by_xpath(r'//*[@id="mat-option-22"]').click()



driver.find_element_by_xpath(r'//*[@id="submit"]').click()
waitForLoad(driver)

ents = getEnts(driver)
downloadEnts(ents, path)
createManifest(ents, path)
organizeFiles(path, date=True)
splitManifest(path)

print("finished")
driver.quit()
