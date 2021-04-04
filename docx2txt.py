
import argparse, sys
import os
import pypandoc

parser=argparse.ArgumentParser()

parser.add_argument('--folder', default="downloads", type=str)
args=parser.parse_args()

folder = args.folder

for fold in os.listdir(folder):
    sfold = os.path.join(folder,fold,"DOCX")
    if os.path.exists(sfold) and os.path.isdir(sfold):
        for file in os.listdir(sfold):
            if file[-4:].lower() != "docx": continue
            fpath = os.path.join(sfold,file)
            if file.find(".DOCX") != -1: os.rename(fpath, os.path.join(sfold,file.lower()))
            fpath = os.path.join(sfold,file.lower())
            pypandoc.convert_file(fpath, 'plain', outputfile=fpath.replace(".docx",".TXT"))
            os.rename(fpath,os.path.join(sfold,file.upper()))
