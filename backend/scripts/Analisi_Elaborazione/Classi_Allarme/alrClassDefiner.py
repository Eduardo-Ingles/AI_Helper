
import pandas as pd
import time, json
import os, sys, re
from thefuzz import fuzz
from thefuzz import process

project_root = os.getcwd()
sys.path.append(project_root)

from backend.scripts.SharedCode import sharedCode, normalizzatore#, applyRules, rulesDefiner

#import chromadb
#from llama_cpp import Llama
#from transformers import AutoTokenizer
#tokenizer = AutoTokenizer.from_pretrained("microsoft/Phi-3-mini-4k-instruct")


# ----------------------------------- START COSTANTI -----------------------------------#  

splitRule = sharedCode.loadSettings("globalSettings", "splitRule")

dictionary = (sharedCode.rw_file(path = sharedCode.loadSettings("paths", "dictFolder") , file = sharedCode.loadSettings("files", "dizionarioMain")))
indexedAliasArray = normalizzatore.aliasIndexArray(dictionary)


usedColumns = ["CODICE ALLARME", "normAlrClass", "DESCRIZIONE ALLARME", "normAlrDescr", "IMPIANTO", "NormalizedPlant", "DISPOSITIVO", "NormalizedDevice", "NormalizeData", "leftOvers"]
usedSheet = "RIFERIMENTO"  

excludeList = ["ALR"]
commonMustWords = ["CUM", "TVCC"]


alrClassPath = project_root + sharedCode.loadSettings("paths", "staticData") 

sheet = "RIFERIMENTO"    
alrClassFile = "ALR_CLASS_ANAS"
    
# ----------------------------------- END COSTANTI -----------------------------------# 


def loadData(rawDfs):  
    print("Normalizzazione dati")
    rawDfs[usedSheet]["NormalizedPlant"] = None
    rawDfs[usedSheet]["NormalizedDevice"] = None
    rawDfs[usedSheet]["leftOvers"] = None
    
    rawDfs[usedSheet]["normAlrClass"] = None
    rawDfs[usedSheet]["normAlrDescr"] = None
    rawDfs[usedSheet]["NormalizeData"] = None
    
    for index, row in rawDfs[usedSheet].iterrows():   
        tempPlantNorm = str(normalizzatore.normalizzaDati(str(row["IMPIANTO"]), dictionary, splitRule=splitRule, aliasArray=indexedAliasArray))
        rawDfs[usedSheet].loc[index, "NormalizedPlant"] = (" ".join(list(set(str(tempPlantNorm).split()))).replace("PLANT", "")).strip()
        
        tempDeviceNorm = normalizzatore.normalizeByType(["Device_Collection", "miscItems_Collection"], str(row["DISPOSITIVO"]), dictionary)
        tdevice = (" ".join(list(set(re.split(r"" + splitRule, tempDeviceNorm)))).replace("PLANT", "")).strip()
        rawDfs[usedSheet].loc[index, "NormalizedDevice"] = tdevice 

        tempAlrClassNorm = (str(normalizzatore.normalizzaDati(str(row["CODICE ALLARME"]), dictionary, splitRule=splitRule, aliasArray=indexedAliasArray)))
        rawDfs[usedSheet].loc[index, "normAlrClass"] = (" ".join(list(set(re.split(r"" + splitRule, tempAlrClassNorm)))).replace("PLANT", "")).strip()
        
        tempAlrDescrNorm = (str(normalizzatore.normalizzaDati(str(row["DESCRIZIONE ALLARME"]), dictionary, splitRule=splitRule, aliasArray=indexedAliasArray)))
        rawDfs[usedSheet].loc[index, "normAlrDescr"] = (" ".join(list(set(re.split(r"" + splitRule, tempAlrDescrNorm)))).replace("PLANT", "")).strip()

        tempNorm = (str(normalizzatore.normalizzaDati(f"{str(row["CODICE ALLARME"])} {str(row["DESCRIZIONE ALLARME"])}", dictionary, splitRule=splitRule, aliasArray=indexedAliasArray))).strip()
        rawDfs[usedSheet].loc[index, "NormalizeData"] = (" ".join(list(set(re.split(r"" + splitRule, f"{tdevice} {tempNorm}")))).replace("PLANT", "")).strip()
        
        rawDfs[usedSheet].loc[index, "leftOvers"] = str(normalizzatore.paroleNonCensite(f"{str(row["DISPOSITIVO"])} {str(row["CODICE ALLARME"])} {str(row["DESCRIZIONE ALLARME"])} {str(row["IMPIANTO"])}", indexedAliasArray)).strip()
        
        sharedCode.progress(index, len(rawDfs[usedSheet]))
    
    rawList = list(set(rawDfs[usedSheet].apply(lambda row: json.dumps(
            {col: str(row[col]).strip() for col in usedColumns if col in rawDfs[usedSheet].columns}), axis=1).tolist()))
    rawDictList = []
    for item in rawList:
        jitem = json.loads(item)
        rawDictList.append(jitem) if jitem not in rawDictList and jitem != "" else next
    return rawDictList


