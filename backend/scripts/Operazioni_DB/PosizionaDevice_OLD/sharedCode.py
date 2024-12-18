# sharedCode
from datetime import datetime
from openpyxl import load_workbook, Workbook
from bson import ObjectId 
import pandas as pd
import bisect
import sys
import os
import re
import traceback
import json
import copy
from bson import json_util

project_root = os.getcwd()

settingsFileName = "settings"# + ".json"
settingsFolder = "\\scripts\\fileAusiliari\\settings\\"



def defineDeviceName(df, index, row):
    0


def currentTimeHMS(prefix):    
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print(f"\nCurrent Time {prefix} = {current_time}")

# lettura nel DB e ritorno della collezione: se ID è specificato ritorna l'elemento trovato, altrimenti tutti gli elementi del DB indicato    
def readDB_wID(currentDB, collectionName, specificID, specificName):
    collection = currentDB[collectionName] # Find all the documents in the collection
    if(specificID == "" and specificName == ""):
        collezione = collection.find()                          #find() returns a cursor
    elif(specificName == ""):
        collezione = collection.find_one({"_id": specificID})   #find_one() which returns a dictionary
    elif(specificName != "" and specificID == ""):
        collezione = collection.find_one({"name": specificName}) 
    return collezione

# lettura nel DB e ritorno della collezione: se ID è specificato ritorna l'elemento trovato, altrimenti tutti gli elementi del DB indicato    
def readDB_wIDv2(currentDB, collectionName, specificID, specificName, specificDescription):
    collection = currentDB[collectionName] # Find all the documents in the collection
    if(specificID == "" and specificName == "" and specificDescription == ""):
        collezione = collection.find()                          #find() returns a cursor
    elif(specificName == "" and specificDescription == ""):
        collezione = collection.find_one({"_id": specificID})   #find_one() which returns a dictionary
    elif(specificName != "" and specificID == "" and specificDescription == ""):
        collezione = collection.find_one({"name": specificName}) 
    elif(specificName == "" and specificID == "" and specificDescription != ""):
        collezione = collection.find_one({"description": specificDescription}) 
    return collezione


def readCollectionData(currentDB, collectionName:str, **kwargs):
    id = kwargs.get("id")
    name = kwargs.get("name")
    description= kwargs.get("description")
    collection = currentDB[collectionName] # Find all the documents in the collection
    if(not id and not name and not description):
        result = collection.find()         #find() returns a cursor
    elif(id and not name and not description):
        result = collection.find_one({"_id": ObjectId(id)})
    elif(not id and name and not description):
        result = collection.find_one({"name": name}) 
    elif(not id and not name and description):
        result = collection.find_one({"description": description}) 
    return result



def defineChunkSize(CpuCores, dataSetSize):
    chunk_size = int(dataSetSize / CpuCores)
    remainder = dataSetSize % CpuCores
    chunks = []
    start_index = 0
    for i in range(CpuCores):
        end_index = start_index + chunk_size
        if i < remainder:   # Distribute the remainder across the first few chunks
            end_index += 1
        chunks.append((start_index, end_index))
        start_index = end_index
    return chunks


def chunkSize(elementDim, num_processes):    # deprecated
    chunk_size = int(elementDim / num_processes)
    remainder = elementDim % num_processes
    chunks = []
    start_index = 0
    for i in range(num_processes):
        end_index = start_index + chunk_size
        if i < remainder:  # Distribute the remainder across the first few chunks
            end_index += 1
        chunks.append((start_index, end_index))
        start_index = end_index
    return chunks



def excel_column_letter(column_number):
    result = ""
    while column_number > 0:
        column_number, remainder = divmod(column_number - 1, 26)
        result = chr(65 + remainder) + result
    return result


# tempo attuale in ms
def get_current_time():
    current_time_ms = int(datetime.now().timestamp() * 1000)
    return current_time_ms

# array di stringhe in input, stgringa in output
def joinArray(arrIn):                                                                                         
    tempVal = " ".join(sorted(set(arrIn), key = arrIn.index))
    return tempVal.strip()

def iteraDocs(collezione):
    for document in collezione:
        #print(document)
        print(json_util.dumps(document, indent = 4))

# verifica se l'ID è univoco
def checkUniqueID(client, collection, curr_ID):
    #collection = readDB_wID(client, "smartscada", "group", "")
    collectionArray = loadIds(collection)
    flag = -1
    for i in range(len(collectionArray)):
        if(collectionArray[i] == curr_ID):
            flag = i
    if (flag != -1):
        print("ID già esistente!:", collectionArray[flag])
        return True
    else:
        print("ID univoco!:", curr_ID)
        return False
    
  #carica tutti gli ID in un array per confronto
def loadIds(collezione):
    array = []
    for document in collezione:
        array.append(f"{document['_id']}")
    return array  

#carica i nodi da file json (path + filename),  flag = True crea il file se non esiste
def dataLoaderJson(filepath, fileName, flag):
    try:
        if(not filepath.endswith("\\")):
            filepath += "\\"
        if(".json" not in fileName):
            fileName += ".json"
        with open(filepath + fileName, encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        if(flag == True):
            data = {}# {"nodes": []}  
            with open(filepath + fileName, 'w', encoding="utf-8") as new_file:
                json.dump(data, new_file)
            return data
        

def saveToFileJson(saveFileName, data):    
    if(".json" not in saveFileName):
        saveFileName += ".json"
    with open(saveFileName , 'w', encoding="utf-8") as json_file:
        json.dump(data, json_file, ensure_ascii=False, sort_keys=True)


def saveToTxtFile(saveFileName, data):
    if(".txt" not in saveFileName):
        saveFileName += ".txt"
    file = open(saveFileName , 'w', encoding="utf-8")
    file.write(data)
    file.close()


def progress(count:int, total:int, status = ''):                                                                  
    bar_len = 40
    filled_len = int(round(bar_len * count / float(total)))
    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)
    sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', status))
    sys.stdout.flush() 
    

