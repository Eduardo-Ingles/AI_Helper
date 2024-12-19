import os, sys, re
import bisect, copy


project_root = os.getcwd()
sys.path.append(project_root)

from backend.scripts.SharedCode import sharedCode


# ----------------------------------- START COSTANTI -----------------------------------#  

# ------------------------------------- END COSTANTI -----------------------------------# 

"""
Per la normalizzazione dei dati si inizia da una parola 
-> viene eseguita una ricerca nel dizionario fino a trovare un elemento nei [Sinonimi] uguale a quello in input
-> viene dato in output il [Segnale] trovato (oppure descrizione se returnType = descr/sig_descr)
"""

def aliasIndexArray(dictData):
    """
    Ritorna il dizionario ordinato per la ricerca per bisezione 
    """
    synonims = []
    for item in dictData["nodes"]:
        for alias in item["values"]["sinonimi"]:             
            if(len(item["children"]) != 0 or len(item["parents"]) != 0):
                #if(item["values"]["signal"] != ""):
                tempDict = {"alias": alias.strip(), "parent": item["_idName"].strip()}
                synonims.append(tempDict) if tempDict not in synonims else next
    return sorted(synonims, key=lambda x: x["alias"])


def searchSortedDictArrayV2(arr, key, searchString, searchSubString):
    matches = []
    searchSubString = searchSubString.lower().strip()
    for i, item in enumerate(arr):
        value = item[key]
        if isinstance(value, str):
            value = value.lower()
            if "alias" in key:
                # Split the value into individual words/phrases
                aliases = [a.strip() for a in value.replace('-', ' ').split()]
                # Check if any alias starts with the search substring
                if any(alias.startswith(searchSubString) for alias in aliases):
                    matches.append(i)
                # Check if the full searchString matches any alias
                elif searchString and any(sharedCode.all_AinB(alias, searchString.lower().strip()) for alias in aliases):
                    matches.append(i)
            else:
                if value.startswith(searchSubString):
                    matches.append(i)
    return matches if matches else [-1]


def searchSortedDictArray(arr, key, searchString, searchSubString):
    if "alias" in key:
        searchSubString = searchSubString.lower().strip() 
    values = [d[key] for d in arr]
    insertion_point = bisect.bisect_left(values, searchSubString)
    start_index = max(0, insertion_point - 1)
    end_index = min(len(values), insertion_point + 1)
    for i in range(start_index, end_index):
        if("alias" in key ):
            if(" " not in values[i]):
                if isinstance(values[i], str) and values[i].startswith(searchSubString):
                    return i  
            elif(searchString != "" and values[i] != "" and sharedCode.all_AinB(values[i], searchString.lower().strip())):
                return i 
        else:
            if isinstance(values[i], str) and values[i].startswith(searchSubString):
                return i
    return -1 


def normalizzaDati(currentWords, usedDictionary, **kwargs): 
    """
   Normalizza una stringa in input. esempio: varry = normalizzaDati(inputString, dizionario)
    - aliasArray -> se indicato l'array indicizzato degli alias esegue la ricerca per bisezione (veloce), altrimenti esegue la normalizzazione scandendo l'intero array (lento)
    - dataType -> tipo di ritorno dei dati normalizzati: STRING (default) / LIST o ARRAY
    - returnType -> se ritorna il segnale (signal di default) o la descrizione (sig_descr)
    - splitRule -> se non indicata viene caricata automaticamente
   
   """
    dataType = kwargs.get("dataType", None)# if kwargs and "dataType" in kwargs.keys() else "STRING"
    returnType = "signal"
    splitRule = kwargs.get("splitRule") if kwargs and "splitRule" in kwargs.keys() else sharedCode.loadSettings("globalSettings", "splitRule")
    if "returnType" in kwargs.keys():
        if(kwargs.get("returnType").startswith("descr") or "sig_descr" in kwargs.get("returnType")):
            returnType = "sig_descr"

    def secondaryChecK(inStr, inSinonArr):
        for alias in inSinonArr:
            if(" " in alias or "-" in alias):
                if(sharedCode.all_AinB(re.split(r"" + splitRule, alias.lower().strip()), inStr)):
                    return True

    sortedAliasArray = kwargs.get("aliasArray")

    normalizedData = []
    stringa = None
    if(isinstance(currentWords, str)):
        stringa = re.split(r"" + splitRule, currentWords.lower().strip())
    elif(isinstance(currentWords, list)):
        stringa = re.split(r"" + splitRule, (" ".join(currentWords)).lower().strip())

    if(sortedAliasArray):
        for subString in stringa:   
            if(subString != ""):  
                foundIndices = searchSortedDictArrayV2(sortedAliasArray, "alias", " ".join(stringa), subString.strip().lower())
                for foundIndx in foundIndices:
                    if foundIndx != -1:         
                        foundNodeIndex =  searchSortedDictArray(usedDictionary["nodes"], "_idName", currentWords, sortedAliasArray[foundIndx]["parent"])
                        if(foundNodeIndex != -1):
                            if(len(usedDictionary["nodes"][foundNodeIndex]["children"]) != 0 or len(usedDictionary["nodes"][foundNodeIndex]["parents"]) != 0):
                                foundNode = usedDictionary["nodes"][foundNodeIndex]["values"][returnType].strip()
                                flaggy = secondaryChecK(stringa, usedDictionary["nodes"][foundNodeIndex]["values"]["sinonimi"])
                                if(subString.strip().lower() in usedDictionary["nodes"][foundNodeIndex]["values"]["sinonimi"] or flaggy):
                                    normalizedData.append(foundNode) if foundNode not in normalizedData and foundNode != "" else next
    else:
        for subString in stringa:  
            for node_data in usedDictionary.get("nodes", []):
                if(len(node_data["parents"]) != 0 or len(node_data["children"]) != 0):
                    if(len (node_data["values"]["sinonimi"]) != 0): 
                        for alias in node_data["values"]["sinonimi"]:  
                            alias = alias.strip() 
                            if(" " in alias):        
                                if(sharedCode.all_AinB(alias, stringa)):  
                                    if node_data["values"][returnType] not in normalizedData:
                                        normalizedData.append(node_data["values"][returnType].strip())
                            elif subString.strip() == alias.lower():
                                if node_data["values"][returnType] not in normalizedData:
                                    normalizedData.append(node_data["values"][returnType].strip())
      
    #print(normalizedData)   
    if(dataType and ("LIST" in dataType.upper() or "ARRAY" in dataType.upper() and dataType != "")):
        #print(normalizedData)   
        return normalizedData    
    
    else:
        #print(normalizedData)   
        return " ".join(normalizedData).strip()
    
    