def matchymatchy(refStr, dataList:list, **kwargs):
    if(isinstance(refStr, str)):
        refStr = refStr.split()

    def matchScore(listA:list, listB:list):
        strA = len(listA)
        strB = len(listB)
        
        print(f"listA: {listA} | {strA} <<--->> listB: {listB} | {strB}", end = "\t")
        counter = 0
        for sitem in listB:
            if(sharedCode.all_AinB(sitem, listA)):
                counter += 1
                
        print(f"{(counter / strA)*100}")

    keys = kwargs.get("keys", None)

    if(not keys):
        return None
    
    key = keys[0]
    for item in dataList:
        if(sharedCode.any_AinB(refStr, item[key])):
            if(isinstance(item[key], str)):
                item[key] = item[key].split()
            ms = matchScore(refStr, item[key])
            #print(ms)


def digitCheck(inputA, inputB): 
    """
    Controlla se A e B contengono valori numerici
    """  
    if(isinstance(inputA, str)):
        inputA = inputA.split()  
    if(isinstance(inputB, str)):
        inputB = inputB.split()

    aFlag = False
    bFlag = False
    for itemA in inputA: 
        0

    for itemA in inputA:
        if(itemA.isdigit()):
            aFlag = True
    for itemB in inputB:
        if(itemB.isdigit()):
            bFlag = True

    if((aFlag and bFlag) or (not aFlag and not bFlag)):
        return True
    elif((not aFlag and bFlag) or (aFlag and not bFlag)):
        return False