def dataLoaderXlsx(filepath, fileName, sheet):
    try:        
        if(filepath != "" and not filepath.endswith("\\")):
            filepath += "\\"
        if(".xlsx" not in fileName):
            fileName = fileName + ".xlsx"
        if(not fileName.startswith("\\") and filepath != "" and not filepath.endswith("\\")):
            fileName =  "\\" + fileName 
        df = pd.read_excel(filepath + fileName, sheet_name = sheet, dtype = str) if (sheet != None and sheet != "") else pd.read_excel(filepath + fileName)
    except IndexError:
        print("No worksheets found at index 0.")
    return df


def compareLists(listA, listB):
    # Convert lists to sets
    if(isinstance(listA, str)):
        listA = listA.split()
    if(isinstance(listB, str)):
        listB = listB.split()
    set1 = set(listA)
    set2 = set(listB)
    # Find intersection (elements that are the same)
    common_elements = set1.intersection(set2)
    # Find differences (elements that are not the same)
    unique_to_str1 = set1.difference(set2)
    unique_to_str2 = set2.difference(set1)
    return list(common_elements), list(unique_to_str1), list(unique_to_str2)


def split_string_CM(s):
    # Split the string into segments
    segments = re.findall(r"[A-Z]+(?=[a-z]|\d|\W|$)|[A-Z]?[a-z]+|\d+|[A-Z]+", s)

    # Process segments to handle special cases
    result = []
    i = 0
    while i < len(segments):
        # Handle uppercase followed by number
        if i + 1 < len(segments) and segments[i].isupper() and segments[i + 1].isdigit():
            result.append(segments[i] + segments[i + 1])
            i += 2
        # Handle single uppercase letter followed by lowercase
        elif (
            len(segments[i]) == 1 and segments[i].isupper() and i + 1 < len(segments) and segments[i + 1][0].islower()
        ):
            result.append(segments[i] + segments[i + 1])
            i += 2
        else:
            result.append(segments[i])
            i += 1

    return " ".join(result)


def extractCamelCase(inputString:str, **kwargs):
    def classicStringSplit(s):
        s = s.lstrip('$')    
        parts = re.findall(r'[A-Z]+(?=[A-Z][a-z]|\d|\W|$)|\d+|[A-Z][a-z]*', s)  
        for part in parts:  
            tempJoinpart = "".join(re.findall(r'[a-z][A-Z]*|\d+', part)) 
            parts.append(tempJoinpart) if tempJoinpart != "" and tempJoinpart not in parts else next
        results = []
        for part in parts:
            results.append(part)
            if re.search(r'[A-Z][a-z]*\d+', part):
                alpha_part = re.match(r'[A-Z][a-z]*', part)
                num_part = re.search(r'\d+', part)
                if alpha_part:
                    results.append(alpha_part.group())
                if num_part:
                    results.append(num_part.group())  
        return results

    def newStringSplit(s):    
        segments = re.findall(r"[A-Z]+(?=[a-z]|\d|\W|$)|[A-Z]?[a-z]+|\d+|[A-Z]+", s)
        result = []
        i = 0
        while i < len(segments):
            if i + 1 < len(segments) and segments[i].isupper() and segments[i + 1].isdigit():
                result.append(segments[i] + segments[i + 1])
                i += 2
            elif (
                len(segments[i]) == 1 and segments[i].isupper() and i + 1 < len(segments) and segments[i + 1][0].islower()
            ):
                result.append(segments[i] + segments[i + 1])
                i += 2
            else:
                result.append(segments[i])
                i += 1
        return result   
    
    if(inputString != ""):
        if(kwargs and "list" in kwargs.get("return")):
            return list(set(classicStringSplit(inputString) + newStringSplit(inputString)))
        else:        
            return " ".join(list(set(classicStringSplit(inputString) + newStringSplit(inputString))))
    else:
        return None


def search_sorted_array_of_dicts(arr, key, searchString):
    # Extract the values of the specified key from the dictionaries
    values = [d[key] for d in arr]
    #for value in values:
    #    print(value)
    #input()
    # Find the insertion point for the target string
    insertion_point = bisect.bisect_left(values, searchString)
    # Initialize the range of elements to search within
    start_index = max(0, insertion_point - 1)
    end_index = min(len(values), insertion_point + 1)
    # Iterate over the potential range of elements
    for i in range(start_index, end_index):
        # Check if the current value matches the target string or its variations
        if isinstance(values[i], str) and values[i].startswith(searchString):
            return i  # Return the index of the found match
    return -1  # Return -1 if the target string is not found


# normalizza i dati in input in base al dizionario fornito
# returnType: signal / sig_descr
def normalizeByType_Old(startNodes, returnType, currentWords, dictData, splitRule):
    foundElements = []
    def traversaNodo(startNode):
        currNodeIndex = search_sorted_array_of_dicts(dictData.get("nodes", []), "id", startNode)
        if(currNodeIndex != -1):
            node_data = dictData.get("nodes", [])[currNodeIndex]
            if(len(node_data["children"]) != 0):
                for nodo in node_data["children"]:
                    findAlias(nodo)
                    traversaNodo(nodo)
        #for node_data in dictData.get("nodes", []):
        #    if(startNode == node_data["id"]):   
        #        if(len(node_data["children"]) != 0):
        #            for nodo in node_data["children"]:
        #                findAlias(nodo)
        #                traversaNodo(nodo)

    def findAlias(currentNode): 
        currNodeIndex = search_sorted_array_of_dicts(dictData.get("nodes", []), "id", currentNode)
        if(currNodeIndex != -1):
            node_data = dictData.get("nodes", [])[currNodeIndex]
            stringa = re.split(r"" + splitRule, currentWords.lower()) 
            for word in stringa:
                for alias in node_data["values"]["sinonimi"]:
                    if(" " in alias.strip()):        
                        if(all_in_one(alias.strip().lower(), currentWords.lower(), splitRule)): 
                            if node_data["values"][returnType] not in foundElements:
                                foundElements.append(node_data["values"][returnType].strip())
                    elif(word.lower() == alias.strip().lower()):
                        if(node_data["values"][returnType] not in foundElements):
                            foundElements.append(node_data["values"][returnType].strip())
        #for node_data in dictData.get("nodes", []):
        #    if(currentNode == node_data["id"]):     
        #        stringa = re.split(r"" + splitRule, currentWords.lower()) 
        #        for word in stringa:
        #            for alias in node_data["values"]["sinonimi"]:
        #                if(" " in alias.strip()):        
        #                    if(all_in_one(alias.strip().lower(), currentWords.lower(), splitRule)): 
        #                        if node_data["values"][returnType] not in foundElements:
        #                            foundElements.append(node_data["values"][returnType].strip())
        #                elif(word.lower() == alias.strip().lower()):
        #                    if(node_data["values"][returnType] not in foundElements):
        #                        foundElements.append(node_data["values"][returnType].strip())
    for nodo in startNodes.split(" "):              
        traversaNodo(nodo.strip())
    return  " ".join((" ".join(foundElements).strip()).split())


