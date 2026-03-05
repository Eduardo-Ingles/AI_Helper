#import ollama
#import chromadb

import os, sys, re

project_root = os.getcwd()
sys.path.append(project_root)

from backend.scripts.SharedCode import sharedCode, rulesDefiner, normalizzatore


# ----------------------------------- START COSTANTI -----------------------------------#  

# ----------------------------------- END COSTANTI -----------------------------------# 



def checkConditions(tempitem, stringaIn):
    """
    """
    tempAnyCond = []
    noFlag = False
    anyFlag = False
    for tempAny in tempitem["condAny"]:
        for key in tempAny.keys():
            tempAnyCond.append(tempAny[key])
    if(len(tempitem["condNo"]) != 0):
        for noCond in tempitem["condNo"]:
            if(sharedCode.any_AinB(stringaIn, noCond)):
                noFlag = True
    else:
        noFlag = False
    for anyCond in tempAnyCond:
        if(sharedCode.any_AinB(stringaIn, anyCond)):
            anyFlag = True
        else:
            anyFlag = False
            break               
    if(len(tempAnyCond) == 0):
        anyFlag = True
    if(sharedCode.all_AinB(tempitem["condYes"], stringaIn) and anyFlag and noFlag == False):
        return True


def fillNoCond(arrStringaIn, currResults): 
    def removeTags(inDataArr):
        inDataArr = list(set(inDataArr))
        tags = ["ALR", "ST", "CMD", "MIS", "PAR"]
        for tag in tags:
            inDataArr.remove(tag) if tag in inDataArr else next
        return inDataArr


    AnyCondHolder = []
    for result in currResults:
        for topKey in result.keys():
            for condAny in result[topKey]["condAny"]:
                for varKey in condAny.keys():
                    AnyCondHolder += condAny[varKey]
    AnyCondHolder = removeTags(AnyCondHolder)

    for indx, result in enumerate(currResults):
        for topKey in result.keys():
            tempAny = []
            for condAny in result[topKey]["condAny"]:
                for varKey in condAny.keys():
                    tempAny += condAny[varKey]

            tempYes = result[topKey]["condYes"]
            tempCommon, tempUniqueA, tempUniqueB = sharedCode.compareLists(removeTags(tempAny + tempYes), AnyCondHolder)
            if(tempUniqueB):
                currResults[indx][topKey]["condNo"] += tempUniqueB
                currResults[indx][topKey]["condNo"] = list(set(currResults[indx][topKey]["condNo"]))

    return currResults  


def applyRules(rulesData:dict, normalizedInputString:list, dictionary, indexedAliasArray, **kwargs):
    """kwargs: 
    - include: 'collection' da includere esplicitamente
    - exclude: 'collection' da escludere esplicitamente (es ALR CMD)
    - device: se applicare le regole 'device' oppure no
    > keys: signal -> ritorna il segnale, descr -> ritorna la descrizione
    """
    if(not (rulesData or normalizedInputString or dictionary or indexedAliasArray)):
        return None
    
    include = kwargs.get("include") if "include" in kwargs else None   
    exclude = kwargs.get("exclude") if "exclude" in kwargs else None
    device = kwargs.get("device") if "device" in kwargs else None
    test = kwargs.get("test", None) 
    
    if(include and isinstance(include, str)): 
        include = include.strip().split()
    if(exclude and isinstance(exclude, str)):
        exclude = exclude.strip().split()

    if(normalizedInputString and len(normalizedInputString) != 0):
        results = []
        if(device):
            device = device.strip().split() if isinstance(device, str) else device
            for key in rulesData.keys(): 
                if(rulesData[key]):
                    for itemData in rulesData[key]:
                        if(itemData["devices"] and sharedCode.any_AinB(device, itemData["devices"]) and checkConditions(itemData, normalizedInputString)):
                            results.append({key: itemData}) if {key: itemData} not in results else next        
        
        elif(not results or not device):
            for key in rulesData.keys():    #dict_keys(['ALR_Collection', 'CMD_Collection', 'MIS_Collection', 'PAR_Collection', 'ST_Collection']) 
                if(include or exclude):
                    checkTag = sharedCode.any_AinB(key.replace("_Collection",""), include) and sharedCode.notAny_AinB(key.replace("_Collection",""), exclude)
                    if(checkTag and rulesData[key]):
                        for itemData in rulesData[key]:
                            if(checkConditions(itemData, normalizedInputString)):
                                results.append({key: itemData})
                else:
                    for itemData in rulesData[key]:
                        if(checkConditions(itemData, normalizedInputString)):
                            results.append({key: itemData}) if {key: itemData} not in results else next

        if(len(results) != 0):
            results = fillNoCond(normalizedInputString, results) if len(results) > 1 else results
            auxResultsList = []
            for result in results:
                if(result):
                    for key in result.keys():
                        condResul = sharedCode.notAny_AinB(result[key]["condNo"], normalizedInputString) #if len(result[key]["condNo"]) != 0 else True
                        tempSignal = result[key]["signal"]
                        tempDescr = result[key]["descr"]
                        for tempCondData in result[key]["condAny"]:
                            if("$VAR" in str(tempCondData.keys())):
                               for anyKey in tempCondData.keys():
                                    for item in tempCondData[anyKey]:
                                        if(item in normalizedInputString and str(anyKey) in tempSignal):
                                            tempSignal = tempSignal.replace(str(anyKey), normalizzatore.normalizzaDati(item, dictionary, aliasArray = indexedAliasArray))
                                            tempDescr = tempDescr.replace(str(anyKey), normalizzatore.normalizzaDati(item, dictionary, aliasArray = indexedAliasArray, returnType = "sig_descr"))
                        tempRes = result[key]["signal"].split("-")
                        auxResultsList.append(tempRes) if tempRes not in auxResultsList else next
                        if(test):
                            print(f"{len(results)}\t{condResul}->\ty: {(result[key]["condYes"])}\tn: {result[key]["condNo"]}\ta: {result[key]["condAny"]}\t[{tempSignal}, {tempDescr}]")
                        if(condResul):
                            return {"signal": tempSignal, "descr": tempDescr}
            
            matchy = sharedCode.most_matches(normalizedInputString, auxResultsList)
            if(test):
                print(f">>> {matchy}")
            if(matchy["index"] != -1):
                result = results[matchy["index"]]
                for key in result.keys():
                    tempSignal = result[key]["signal"]
                    tempDescr = result[key]["descr"]
                    for tempCondData in result[key]["condAny"]:
                        if("$VAR" in str(tempCondData.keys())):
                           for anyKey in tempCondData.keys():
                                for item in tempCondData[anyKey]:
                                    if(item in normalizedInputString and str(anyKey) in tempSignal):
                                        tempSignal = tempSignal.replace(str(anyKey), normalizzatore.normalizzaDati(item, dictionary, aliasArray = indexedAliasArray))
                                        tempDescr = tempDescr.replace(str(anyKey), normalizzatore.normalizzaDati(item, dictionary, aliasArray = indexedAliasArray, returnType = "sig_descr"))

                    rdict = {"signal": tempSignal, "descr": tempDescr}
                    return rdict