def mainCall(alrClassFile, alrClassPath, inputData, **kwargs):
    rawDict = None
    reWriteFlag = False
    rawDf = None
    if(sharedCode.fileExists(path = alrClassPath, file = "_alrClassFile_")):     
        rawDf = sharedCode.rw_xlsx(path = alrClassPath, file = "_alrClassFile_") 
        rawList = list(set(rawDf.apply(lambda row: json.dumps(
                {col: str(row[col]).strip() for col in usedColumns if col in rawDf.columns}), axis=1).tolist()))
        rawDictList = []
        for item in rawList:
            jitem = json.loads(item)
            rawDictList.append(jitem) if jitem not in rawDictList and jitem != "" else next
        
        reWriteFlag = True
        rawDict = rawDictList

    if(not sharedCode.fileExists(path = alrClassPath, file = alrClassFile)):
        return 
    
    if(not rawDict):
        reWriteFlag = False
        rawDf = sharedCode.rw_xlsx(path = alrClassPath, file = alrClassFile, sheet = "all") 
        rawDict = loadData(rawDf)


    if(isinstance(rawDf, pd.DataFrame) and reWriteFlag == True):
        0
        #rawDf = rawDf.apply(lambda x: pd.Series(x.dropna().values))
        #rawDf = rawDf.fillna('')
        #print(f"Salvataggio: {sharedCode.rw_xlsx(path = downloadsFolderPath, file = "_alrClassFile_", mode = "save", df = {"NormalizedData": rawDf})}")
    elif(isinstance(rawDf[usedSheet], pd.DataFrame) and reWriteFlag == False):
        print(f"Salvataggio: {sharedCode.rw_xlsx(path = alrClassPath, file = "_alrClassFile_", mode = "save", df = rawDf[usedSheet][usedColumns])}")

    device = normalizzatore.normalizeByType(["Device_Collection", "miscItems_Collection"], str(inputData["device"]), dictionary)
    
    normSigDescr = (str(normalizzatore.normalizzaDati(f"{inputData["signal"]} {inputData["descr"]}", dictionary, splitRule=splitRule, aliasArray=indexedAliasArray))).strip()
    normdata = (" ".join(list(set(f"{device} {normSigDescr}".split())))).strip()

    subSetHolder = []
    tdevice = []
    tclass = []
    tdescr = []
    tnorm = []
    tempResults = []
    tempResultsClass = []

    #check description
    for dictItem in rawDict:
        if(dictItem["NormalizedDevice"] != "" and sharedCode.any_AinB(device, dictItem["NormalizedDevice"], exclude = ["ALR"])):
            #digitCheck()
            if(dictItem["DESCRIZIONE ALLARME"].lower() == inputData["descr"].lower() and digitCheck(normdata, dictItem["NormalizeData"]) and (dictItem["leftOvers"] == "" or dictItem["leftOvers"] == "nan")):
                tempResults.append(dictItem) if dictItem not in tempResults else next
    
    if(len(tempResults) != 0):
        if(len(tempResults) == 1):
            return tempResults[0]
        if(len(tempResults) > 1):
            #print(f"0_B: {tempResults[0]}") # Check & Implement!
            0

    if(len(tempResults) == 0):
        for dictItem in rawDict:
            """confrontare all_AinB -> se fallisce, cercare solo elementi presenti | rimuoverli da normData -> fallback a any_AinB """
            if(dictItem["NormalizedDevice"] != "" 
                and (sharedCode.all_AinB(device, dictItem["NormalizedDevice"], exclude = ["ALR"]) or sharedCode.all_AinB(dictItem["NormalizedDevice"], device, exclude = ["ALR"]))
                and sharedCode.any_AinB(normdata, dictItem["NormalizeData"], exclude = ["ALR"] + device.split()) 
                and digitCheck(normdata, dictItem["NormalizeData"])
                and (dictItem["leftOvers"] == "" or dictItem["leftOvers"] == "nan")):
                tempResults.append(dictItem) if dictItem not in tempResults else next
                tdescr.append(dictItem["DESCRIZIONE ALLARME"]) if dictItem["DESCRIZIONE ALLARME"] not in tdescr else next
    
        if(len(tempResults) == 1):
            return tempResults[0]
        
        if(len(tempResults) > 1):                         
            extrDescr = process.extract(inputData["descr"], tdescr, limit=5, scorer=fuzz.token_set_ratio)
            if(extrDescr):       
                for dictItem in rawDict:
                    for item in extrDescr:
                        if(item[0].lower() == dictItem["DESCRIZIONE ALLARME"].lower()):
                            tclass.append(dictItem["normAlrDescr"]) if dictItem["normAlrDescr"] not in tclass else next
                            tempResultsClass.append(dictItem) if dictItem not in tempResultsClass else next
                
                if(len(tempResultsClass) != 0 and tempResultsClass == 1):
                    return tempResultsClass[0]
                elif(len(tempResultsClass) != 0 and tempResultsClass != 1):
                    for item in tclass:
                        if(sharedCode.all_AinB(item, normdata, exclude = ["ALR", "NONE"])):
                            for data in tempResultsClass:
                                if(data["normAlrDescr"] == item):
                                    return data
                
    if(len(tempResults) == 0):
        for dictItem in rawDict:
            """confrontare all_AinB -> se fallisce, cercare solo elementi presenti | rimuoverli da normData -> fallback a any_AinB """
            if(dictItem["NormalizedDevice"] != "" and sharedCode.all_AinB(device, dictItem["NormalizedDevice"], exclude = excludeList) 
                and digitCheck(normdata, dictItem["NormalizeData"])
                and (dictItem["leftOvers"] == "" or dictItem["leftOvers"] == "nan")):
                tempResults.append(dictItem) if dictItem not in tempResults else next
                tdescr.append(dictItem["DESCRIZIONE ALLARME"]) if dictItem["DESCRIZIONE ALLARME"] not in tdescr else next
    
        if(len(tempResults) == 1):
            return tempResults[0]
        
        if(len(tempResults) > 1): 
            extrDescr = process.extract(inputData["descr"], tdescr, limit=5, scorer=fuzz.token_set_ratio)
            if(extrDescr): 
                tempResults2B = []   
                for dictItem in rawDict:
                    for item in extrDescr:
                        if(item[0].lower() == dictItem["DESCRIZIONE ALLARME"].lower()):
                            tclass.append(dictItem["normAlrDescr"]) if dictItem["normAlrDescr"] not in tclass else next
                            tempResultsClass.append(dictItem) if dictItem not in tempResultsClass else next
                            foundFlag = False
                            for sitem in tempResults2B:
                                if(dictItem["normAlrDescr"] in sitem["normAlrDescr"]):
                                    foundFlag = True
                            if(not foundFlag):
                                tempResults2B.append(dictItem) if dictItem not in tempResults2B else next
                if(len(tempResults2B) == 1):
                    return tempResults2B[0]

    if(len(tempResults) == 0):        
        for dictItem in rawDict:
            if(dictItem["NormalizeData"] != "" and sharedCode.any_AinB(normdata, dictItem["NormalizeData"], exclude = ["ALR", "NONE"]) 
               and (dictItem["leftOvers"] == "" or dictItem["leftOvers"] == "nan")):
                tempResults.append(dictItem) if dictItem not in tempResults else next
                tdescr.append(dictItem["DESCRIZIONE ALLARME"]) if dictItem["DESCRIZIONE ALLARME"] not in tdescr else next

        if(len(tempResults) == 1):
                return tempResults[0]

        if(len(tempResults) > 1):
            extrDescr = process.extract(inputData["descr"], tdescr, limit=5, scorer=fuzz.token_set_ratio)
            if(extrDescr):  
                tempResults2 = []     
                tclass = []         
                for tempResult in tempResults:    
                    for item in extrDescr:
                        if(item[0] == tempResult["DESCRIZIONE ALLARME"] and sharedCode.any_AinB(tempResult["NormalizedDevice"], device)):     
                            tempResults2.append(tempResult) if tempResult not in tempResults2 else next
                            tclass.append(tempResult["CODICE ALLARME"]) if tempResult["CODICE ALLARME"] not in tclass else next      
                extrSignal = process.extract(inputData["signal"], tclass, limit=4, scorer=fuzz.token_set_ratio)    
                signalsList = []
                [signalsList.append(" ".join(re.split(r""+splitRule, item[0]))) for item in extrSignal]
                for tempResult in tempResults2:
                            if(([sharedCode.all_AinB(normSigDescr, normalizzatore.normalizzaDati(signalList, dictionary, splitRule=splitRule, aliasArray=indexedAliasArray)) for signalList in signalsList]) 
                               and ((sharedCode.any_AinB(commonMustWords, normdata, exclude = excludeList) and sharedCode.any_AinB(commonMustWords, tempResult["NormalizeData"], exclude = excludeList)) 
                                or (not sharedCode.any_AinB(commonMustWords, normdata, exclude = excludeList) and not sharedCode.any_AinB(commonMustWords, tempResult["NormalizeData"], exclude = excludeList))) ):
                                compareAB = sharedCode.compareLists(normSigDescr, tempResult["normAlrClass"] + " " + tempResult["normAlrDescr"])
                                if(len(compareAB[1]) == 0):
                                    return tempResult


    """
        1) Device in NormalizedDevice
        2) normData in NormalizeData
            if one match -> return
        3) compare: A: [CODICE ALLARME] & signal + B: [DESCRIZIONE ALLARME] & descr
            if multiple compare best match A & B 
    """
    
