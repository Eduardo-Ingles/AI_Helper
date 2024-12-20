
import pandas as pd
import time, json
import os, sys, re
import string
import random
import traceback 

project_root = os.getcwd()
sys.path.append(project_root)

from backend.scripts.SharedCode import sharedCode

# ----------------------------------- START COSTANTI -----------------------------------#  
# ----------------------------------- END COSTANTI -----------------------------------# 

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    """
    genera un id di 'size' caratteri da utilizzare (utilizzato in caso il nome del file è troppo lungo)
    """
    return ''.join(random.choice(chars) for _ in range(size))


def mainCall(UploadsFileFolder, DownloadsFileFolder, fileNames, prefix, yieldFlag = True, **kwargs):
    """
    - Unisce in un unico file & sheet tutti gli sheet dei file in input (fileNames).
    - esclude gli sheet indicati in 'excludeSheets'
    """
    links = []
    finalDF = pd.DataFrame(dtype=str)     
    finalDF["input_File"] = None
    finalDF["reference_Sheet"] = None
    
    excludeSheets = kwargs.get("excludeSheets", None)
    if(fileNames):
        if(excludeSheets):
            yield f"Sheet da escludere: {str(excludeSheets)}"
        yield f"\nAttendere...elaborazione di {len(fileNames)} file..."
        
        for indx, fileName in enumerate(fileNames):
            dfs = pd.read_excel(UploadsFileFolder+fileName, sheet_name=None, index_col=None)           
            #if excludeSheets:             
            #    dfs = {key: sheet for key, sheet in dfs.items() if key.strip() not in excludeSheets}
            if excludeSheets:           
                dfs = {key: sheet for key, sheet in dfs.items() if not sharedCode.all_AinB(key, excludeSheets)}
                
            try:
                for skey in dfs.keys():   # skey = sheet keys
                    #if(dfs[skey] not in excludeSheets):
                    for index, row in dfs[skey].iterrows():
                        dfs[skey].loc[index, "input_File"] = fileName
                        dfs[skey].loc[index, "reference_Sheet"] = skey
                    dfs[skey] = dfs[skey][ ["reference_Sheet"] + [ col for col in dfs[skey].columns if col and col != "reference_Sheet"] ]
                    dfs[skey] = dfs[skey][ ["input_File"]  + [ col for col in dfs[skey].columns if col != "input_File"  ] ]
                    #dfs[skey] = dfs[skey].fillna(method='ffill', axis=0)
                    #dfs[skey] = handle_merged_cells(dfs[skey])
                    #dfs[skey] = fill_merged_cells_only(dfs[skey])        
            except Exception as e:
                yield(f"Errore nel file: {fileName} -> sheet: {skey} -> {dfs[skey].columns} |: {str(e)}:")

            df2 = pd.concat(dfs, sort=True)

            finalDF = pd.concat([finalDF, df2])

        yield "\nSalvataggio in corso...\n"
        if(isinstance(fileNames, list)):
            rfile = f"{str(len(fileNames[0].replace(".xlsx","")))}.xlsx" if len(fileNames) != 1 else fileNames[0]
        elif(isinstance(fileNames, str)):
            rfile = f"{str(len(fileNames.replace(".xlsx","")))}.xlsx" if len(fileNames) != 1 else fileNames[0]
    
        prefix += id_generator(6)
        if(sharedCode.rw_xlsx(path = DownloadsFileFolder, file = f"{prefix}-{rfile}", mode = "save", df = finalDF)):
            #link = f"""<a href= "{DownloadsFileFolder}{f"{sharedCode.timeStamp(fullDate = True)}-{prefix}-{rfile}"} target="_blank"">{f"{prefix}-{rfile}"}</a><br>"""
            filePath = f"{DownloadsFileFolder}{prefix}-{rfile}"
            #link = f"""<a href = "{filePath}-{prefix}-{rfile}" target="_blank"">{f"{prefix}-{rfile}"}</a><br>"""
            ylink = {"link": filePath, "linkName": f"{prefix}-{rfile}"}
            links.append(ylink) if ylink not in links else next
            print(f"links -> {links}")
            yield  {"links": links}#f"""<a href= "{DownloadsFileFolder}{f"{sharedCode.timeStamp(fullDate = True)}-{prefix}-{rfile}"} target="_blank"">{f"{prefix}-{rfile}"}</a><br>"""    # da modificare in {"link": current_link}
            yield ""
            
        else:
            yield "Errore nel salvataggio!\nElaborazione fallita!"


if __name__ == "__main__":
    0
    
    
    #<a *ngIf= showLink href="javascript:void(0)"  (click) = "downloadFile(exampleFile)">
	#    <mat-icon>file_copy</mat-icon>
    #    {{exampleFile}}
	#</a>