if __name__ == "__main__":
    rulesPath = sharedCode.loadSettings("paths", "rulesFolder")
    rawRulesFile =  sharedCode.loadSettings("globalSettings", "raw_descrRules") 
    newRulesFile =  sharedCode.loadSettings("globalSettings", "descrRules")
        
    #dictFileName = sharedCode.loadSettings("globalSettings", "mainDictionary")
    #dictFolder = sharedCode.loadSettings("globalSettings", "dictionaryFolderPath") 
    
    dictFolder = project_root + sharedCode.loadSettings("paths", "dictFolder") 
    dictFileName = sharedCode.loadSettings("files", "dizionarioMain")

    dictionary = (sharedCode.rw_file(path = dictFolder, file = dictFileName))
    indexedAliasArray = normalizzatore.aliasIndexArray(dictionary)

    rulesDefiner.creaNuovoFormato(rulesPath, rawRulesFile, newRulesFile)
    currRules = rulesDefiner.loadRulesData(rulesPath, rawRulesFile, newRulesFile)

    if(currRules):
        #print(type(currRules))
    
        inputTest = [
                    "ST TOT FAST MEDIAN NORD TVCC RIL",
                    "ST TOT FAST MEDIAN SUD TVCC RIL",
                    "INT ST CH UPS",
                    "INT ST CH ALIMENT PMV EST",
                    "UPS ST",
                    "GE ST MARCIA G E IN FUNC",
                    "ALR CNTRL CMD TEMP TRAFO 4 QGBT1 CAB MAIN",
                    "ALR GROUP PRESS B CAB MAIN"
                    ]

        #testFunc(inputTest)
        for stringa in inputTest:
            print(f"\n{stringa}")
            #applyRules(currRules, stringa.split(), include = "ST ALR MIS", exclude = "PAR")
            #applyRules(currRules, stringa.split(), include = "MIS PAR", exclude = "PAR")
            #applyRules(currRules, stringa.split(), exclude = "ST ALR")
            result = None
            excluded = None
            #if("ALR" in stringa):
            #    excluded = "ST"
            #
            #if("MIS" in stringa):
            #    excluded = "CMD"
            #
            #if("PAR" in stringa):
            #    excluded = "ALR ST MIS"
            
            if(excluded):
                result = applyRules(currRules, stringa.split(), dictionary, indexedAliasArray, exclude = excluded, test = True)
            else:
                if("SEMAF" in stringa):
                    result = applyRules(currRules, stringa.split(), dictionary, indexedAliasArray, test = True, device = ["SEMAF"])
                elif("SCAR" in stringa):
                    result = applyRules(currRules, stringa.split(), dictionary, indexedAliasArray, test = True, device = ["SCAR"])
                else:
                    result = applyRules(currRules, stringa.split(), dictionary, indexedAliasArray, test = True)
            print(f"result:\t{result}")
            print("-"*40)