def alrClassFiller(df):
    # unused
    for index, row in df.iterrows():
        tempDfDevice = str(row["NewDevice"]).strip()
        tempDfProfile = str(row["NewProfileName"]).strip()
        tempDfSignal = str(row["NewSignalName"]).strip()
        tempDfSignalDescr = str(row["NewSignalDescription"]).strip()
        
        currentAlrClass = str(row["NewAlarmClass"]).strip()
        if(currentAlrClass != "" and currentAlrClass != "nan"):
            if(tempDfDevice and (tempDfDevice == "nan" or tempDfDevice == "")):
                tempDfDevice = tempDfProfile
            if(tempDfDevice and tempDfDevice != "nan" and tempDfSignal and tempDfSignal != "nan" and tempDfSignalDescr and tempDfSignalDescr != "nan"):
                inputData = {"device": tempDfDevice, "signal": tempDfSignal, "descr": tempDfSignalDescr}            
                result = mainCall(alrClassFile, alrClassPath, inputData) 
                if(result):
                    df.at[index, "NewAlarmClass"] = result["CODICE ALLARME"]
                    df.at[index, "NewAlarmDescription"] = result["DESCRIZIONE ALLARME"]
                    print (f"{inputData} -> {result["DISPOSITIVO"]}: {result["CODICE ALLARME"]} - {result["DESCRIZIONE ALLARME"]}") if(result) else print()
                    print("-"*50)  
        
      