def normalizeAllByKey(returnType, currentWords, dictData, aliasArr, splitRule): #deprecated name
    normalizedData = []
    stringa = re.split(r"" + splitRule, currentWords.lower())
    for subString in stringa:
        foundIndx =  search_sorted_array_of_dicts(aliasArr, "alias", subString.lower())
        if(foundIndx != -1):
            foundNodeIndex =  search_sorted_array_of_dicts(dictData["nodes"], "_idName", aliasArr[foundIndx]["parent"])
            #print(f"{dictData["nodes"][foundNodeIndex]}")
            if(foundNodeIndex != -1):
                if(len(dictData["nodes"][foundNodeIndex]["children"]) != 0 or len(dictData["nodes"][foundNodeIndex]["parents"]) != 0):
                    foundNode = dictData["nodes"][foundNodeIndex]["values"][returnType].strip()
                    normalizedData.append(foundNode) if foundNode not in normalizedData else next
    return " ".join(normalizedData)


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
                elif searchString and any(all_AinB(alias, searchString.lower().strip()) for alias in aliases):
                    matches.append(i)
            else:
                if value.startswith(searchSubString):
                    matches.append(i)
    return matches if matches else [-1]


def all_AinB(A, B):
    # Helper function to check if all words in A are in B
    words_A = A.split()
    words_B = B.split()
    return all(word in words_B for word in words_A)


def dataNormalizationWithSupportArrV2_OLD(currentWords, currentDictionary, sortedAliasArray, splitRule, returnItemType, returnDataType):
    normalizedData = []
    stringa = re.split(r"" + splitRule, currentWords.lower().strip()) if isinstance(currentWords, str) else copy.copy(currentWords)
    for subString in stringa:
        foundIndices = searchSortedDictArrayV2(sortedAliasArray, "alias", " ".join(stringa), subString.strip().lower())
        for foundIndx in foundIndices:
            if foundIndx != -1:
                foundNodeIndices = searchSortedDictArrayV2(currentDictionary["nodes"], "_idName", currentWords, sortedAliasArray[foundIndx]["parent"])
                for foundNodeIndex in foundNodeIndices:
                    if foundNodeIndex != -1:
                        node = currentDictionary["nodes"][foundNodeIndex]
                        if node["children"] or node["parents"]:
                            foundNode = node["values"][returnItemType].strip()
                            if any(subString.strip().lower() in synonym.lower() for synonym in node["values"]["sinonimi"]):
                                if foundNode not in normalizedData:
                                    normalizedData.append(foundNode)
    if "LIST" in returnDataType.upper() or "ARRAY" in returnDataType.upper():
        return normalizedData
    else:
        return " ".join(normalizedData).strip()



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
            elif(searchString != "" and values[i] != "" and all_AinB(values[i], searchString.lower().strip())):
                return i 
        else:
            if isinstance(values[i], str) and values[i].startswith(searchSubString):
                return i
    return -1 



def dataNormalizationWithSupportArrV2(currentWords, currentDictionary, sortedAliasArray, splitRule, returnItemType, returnDataType):
    def secondaryChecK(inStr, inSinonArr):
        for alias in inSinonArr:
            if(" " in alias or "-" in alias):
                if(all_AinB(re.split(r"" + splitRule, alias.lower().strip()), inStr)):
                    return True
                
    normalizedData = []
    stringa = None
    if(isinstance(currentWords, str)):
        stringa = re.split(r"" + splitRule, currentWords.lower().strip())
    elif(isinstance(currentWords, list)):
        stringa = copy.copy(currentWords)
    for subString in stringa:   
        if(subString != ""):  
            foundIndices = searchSortedDictArrayV2(sortedAliasArray, "alias", " ".join(stringa), subString.strip().lower())
            for foundIndx in foundIndices:
                if foundIndx != -1:         
                    foundNodeIndex =  searchSortedDictArray(currentDictionary["nodes"], "_idName", currentWords, sortedAliasArray[foundIndx]["parent"])
                    #print(f"{foundIndx}: {sortedAliasArray[foundIndx]}\t {foundNodeIndex}: {currentDictionary["nodes"][foundNodeIndex]["_idName"]}\n")
                    if(foundNodeIndex != -1):
                        if(len(currentDictionary["nodes"][foundNodeIndex]["children"]) != 0 or len(currentDictionary["nodes"][foundNodeIndex]["parents"]) != 0):
                            foundNode = currentDictionary["nodes"][foundNodeIndex]["values"][returnItemType].strip()
                            #print(f"{all_AinB(subString, currentDictionary["nodes"][foundNodeIndex]["values"]["sinonimi"])}\t{subString.strip().lower()} in {currentDictionary["nodes"][foundNodeIndex]["values"]["sinonimi"]}")
                            flaggy = secondaryChecK(stringa, currentDictionary["nodes"][foundNodeIndex]["values"]["sinonimi"])
                            if(subString.strip().lower() in currentDictionary["nodes"][foundNodeIndex]["values"]["sinonimi"] or flaggy):
                                normalizedData.append(foundNode) if foundNode not in normalizedData and foundNode != "" else next
                            #normalizedData.append(foundNode) if foundNode not in normalizedData else next
    if(("LIST" in returnDataType.upper() or "ARRAY" in returnDataType.upper()) and returnDataType != ""):
        return normalizedData
    elif(returnDataType == "" or (returnDataType != "" and ("STR" in returnDataType.upper() or "STRING" in returnDataType.upper()))):
        return " ".join(normalizedData).strip()
    

