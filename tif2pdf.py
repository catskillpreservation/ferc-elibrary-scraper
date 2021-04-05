
import argparse, sys
import os
import img2pdf


parser=argparse.ArgumentParser()

parser.add_argument('--folder', default="downloads", type=str)
args=parser.parse_args()

folder = os.path.abspath(args.folder) # ./comments

for fold in os.listdir(folder): # ./comments/*
    sfold = os.path.join(folder,fold,"tif")
    if os.path.exists(sfold) and os.path.isdir(sfold):
        for file in os.listdir(sfold):
            if file[-3:].lower() != "tif": continue
            fpath = os.path.join(sfold,file)
            print(fpath)
            try:
                with open(fpath.replace(".TIF",".PDF"),"wb") as f1:
                    f1.write(img2pdf.convert(fpath))
            except:
                print("Cannot convert", file)
                os.remove(fpath.replace(".TIF",".PDF"))
            else: 
                print("Creating", fpath.replace(".TIF",".PDF"))