if __name__ == "__main__":
    #alrClassPath = project_root + sharedCode.loadSettings("paths", "staticData") 
    #
    #sheet = "RIFERIMENTO"    
    #alrClassFile = "ALR_CLASS_ANAS"
    
    testData = [{"device": "CUPONEDDI-QP2S-INT-TEST-INT-BOX-3S-CE-01", "signal": "ALR-INT", "descr": "Allarme interruttore"},
                {"device": "CUPONEDDI-QP2S-INT-QAB27-INT-BOX-3S-CE-01", "signal": "ALR-INT-SCATT", "descr": "Allarme interruttore scattato"},
                {"device": "SCAR-QP-N", "signal": "ALR-SCAR", "descr": "Allarme scaricatore"},
                {"device": "CUPONEDDI-QP1N-INT-QAB3-ILLUMINAZIONE-PIAZZOLA-CE-01", "signal": "ALR-INT-SCATT", "descr": "Allarme interruttore scattato"},
                {"device": "CUPONEDDI-CENTRALE-FIBROLASER-CE-01", "signal": "ALR-INCEND-SUD", "descr": "Allarme incendio sud"},
                {"device": "CUPONEDDI-CENTRALE-FIBROLASER-CE-01", "signal": "ALR-INCEND-NORD", "descr": "Allarme incendio nord"},
                {"device": "CUPONEDDI-CENTRALINA-ANTINCENDIO", "signal": "ALR-FAULT-CNTRL-RIL", "descr": "Allarme guasto centralina rilevamento incendio"},
                {"device": "CUPONEDDI-ZONA-INCENDIO-01-SUD", "signal": "ALR-GRADIENT-ZON-1", "descr": "Allarme gradiente zona 1"},
                #{"device": "CUPONEDDI-ZONA-INCENDIO-02-SUD", "signal": "ALR-GRADIENT-ZON-2", "descr": "Allarme gradiente zona 2"},
                #{"device": "CUPONEDDI-ZONA-INCENDIO-03-SUD", "signal": "ALR-GRADIENT-ZON-3", "descr": "Allarme gradiente zona 3"},
                #{"device": "CUPONEDDI-ZONA-INCENDIO-04-SUD", "signal": "ALR-GRADIENT-ZON-4", "descr": "Allarme gradiente zona 4"},
                #{"device": "CUPONEDDI-ZONA-INCENDIO-05-SUD", "signal": "ALR-GRADIENT-ZON-5", "descr": "Allarme gradiente zona 5"},
                ]
		

    inData = {'device': 'CUPONEDDI-QP2S-INT-QAB27-INT-BOX-3S-CE-01', 'signal': 'ALR-INT-SCATT', 'descr': 'Allarme interruttore scattato'}# - CE01 INT BOX CE | CE01 INT BOX CE ALR SCATT --->
    
    vals = [{'CODICE ALLARME': 'ALR_QIG_SCATTATO_INT', 'DESCRIZIONE ALLARME': 'Allarme interruttore', 'IMPIANTO': 'Impianto elettrico', 'NormalizedPlant': 'ELETTRIC ', 'DISPOSITIVO': 'Interruttore', 'NormalizedDevice': 'INT', 'NormalizeData': 'ALR INT SCATT', 'leftOvers': ''}        
            ,{'CODICE ALLARME': 'ALR_INT', 'DESCRIZIONE ALLARME': 'Allarme Interruttore ', 'IMPIANTO': 'Impianto elettrico', 'NormalizedPlant': 'ELETTRIC ', 'DISPOSITIVO': 'Interruttore', 'NormalizedDevice': 'INT', 'NormalizeData': 'ALR INT', 'leftOvers': ''}
            ]
    
    choices = ["ALR_QIG_SCATTATO_INT", "ALR_INT"]
    #print(process.extractOne("ALR-INT-SCATT", choices))

    #print(fuzz.token_sort_ratio("fuzzy was a bear", "fuzzy fuzzy was a bear"))
    #print(fuzz.token_set_ratio("fuzzy was a bear", "fuzzy fuzzy was a bear"))
    
    #for inputData in testData:
    #    mainCall(alrClassFile, uploadsFolderPath, downloadsFolderPath, inputData)
    #    print("-"*30)  

    #res = sharedCode.most_matches("ALR SCAR".split(), ["SCAR OF TENS ALR SOVRATENS", "SOVRATENS SCAR OF ALR", "SCAR OF TENS ALR SOVRATENS INT"])
    #print(res)
    for inputData in testData:
        result = mainCall(alrClassFile, alrClassPath, inputData) 
        print (f"{result["DISPOSITIVO"]}: {result["CODICE ALLARME"]} - {result["DESCRIZIONE ALLARME"]}") if(result) else print()
        print("-"*50)    
        #input()
        #break

    #dfTest = sharedCode.rw_xlsx(path = uploadsFolderPath, file = "_elaborato_profili__elaborato_sorgente_MODBUS TCPIP Rmt Plc Galleria Cuponeddi merged 3_FEDE_rev1", mode = "load", sheet = 0)
    ##print(dfTest.head())
    #for index, row in dfTest.iterrows():
    #    if(str(row["tags"]) == "[Alarms]" and (str(row["signalDescription"]) != "nan" and str(row["signalDescription"]) != "") and (str(row["profileName"]) != "nan" and str(row["profileName"]) != "")):
    #        if((str(row["alarmClass"]) == "nan") or (str(row["alarmClass"]) == "")):
    #            inputData = {"device": str(row["profileName"]), "signal": str(row["signalName"]), "descr": str(row["signalDescription"])}
    #            result = mainCall(alrClassFile, uploadsFolderPath, downloadsFolderPath, inputData)
    #            if(result):
    #                dfTest.loc[index, "alarmClass"] = result["CODICE ALLARME"]
    #                dfTest.loc[index, "alarmDescription"] = result["DESCRIZIONE ALLARME"]
    #    
    #    sharedCode.progress(index, len(dfTest))