def dataNormalizationWithSupportArr(currentWords, currentDictionary, sortedAliasArray, splitRule, returnItemType, returnDataType):
    normalizedData = []
    stringa = None
    if(isinstance(currentWords, str)):
        stringa = re.split(r"" + splitRule, currentWords.lower().strip())
    elif(isinstance(currentWords, list)):
        stringa = copy.copy(currentWords)
    tempNodes = []
    for subString in stringa:
        foundIndx =  searchSortedDictArray(sortedAliasArray, "alias", " ".join(stringa), subString.strip().lower())
        if(foundIndx != -1):            
            foundNodeIndex =  searchSortedDictArray(currentDictionary["nodes"], "_idName", currentWords, sortedAliasArray[foundIndx]["parent"])
            if(foundNodeIndex != -1):
                if(len(currentDictionary["nodes"][foundNodeIndex]["children"]) != 0 or len(currentDictionary["nodes"][foundNodeIndex]["parents"]) != 0):
                    foundNode = currentDictionary["nodes"][foundNodeIndex]["values"][returnItemType].strip()
                    if(subString.strip().lower() in currentDictionary["nodes"][foundNodeIndex]["values"]["sinonimi"]):
                        normalizedData.append(foundNode) if foundNode not in normalizedData else next
    if(("LIST" in returnDataType.upper() or "ARRAY" in returnDataType.upper()) and returnDataType != ""):
        return normalizedData
    elif(returnDataType == "" or (returnDataType != "" and ("STR" in returnDataType.upper() or "STRING" in returnDataType.upper()))):
        return " ".join(normalizedData).strip()


# TO KEEP
def normalizeDataSupportArray(returnType, currentWords, dictData, aliasArr, splitRule):
    normalizedData = []
    stringa = None
    if(isinstance(currentWords,str)):
        stringa = re.split(r"" + splitRule, currentWords.lower().strip())
    elif(isinstance(currentWords, list)):
        stringa = currentWords
    for subString in stringa:
        foundIndx =  search_sorted_array_of_dicts(aliasArr, "alias", subString.lower().strip())
        if(foundIndx != -1):
            foundNodeIndex =  search_sorted_array_of_dicts(dictData["nodes"], "_idName", aliasArr[foundIndx]["parent"])
            if(foundNodeIndex != -1):
                if(len(dictData["nodes"][foundNodeIndex]["children"]) != 0 or len(dictData["nodes"][foundNodeIndex]["parents"]) != 0):
                    foundNode = dictData["nodes"][foundNodeIndex]["values"][returnType].strip()
                    normalizedData.append(foundNode) if foundNode not in normalizedData else next
    return " ".join(normalizedData).strip()

# TO KEEP
def aliasIndexArray(dictData):
    synonims = []
    for item in dictData["nodes"]:
        for alias in item["values"]["sinonimi"]:             
            if(len(item["children"]) != 0 or len(item["parents"]) != 0):
                #if(item["values"]["signal"] != ""):
                    tempDict = {"alias": alias.strip(), "parent": item["_idName"].strip()}
                    synonims.append(tempDict) if tempDict not in synonims else next
    return sorted(synonims, key=lambda x: x["alias"])

# TO KEEP
def leftOversWithSupportArr(currentWords, aliasArr, splitRule):
    if(not currentWords):
            return ""
    stringa = None
    if(isinstance(currentWords,str)):
        stringa = re.split(r"" + splitRule, currentWords.lower().strip())
        stringaRif = re.split(r"" + splitRule, currentWords.lower().strip())
    elif(isinstance(currentWords, list)):
        stringa = currentWords
        stringaRif = currentWords
    for i in range (len(stringa)):
        foundIndx =  searchSortedDictArray(aliasArr, "alias", " ".join(stringa), stringa[i].strip().lower())
        if(foundIndx != -1):
            currAlias = aliasArr[foundIndx]["alias"].strip().lower()
            if(" " not in currAlias):
                if(stringa[i].strip().lower() == currAlias):
                    stringaRif[i] = ""
            elif(" " in currAlias):
                for tempAlias in currAlias.split():
                    if(stringa[i].strip().lower() == tempAlias):
                        stringaRif[i] = ""

    unique_words = list(set(word.upper() for word in stringaRif))
    return " ".join(((" ".join(unique_words)).strip()).split())


def normalizeByType(startNodes, returnType, currentWords, dictData, splitRule):
    foundElements = []
    def traversaNodo(startNode):
        for node_data in dictData.get("nodes", []):
            if(startNode == node_data["id"]):   
                if(len(node_data["children"]) != 0):
                    for nodo in node_data["children"]:
                        findAlias(nodo)
                        traversaNodo(nodo)

    def findAlias(currentNode): 
        for node_data in dictData.get("nodes", []):
            if(currentNode == node_data["id"]):     
                stringa = re.split(r"" + splitRule, currentWords.lower()) 
                for word in stringa:
                    for alias in node_data["values"]["sinonimi"]:
                        if(" " in alias.strip()):        
                            if(all_in_one(alias.strip().lower(), currentWords.lower(), splitRule)): 
                                if node_data["values"][returnType] not in foundElements:
                                    foundElements.append(node_data["values"][returnType].strip())
                        elif(word.lower() == alias.strip().lower()):
                            if(node_data["values"][returnType] not in foundElements):
                                foundElements.append(node_data["values"][returnType].strip())
    for nodo in startNodes.split(" "):              
        traversaNodo(nodo.strip())
    return  " ".join((" ".join(foundElements).strip()).split())