def paroleNonCensite(currentWords, indexedDictionary, **kwargs):     
    """
    Ricerca le parole non censite, ritorna sempre una stringa.
    (utilizza il dizionario indicizzato per la ricerca)
    - kwargs: splitRule
    - dataType: LIST / STRING
    """
    splitRule = kwargs.get("splitRule") if kwargs and "splitRule" in kwargs.keys() else sharedCode.loadSettings("globalSettings", "splitRule")  
    dataType = kwargs.get("dataType", None)
    if(not currentWords):
            return None
    stringa = None
    if(isinstance(currentWords,str)):
        stringa = re.split(r"" + splitRule, currentWords.lower().strip())
        stringaRif = re.split(r"" + splitRule, currentWords.lower().strip())
    elif(isinstance(currentWords, list)):        
        stringa = (re.split(r"" + splitRule, (" ".join(currentWords)).lower().strip()))
        stringaRif = copy.copy(currentWords)
    
    for i in range (len(stringa)):
        foundIndx =  searchSortedDictArray(indexedDictionary, "alias", " ".join(stringa), stringa[i].strip().lower())
        if(foundIndx != -1):
            currAlias = indexedDictionary[foundIndx]["alias"].strip().lower()
            if(" " not in currAlias):
                if(stringa[i].strip().lower() == currAlias):
                    stringaRif[i] = ""
            elif(" " in currAlias):
                for tempAlias in currAlias.split():
                    if(stringa[i].strip().lower() == tempAlias):
                        stringaRif[i] = ""
    unique_words = list(set(word.upper() for word in stringaRif))
    if(dataType and dataType == "LIST" ):
        return unique_words
    else:
        return " ".join(((" ".join(unique_words)).strip()).split())


def normalizeByType(startNodes, currentWords, usedDictionary, **kwargs):  
    """
    Normalizza i dati dal nodo di partenza indicato
    - returnType -> signal / sig_descr
    - startNodes -> es: Status_Collection
    - splitRule -> lista caratteri da utilizzare per lo split
    """     
    splitRule = kwargs.get("splitRule") if kwargs and "splitRule" in kwargs.keys() else sharedCode.loadSettings("globalSettings", "splitRule")  
    if(isinstance(currentWords,str)):
        currentWords = re.split(r"" + splitRule, currentWords.lower().strip())
    elif(isinstance(currentWords, list)):
        currentWords = (re.split(r"" + splitRule, (" ".join(currentWords)).lower().strip()))
    
    if(isinstance(startNodes,str)):
        startNodes = startNodes.strip().split()
    elif(isinstance(startNodes, list)):
        startNodes = ((" ".join(startNodes)).strip()).split()
    
    returnType = "signal"
    splitRule = kwargs.get("splitRule") if kwargs and "splitRule" in kwargs.keys() else sharedCode.loadSettings("globalSettings", "splitRule")
    if "returnType" in kwargs.keys():
        if(kwargs.get("returnType").startswith("descr") or "sig_descr" in kwargs.get("returnType")):
            returnType = "sig_descr"


    foundElements = []
    def traversaNodo(startNode):
        for node_data in usedDictionary.get("nodes", []):
            if(startNode == node_data["id"]):   
                if(len(node_data["children"]) != 0):
                    for nodo in node_data["children"]:
                        findAlias(nodo)
                        traversaNodo(nodo)

    def findAlias(currentNode): 
        for node_data in usedDictionary.get("nodes", []):
            if(currentNode == node_data["id"]):     
                for word in currentWords:
                    for alias in node_data["values"]["sinonimi"]:
                        if(" " in alias.strip()):        
                            if(sharedCode.all_AinB(alias.strip().lower(), currentWords)): 
                                if node_data["values"][returnType] not in foundElements:
                                    foundElements.append(node_data["values"][returnType].strip())
                        elif(word.lower() == alias.strip().lower()):
                            if(node_data["values"][returnType] not in foundElements):
                                foundElements.append(node_data["values"][returnType].strip())
    for nodo in startNodes:              
        traversaNodo(nodo.strip())
    return  " ".join((" ".join(foundElements).strip()).split())



if __name__ == "__main__":
    
    dictFolder = sharedCode.loadSettings("paths", "dictFolder") 
    dictFileName = sharedCode.loadSettings("files", "dizionarioMain")
    dictionary = (sharedCode.rw_file(path = dictFolder, file = dictFileName))
    indexedAliasArray = aliasIndexArray(dictionary)
    
    test = "interruttore"
    print("\n")
    print(normalizzaDati(test, dictionary, aliasArray = indexedAliasArray))