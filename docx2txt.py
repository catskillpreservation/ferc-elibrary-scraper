
import argparse, sys
import os
import pypandoc

parser=argparse.ArgumentParser()

parser.add_argument('--folder', default="downloads", type=str)
args=parser.parse_args()

folder = os.path.abspath(args.folder) # ./comments
print(folder)

for fold in os.listdir(folder): # ./comments/*
    sfold = os.path.join(folder,fold,"docx")
    if os.path.exists(sfold) and os.path.isdir(sfold):
        print(sfold)
        for file in os.listdir(sfold):
            if file[-4:].lower() != "docx": continue
            fpath = os.path.join(sfold,file)
            if file.find(".DOCX") != -1: os.rename(fpath, os.path.join(sfold,file.lower()))
            fpath = os.path.join(sfold,file.lower())
            try: 
                a = pypandoc.convert_file(fpath, 'plain', outputfile=fpath.replace(".docx",".TXT"))
            except:
                print('cannot convert',fpath)
            print("Creating", fpath.replace(".docx",".TXT"))
            os.rename(fpath,os.path.join(sfold,file.upper()))