# normalizza i dati in input in base al dizionario fornito
# returnType: signal / sig_descr
def normalizeAll(words, returnType, loaded_data, splitRule): 
    foundFlag = False   
    tempArr = []
    stringa = re.split(r"" + splitRule, words.lower().strip() )    
    for word in stringa:
        for node_data in loaded_data.get("nodes", []):
            if(len(node_data["parents"]) != 0 or len(node_data["children"]) != 0):
                if(len (node_data["values"]["sinonimi"]) != 0): 
                    for alias in node_data["values"]["sinonimi"]:   
                        if(" " in alias.strip()):        
                            if(all_in_one(alias.strip().lower(), words.lower(), splitRule)):  
                                if node_data["values"][returnType] not in tempArr:
                                    tempArr.append(node_data["values"][returnType].strip())
                        elif word.strip() == alias.lower().strip():
                            if node_data["values"][returnType] not in tempArr:
                                tempArr.append(node_data["values"][returnType].strip())

    return " ".join(((" ".join(tempArr)).strip()).split())


def leftOverWords(words, loaded_data, splitRule):
    if(not words):
        return ""
    stringa = re.split(r"" + splitRule, words.lower().strip() )
    stringaRif = re.split(r"" + splitRule, words.strip())     
    if(len(stringa) != len(stringaRif)):
        print(f"S: {len(stringa)} - {stringa} \tR:{len(stringaRif)} - {stringaRif}")
    for i in range (len(stringa)):
        for node_data in loaded_data.get("nodes", []):
            if(len(node_data["parents"]) != 0 or len(node_data["children"]) != 0):
                if(len (node_data["values"]["sinonimi"]) != 0): 
                    for alias in node_data["values"]["sinonimi"]:  
                        if(" " in alias):
                            if(all_in_one(alias.strip().lower(), words.lower(), splitRule)):        
                                stringaRif[i] = ""
                        elif (stringa[i].lower().strip() == alias.lower().strip()):       
                            stringaRif[i] = ""
    unique_words = list(set(word.upper() for word in stringaRif))
    return " ".join(((" ".join(unique_words)).strip()).split())


def fillDataType(compareData, dataTypeDict, usageType:int):
    for dataT in dataTypeDict:
        for data in dataT.values():
            for subData in data:
                if("_" in subData or " " in subData):
                    for var in [" ","-"]:
                        subData = subData.replace(var,"_") 
                if(subData == compareData.upper()):
                    return data[usageType]  # 1 -> mappa # 0 -> profili  


def fill_DataType(compareData, dataTypeDict, **kwargs):
    usageType = 0
    for key, value in kwargs.items():
        if("prof" in key.lower):
            usageType = 1
    for dataT in dataTypeDict:
        for data in dataT.values():
            for subData in data:
                if("_" in subData or " " in subData):
                    for var in [" ","-"]:
                        subData = subData.replace(var,"_") 
                if(subData == compareData.upper()):
                    return data[usageType]  # 1 -> mappa # 0 -> profili 


def get_file_names(directory):
    file_names = []    
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if(os.path.join(root, filename) not in file_names):
                file_names.append(os.path.join(root, filename))    
    return file_names


def get_file_names_for_folders(folders):
    all_file_names = []
    for folder in folders:
        file_names = []
        for root, dirs, files in os.walk(project_root + folder):
            for filename in files:
                if(os.path.join(root, filename) not in file_names):
                    file_names.append(os.path.join(root, filename))
        all_file_names.append(file_names)
    return all_file_names


def extractAnyBrackets(inputText, varType): 
    if(varType == "[]"):
        return re.findall(r'\[(.*?)\]', inputText)
    if(varType == "()"):
        return re.findall(r'\((.*?)\)', inputText)
    elif(varType == None):
        if("(" in inputText and ")" in inputText):
            return re.findall(r'\((.*?)\)', inputText)
        if("[" in inputText and "]" in inputText):
            return re.findall(r'\[(.*?)\]', inputText)
    return None

    
# type: cardinatorSettings, dragonFlySettings,  globalSettings,  mappinatorSettings,  plantSettings,  profilatorSettings
def loadSettings(idName, dataPull):
    settings = (dataLoaderJson(project_root + settingsFolder, settingsFileName, False))
    tempArr = []
    if(idName == "" and dataPull == ""):
        for setting in settings:
            if(setting not in tempArr):
                tempArr.append(setting)
        return tempArr
    elif(idName != "" and dataPull == ""):
        for setting in settings[idName]:
            if(setting["_id"] not in tempArr):
                tempArr.append(setting["_id"] )
        return tempArr
    else:
        for tempy in settings[idName]:
            if(tempy["_id"] == dataPull):
                return tempy["data"]


def all_AinB(varA, varB):  
    if(not varA or not varB):
        return True  
    if(isinstance(varA, str)):
        varA = varA.strip().lower().split()
    if(isinstance(varB, str)):
        varB = varB.strip().lower().split()
    if(varA and all(element in varB for element in varA)): 
        return True
    else:
        return False
    

def any_AinB(varA, varB):
    if not varA or not varB:
        return True
    if(isinstance(varA, str)):
        varA = varA.strip().lower().split()
    if(isinstance(varB, str)):
        varB = varB.strip().lower().split()
    if(any(element in varB for element in varA)):
        return True
    else:
        return False
    


def condizioneComplessa(condSI, condOR, condNO, dati, splitRule):
    if((all_in_one(condSI, dati, splitRule) == True and any_element_in_array(condOR, dati, splitRule) == True) and any_element_in_array(condNO, dati, splitRule) == False):
        return True
    else:
        return False