#
    #print(f"save: {sharedCode.rw_xlsx(path = downloadsFolderPath, file = f"test_file_elaborato.xlsx", df= dfTest, mode = "save")}")
    
    
    #SCENAR-DIR-SUD	ST-SCENAR-PREALR-INCEND-SUD	Stato scenario preallarme incendio sud
    #SCENAR-DIR-SUD	ALR-VEHICL-STOP-CORS-SUD	Allarme veicolo arresto corsia sud
    #CUPONEDDI-SOS-01N	ALR-CALL-118	Allarme chiamata 118
    #CUPONEDDI-SOS-01N	ALR-CALL-113	Allarme chiamata 113
    #CUPONEDDI-SOS-01N	ALR-CALL-115	Allarme chiamata 115
    #CUPONEDDI-SOS-01N	ALR-CALL-ANAS	Allarme chiamata anas
    #CUPONEDDI-SOS-01N	ALR-SOS-DOOR	Allarme porta SOS
    #CUPONEDDI-SOS-01N	ALR-PRELIEV-EXTING	Allarme prelievo estintore
    #CUPONEDDI-SOS-01N	ALR-PRELIEV-EXTING	Allarme prelievo estintore
    #CUPONEDDI-SOS-01N	ALR-PRELIEV-HOSE	Allarme prelievo manicchetta
    #CUPONEDDI-SOS-01N	ALR-GENERALE-SOS	Allarme generale SOS
    #CUPONEDDI-SOS-01N	ALR-LAMPEG	Allarme lampeggiante
    #CUPONEDDI-SOS-01N	ALR-INT-SCATT-CUM	Allarme cumulativo interruttore scattato
    #CUPONEDDI-SOS-01N	ALR-INT-SCATT-CUM	Allarme cumulativo interruttore scattato

# >>> collection: notificationClass

#Token Set Ratio
""">>> fuzz.token_sort_ratio("fuzzy was a bear", "fuzzy fuzzy was a bear")
    84
>>> fuzz.token_set_ratio("fuzzy was a bear", "fuzzy fuzzy was a bear")
    100
Process
>>> choices = ["Atlanta Falcons", "New York Jets", "New York Giants", "Dallas Cowboys"]
>>> process.extract("new york jets", choices, limit=2)
    [('New York Jets', 100), ('New York Giants', 78)]
>>> process.extractOne("cowboys", choices)
    ("Dallas Cowboys", 90)"""