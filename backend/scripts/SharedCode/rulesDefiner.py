import os, sys, re
import traceback 

project_root = os.getcwd()
sys.path.append(project_root)

from backend.scripts.SharedCode import sharedCode


# ----------------------------------- START COSTANTI -----------------------------------#  

# ----------------------------------- END COSTANTI -----------------------------------# 


def extract_and_format(text):
    """
    funzione utilizzata per portare dal vecchio formato delle regole al nuovo: estrazione dei dati in parentesi quadre [] e il testo al di fuori
    """
    pattern = r'\[([^\[\]]+)\]'
    matches = re.findall(pattern, text)
    non_brackets_content = re.sub(r'\[[^\]]*\]', '', text)
    results = []
    offset = (len(matches)-1) if len(matches) > 0 else 0
    for i, match in enumerate(matches):        
        var_name = f"$VAR{chr(65 + offset)}$"
        offset -= 1
        #tempObjy = {"var": var_name, "data": match.split()}
        tempObjy = {var_name: match.split()}
        results.append(tempObjy) if tempObjy not in results else next
    return non_brackets_content, results


def creaNuovoFormato(rulesPath, rawRulesFile, newRulesFile): 
    """
    Funzione utilizzata per convertire dal formato (raw) di 'facile lettura' delle regole nel formato utilizzato per applicare le regole
    """
    oldFormat = sharedCode.rw_file(path = rulesPath, file = rawRulesFile, mode = "load")
    tempDict = {}
    for key in oldFormat.keys():
        tempDict[key] = []
        for data in oldFormat[key]:
            if(not data.startswith("!---")):  
                try:   
                    if(data.count("=") != 1 or data.count(":") != 2):
                        print(data) 
                    devices = ""
                    if("&&" in data):
                        devices = data.split("&&")[1]
                        data = data.split("&&")[0] 
                    tempCond = data.split("=")[0]
                    tempResult = data.split("=")[1]
                    tempYes, tempAny = extract_and_format(tempCond.split(":")[0])
                    protoObj = {
                        "signal": tempResult.split(":")[0].strip().replace("$VAR$", "$VARA$"),
                        "descr": tempResult.split(":")[1].strip().replace("$VAR$", "$VARA$"),
                        "condYes": list((tempYes.replace("(","").replace(")","").split())),
                        "condAny": tempAny,
                        "condNo": (tempCond.split(":")[1]).split(),
                        "devices" : devices.strip().split() if devices != "" else []
                        } 
            
                except Exception as e:
                    print(f"An error occurred: {str(e)}: {data}")
                    traceback.print_exc()
                    
                tempDict[key].append(protoObj) if protoObj not in tempDict[key] else next
        tempDict[key] = sorted(tempDict[key], key=lambda x: x["signal"])

    if(not sharedCode.rw_file(path = rulesPath, file = newRulesFile, mode = "save", data = tempDict)):
        print("\nErrore nel salvataggio dei dati!\n")



def loadRulesData(rulesPath, rawRulesFile, newRulesFile, **kwargs):
    """
    Funzione che crea il nuovo formato, salva sul disco e lo riapre/legge e ritorna le regole.
    """
    creaNuovoFormato(rulesPath, rawRulesFile, newRulesFile) if "create" in kwargs.keys() else next
    signalRules = sharedCode.rw_file(path = rulesPath, file = newRulesFile)
    if(signalRules):
        return signalRules



if __name__ == "__main__":    
    """
    Dopo aver modificato le regole, eseguire questo script!
    """
    rulesPath = sharedCode.loadSettings("paths", "rulesFolder")
    rawRulesFile =  sharedCode.loadSettings("files", "sigRulesRaw") # descrRules
    newRulesFile =  sharedCode.loadSettings("files", "sigRules")
    print("Elaborating...")
    creaNuovoFormato(rulesPath, rawRulesFile, newRulesFile)
    print("!DONE!")