def all_in_one(arrCond, dataSet, splitRule):
    if(arrCond == ""):
        return True
    if(len(splitRule) == 1):
        arrCond = arrCond.strip().upper().split(splitRule)
        dataSet = dataSet.strip().upper().split(splitRule)
    elif(len(splitRule) != 1):    
        arrCond = re.split(r""+splitRule, arrCond.upper())
        dataSet = re.split(r""+splitRule, dataSet.upper())
    if( all(element in dataSet for element in arrCond)): 
        return True
    else:
        return False
    

def any_element_in_array(arrCond, dataSet, splitRule):
    if(arrCond == ""):
        return True
    elif(arrCond == "?"):
        return False
    if(len(splitRule) == 1):
        arrCond = arrCond.upper().split(splitRule)
        dataSet = dataSet.upper().split(splitRule)
    elif(len(splitRule) != 1):    
        arrCond = re.split(r""+splitRule, arrCond.upper())
        dataSet = re.split(r""+splitRule, dataSet.upper())
    if(any(element in dataSet for element in arrCond)):
        return True
    else:
        return False
    

def read_keywords_from_file(filename, splitChar):
    keyword_dict = {}
    if(filename != None):
        with open(filename, 'r') as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith("<!---"):
                    if splitChar == "":
                        category, keywords = line, line
                    else:
                        category, keywords = line.split(splitChar)
                    keyword_dict[category.strip()] = tuple(keyword.strip() for keyword in keywords.split(','))
        return keyword_dict
    

def extract_text_in_brackets(input_text):
    if isinstance(input_text, tuple) and len(input_text) == 1:
        input_text = input_text[0]
    matches = re.findall(r'\[(.*?)\]', input_text)
    if matches:
        return matches[0] 
    else:
        return None  
    

def extractAnyText(inputText, type):  
    if(type == "()"):  
        return re.findall(r'\((.*?)\)', inputText)
    elif(type == "[]"):  
        return re.findall(r'\[(.*?)\]', inputText)
    else:
        return None
    

# new RulesApplyer
def applyForcedRules(rulesData, dataSet, df, index, row, dictionary, splitRule):
    noteColumn = "<Used Functions>"
    if("Notice" in df.columns and not "<Used Functions>" in df.columns):
        noteColumn = "Notice"
    elif("<Used Functions>" in df.columns):
        noteColumn = "<Used Functions>"
    def multiCondizione(yesCond, anyCond, orCond, noCond, signal, descr):
        def replaceData(dataIn):  
            if(dataIn):    
                temp = normalizeAll(dataIn[1], "sig_descr", dictionary, splitRule)
                tempSignal = ""
                tempDescr = ""
                if("$" in signal):
                    tempSignal = signal.replace("$VAR$",dataIn[1]).strip()
                elif("$" not in signal):
                    tempSignal = signal.strip()
                if("$" in descr):
                    tempDescr = descr.replace("$VAR$", temp).strip()
                elif("$" not in descr):
                    tempDescr = descr.strip()
                return tempSignal.strip(), tempDescr.strip()
            
        allCond = AllCheck(yesCond, dataSet)
        atLeastOne = None
        boolArr = []
        if(len(anyCond) != 0 ):        
            for anyItem in anyCond:
                atLeastOne = preCheck(anyItem)
                if(not atLeastOne):
                    break
                else:
                    boolArr.append(atLeastOne)
        boolArrValue = []
        
        for item in boolArr:
            boolArrValue.append(item[1])
        boolArrValue = " ".join(boolArrValue)
        anyOne = preCheck(orCond)
        notAnyOne = preCheck(noCond)
        forcedSignal = ""
        forcedDescr = ""
        nota = ""
        if(allCond == True and notAnyOne == None): 
            if(anyOne and anyOne[0] == True and not atLeastOne ):
                nota += f" {anyOne[1]} "
            if(anyCond and atLeastOne ):
                forcedSignal, forcedDescr = replaceData(atLeastOne)
                nota += f" (var: [{str(yesCond), str(anyCond)}])"
            elif(not anyCond):
                forcedSignal = signal
                forcedDescr = descr
                nota += ""
        if(forcedSignal != "" and forcedDescr != ""):
            df.at[index, "NewSignalName"] = forcedSignal.strip()
            df.at[index, "NewSignalDescription"] = forcedDescr.strip()
            noticeUpdate(df, index, row, noteColumn, str(f"applyRules({nota})"))

    def preCheck(variabile):
        if(isinstance(variabile,str)):
            variabile = variabile.strip().split(" ")
        tempLogic = False   
        if(variabile):
            if(len(variabile) == 1):
                return (AnyCheck(variabile[0], dataSet))
            elif(len(variabile) > 1):   
                for element in variabile:
                    tempLogic = (AnyCheck(element, dataSet))
                    if(tempLogic):
                        return tempLogic
        else:            
            return False   

    def AnyCheck(condData, dataSet):
        if(isinstance(condData,str)):
            condData = condData.strip().split(" ")
        if(isinstance(dataSet, str)):
            dataSet = dataSet.strip().split(" ")
        if(len(condData) != 0 and len(dataSet) != 0):
            for element in dataSet:
                if element in condData:
                    return True, element
        
    def AllCheck(condData, dataSet):
        if(isinstance(condData,str)):
            condData = condData.strip().split(" ")
        if(isinstance(dataSet, str)):
            dataSet = dataSet.strip().split(" ")
        if(len(condData) != 0 and len(dataSet) != 0):
            if(all(element in dataSet for element in condData)): 
                return True
            else:
                return False

    def extractAtLeastOne(inputText):    
        return re.findall(r'\[(.*?)\]', inputText)
        
    def extractAny(inputText):    
        return re.findall(r'\((.*?)\)', inputText)

    def removeFromString(targetStr, remElem, delimiters):
        for delimiter in delimiters:
            if(delimiter in targetStr):
                targetStr = targetStr.replace(delimiter,"")                
        newString = targetStr.split(" ")
        for i in range (len(newString)):
            for element in remElem:
                for subElem in element.split(" "):
                    if(newString[i] == subElem):
                        newString[i] = ""        
        return " ".join(newString)
    
    def prepareData():
        for dataRef in rulesData:
            if(not (dataRef.startswith("!---") and dataRef.endswith("---!"))):
                tempCondition, tempResult = dataRef.strip().split("=")
                tempYes, tempNo = tempCondition.strip().split(":")
                tempSignal, tempDescr = tempResult.strip().split(":")
                anyCond = (extractAtLeastOne(tempYes.strip()))
                orCond = (extractAny(tempYes.strip()))
                if anyCond:
                    tempYes = (" ".join((removeFromString(tempYes, anyCond, "[]")).split())).strip()
                if orCond:
                    tempYes = (" ".join((removeFromString(tempYes, orCond, "()")).split())).strip()
                multiCondizione(tempYes, anyCond, orCond, tempNo, tempSignal, tempDescr)
    prepareData()



# new RulesApplyer
def applyForcedRulesMOD(rulesData, dataSet, df, index, row, dictionary, splitRule):
    noteColumn = "<Used Functions>"
    if("Notice" in df.columns and not "<Used Functions>" in df.columns):
        noteColumn = "Notice"
    elif("<Used Functions>" in df.columns):
        noteColumn = "<Used Functions>"
    def multiCondizione(yesCond, anyCond, orCond, noCond, signal, descr):
        def replaceData(dataIn):  
            if(dataIn):    
                temp = normalizeAll(dataIn[1], "sig_descr", dictionary, splitRule)
                tempSignal = ""
                tempDescr = ""
                if("$" in signal):
                    tempSignal = signal.replace("$VAR$",dataIn[1]).strip()
                elif("$" not in signal):
                    tempSignal = signal.strip()
                if("$" in descr):
                    tempDescr = descr.replace("$VAR$", temp).strip()
                elif("$" not in descr):
                    tempDescr = descr.strip()
                return tempSignal.strip(), tempDescr.strip()
            
        allCond = AllCheck(yesCond, dataSet)
        atLeastOne = None
        boolArr = []
        if(len(anyCond) != 0 ):        
            for anyItem in anyCond:
                atLeastOne = preCheck(anyItem)
                if(not atLeastOne):
                    break
                else:
                    boolArr.append(atLeastOne)
        boolArrValue = []
        
        for item in boolArr:
            boolArrValue.append(item[1])
        boolArrValue = " ".join(boolArrValue)
        anyOne = preCheck(orCond)
        notAnyOne = preCheck(noCond)
        forcedSignal = ""
        forcedDescr = ""
        nota = ""
        if(allCond == True and notAnyOne == None): 
            if(anyOne and anyOne[0] == True and not atLeastOne ):
                nota += f" {anyOne[1]} "
            if(anyCond and atLeastOne ):
                forcedSignal, forcedDescr = replaceData(atLeastOne)
                nota += f" (var: [{str(yesCond), str(anyCond)}])"
            elif(not anyCond):
                forcedSignal = signal
                forcedDescr = descr
                nota += ""
        if(forcedSignal != "" and forcedDescr != ""):
            #df.at[index, "NewSignalName"] = forcedSignal.strip()
            #df.at[index, "NewSignalDescription"] = forcedDescr.strip()
            return forcedSignal.strip(), forcedDescr.strip()
            #noticeUpdate(df, index, row, noteColumn, str(f"applyRules({nota})"))

    def preCheck(variabile):
        if(isinstance(variabile,str)):
            variabile = variabile.strip().split(" ")
        tempLogic = False   
        if(variabile):
            if(len(variabile) == 1):
                return (AnyCheck(variabile[0], dataSet))
            elif(len(variabile) > 1):   
                for element in variabile:
                    tempLogic = (AnyCheck(element, dataSet))
                    if(tempLogic):
                        return tempLogic
        else:            
            return False   

    def AnyCheck(condData, dataSet):
        if(isinstance(condData,str)):
            condData = condData.strip().split(" ")
        if(isinstance(dataSet, str)):
            dataSet = dataSet.strip().split(" ")
        if(len(condData) != 0 and len(dataSet) != 0):
            for element in dataSet:
                if element in condData:
                    return True, element
        
    def AllCheck(condData, dataSet):
        if(isinstance(condData,str)):
            condData = condData.strip().split(" ")
        if(isinstance(dataSet, str)):
            dataSet = dataSet.strip().split(" ")
        if(len(condData) != 0 and len(dataSet) != 0):
            if(all(element in dataSet for element in condData)): 
                return True
            else:
                return False

    def extractAtLeastOne(inputText):    
        return re.findall(r'\[(.*?)\]', inputText)
        
    def extractAny(inputText):    
        return re.findall(r'\((.*?)\)', inputText)

    def removeFromString(targetStr, remElem, delimiters):
        for delimiter in delimiters:
            if(delimiter in targetStr):
                targetStr = targetStr.replace(delimiter,"")                
        newString = targetStr.split(" ")
        for i in range (len(newString)):
            for element in remElem:
                for subElem in element.split(" "):
                    if(newString[i] == subElem):
                        newString[i] = ""        
        return " ".join(newString)
    
    
    def prepareData():
        for dataRef in rulesData:
            if(not (dataRef.startswith("!---") or dataRef.endswith("---!"))):
                tempCondition, tempResult = dataRef.strip().split("=")
                tempYes, tempNo = tempCondition.strip().split(":")
                tempSignal, tempDescr = tempResult.strip().split(":")
                anyCond = (extractAtLeastOne(tempYes.strip()))
                orCond = (extractAny(tempYes.strip()))
                if anyCond:
                    tempYes = (" ".join((removeFromString(tempYes, anyCond, "[]")).split())).strip()
                if orCond:
                    tempYes = (" ".join((removeFromString(tempYes, orCond, "()")).split())).strip()
                multiCondizione(tempYes, anyCond, orCond, tempNo, tempSignal, tempDescr)
    prepareData()


def noticeUpdate(df, index, row, columnName, inString):
    if(df.loc[index, columnName] == None 
       or str(df.loc[index, columnName]) == "" 
       or str(df.loc[index, columnName]) == "nan"):
        df.loc[index, columnName] = str(f"|{inString}|")
    elif(df.loc[index, columnName] != None and str(df.loc[index, columnName]) != "" and str(df.loc[index, columnName]) == "nan"):#and df.at[index, columnName] != None):
        df.loc[index, columnName] += str(f" & |{inString}|") if inString not in str(df.loc[index, columnName]) else ""


# new RulesApplyer ALR CLASS
def applyForcedRulesAlrClass(rulesData, dataSet, df, row, index, dictionary, splitRule):
    noteColumn = "<Used Functions>"
    if("Notice" in df.columns):
        noteColumn = "Notice"
    elif("<Used Functions>" in df.columns and "Notice" not in df.columns):
        noteColumn = "<Used Functions>"

    def multiCondizione(yesCond, anyCond, orCond, noCond, signal, descr):
        def replaceData(dataIn):  
            if(dataIn):    
                temp = normalizeAll(dataIn[1], "sig_descr", dictionary, splitRule)
                tempSignal = ""
                tempDescr = ""
                if("$" in signal):
                    tempSignal = signal.replace("$VAR$",dataIn[1]).strip()
                elif("$" not in signal):
                    tempSignal = signal.strip()
                if("$" in descr):
                    tempDescr = descr.replace("$VAR$", temp).strip()
                elif("$" not in descr):
                    tempDescr = descr.strip()
                return tempSignal.strip(), tempDescr.strip()
            
        allCond = AllCheck(yesCond, dataSet)
        atLeastOne = None
        boolArr = []
        if(len(anyCond) != 0 ):        
            for anyItem in anyCond:
                atLeastOne = preCheck(anyItem)
                if(not atLeastOne):
                    break
                else:
                    boolArr.append(atLeastOne)
        boolArrValue = sum(bool(x) for x in boolArr)
        anyOne = preCheck(orCond)
        notAnyOne = preCheck(noCond)
        forcedSignal = ""
        forcedDescr = ""
        nota = ""
        if(allCond == True and notAnyOne == None): 
            if(anyOne and anyOne[0] == True):
                nota += f" {anyOne[1]} "
            if(anyCond and atLeastOne and boolArrValue == len(anyCond)):
                forcedSignal, forcedDescr = replaceData(atLeastOne)
                nota += f" (var: [{str(yesCond), str(anyCond)}])"
            elif(not anyCond):
                forcedSignal = signal
                forcedDescr = descr
                nota += ""

        if(forcedSignal != "" and forcedDescr != ""):
            df.loc[index, "NewAlarmClass"] = forcedSignal.strip()
            df.loc[index, "NewAlarmDescription"] = forcedDescr.strip()
            noticeUpdate(df, index, row, noteColumn, f"applyAlrClassRules{nota}")

    def preCheck(variabile):
        if(isinstance(variabile,str)):
            variabile = variabile.strip().split(" ")
        tempLogic = False   
        if(variabile):
            if(len(variabile) == 1):
                return (AnyCheck(variabile[0], dataSet))
            elif(len(variabile) > 1):   
                for element in variabile:
                    tempLogic = (AnyCheck(element, dataSet))
                    if(tempLogic):
                        return tempLogic
        else:            
            return False    

    def AnyCheck(condData, dataSet):
        if(isinstance(condData,str)):
            condData = condData.strip().split(" ")
        if(isinstance(dataSet, str)):
            dataSet = dataSet.strip().split(" ")
        if(len(condData) != 0 and len(dataSet) != 0):
            for element in dataSet:
                if element in condData:
                    return True, element
        
    def AllCheck(condData, dataSet):
        if(isinstance(condData,str)):
            condData = condData.strip().split(" ")
        if(isinstance(dataSet, str)):
            dataSet = dataSet.strip().split(" ")
        if(len(condData) != 0 and len(dataSet) != 0):
            if(all(element in dataSet for element in condData)): 
                return True
            else:
                return False

    def extractAtLeastOne(inputText):    
        return re.findall(r'\[(.*?)\]', inputText)

    def extractAny(inputText):    
        return re.findall(r'\((.*?)\)', inputText)

    def removeFromString(targetStr, remElem, delimiters):
        for delimiter in delimiters:
            if(delimiter in targetStr):
                targetStr = targetStr.replace(delimiter,"")                
        newString = targetStr.split(" ")
        for i in range (len(newString)):
            for element in remElem:
                for subElem in element.split(" "):
                    if(newString[i] == subElem):
                        newString[i] = ""        
        return " ".join(newString)

    def prepareData():
        for dataRef in rulesData:
            if(not (dataRef.startswith("!---") and dataRef.endswith("---!"))):
                tempCondition, tempResult = dataRef.strip().split("=")
                tempYes, tempNo = tempCondition.strip().split(":")
                tempSignal, tempDescr = tempResult.strip().split(":")
                anyCond = (extractAtLeastOne(tempYes.strip()))
                orCond = (extractAny(tempYes.strip()))
                if anyCond:
                    tempYes = (" ".join((removeFromString(tempYes, anyCond, "[]")).split())).strip()
                if orCond:
                    tempYes = (" ".join((removeFromString(tempYes, orCond, "()")).split())).strip()
                multiCondizione(tempYes, anyCond, orCond, tempNo, tempSignal, tempDescr)
    prepareData()


def extract_id(string, splitRule):  
    if(string):
        string = re.split(r"" + splitRule, string)
        ids = []
        for element in string:
            if(len(element) <= 6):                       
                pattern = r'\b(?=\w*\d)(?=\w*[a-zA-Z])\w{2,}\b'
                ids.append((re.findall(pattern, element))[0]) if (re.findall(pattern, element)) else next 
    return "/".join(ids) if "/".join(ids) != "" else None


if __name__ == '__main__':
    0