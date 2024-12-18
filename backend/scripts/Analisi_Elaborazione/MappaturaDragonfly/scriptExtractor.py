import sys, os, re, copy

project_root = os.getcwd()
sys.path.append(project_root)

from backend.scripts.SharedCode import sharedCode

# ----------------------------------- START COSTANTI -----------------------------------#  


# ----------------------------------- END COSTANTI -----------------------------------# 


def labelDataExtractor(scriptName, scriptData):  
    """
    Cerca di individuare & estrarre i dati dal blocco condizionale: buona fortuna ai posteri per i pattern
    """
    if("/*" in scriptData and "*/" in scriptData):
        if(scriptData.find("/*") != -1 and scriptData.find("*/") != -1):
            scriptData = scriptData.replace(scriptData[scriptData.find("/*"):scriptData.find("*/")],"")

    removeItems = ["+component.getName()+", r"+\s*component.getName()\s*+", "'+'", "''", "+", str("''"), "'')"]

    tempScriptData = copy.copy(scriptData)
    for item in removeItems:
        tempScriptData = tempScriptData.replace(item,"")

    ZulStartPatterns = [r"String\s*gridZul", r"String\s*zul", r"if\s*\(component.getFirstElement\(\)\s*==\s*null\)\s*{"]
    matchEndZul = re.search(r"component\.getElementContainer\(\)\s*,\s*null\s*\)\s*;", tempScriptData, re.DOTALL)
    noZul = False
    
    for zulPattern in ZulStartPatterns:
        matchStartZul = re.search(zulPattern, tempScriptData, re.DOTALL)
        if(matchStartZul):
            noZul = True
            break
    if(not matchEndZul and noZul == False):
        print(f"Missing START & END {scriptName}")
        return None
    
    Patterns = [
                r"<label\s+value\s*=\s*'(.*?)'\s*/>\s*<div\s*align\s*=\s*'right'\s*>\s*<label\s+id\s*=\s*'(.*?)'\s*/>\s*<label\s+value='(.*?)'\s*/>\s*</div>", 
                r"<row.*?<label\s+value\s*=\s*'(.*?)'\s*/>\s*<div\s*align\s*=\s*'right'\s*>\s*<label\s+id\s*=\s*'(.*?)'\s*/>\s*<label\s+value='(.*?)'\s*/>\s*</div>?\s*</row>",
                #r"<row>\s*<label\s+value='(.*?)'/>\s*<div\s+align='right'>\s*<label\s+id='(.*?)'/>\s*</div>\s*</row>", 
                r"<row>(?:\s*)<label\s+value='([^']+)'/>(?:\s*)<div\s+height='[^']+'\s+align='right'>(?:\s*)<label\s+id='([^']+)'/>(?:\s*)</div>(?:\s*)</row>",
                r"<row>\s*<label\s+value='([^']+)'/>\s*<div\s+align='right'>\s*<label\s+id='([^']+)'/>\s*(?:<label\s+value='([^']+)'/>)?\s*</div>\s*</row>",   
                r"<row.*?<label\s+value='(.*?)'/>\s*<div\s+align='right'>\s*<label\s+id='(.*?)'\s*/>\s*</div>",
                r"<label\s+value='([^']+)'/>\s*<div\s+align='right'>\s*<doublebox\s+id='([^']+)'", 
                r"<label\s+value='(.*?)'\s*/>\s*<div\s+align='right'>\s*<label\s+id='(.*?)'\s*/>\s*</div>",
                r"<label\s+value='(.*?)'\s*/>\s*(?:.*?)\s*<label\s+id='(.*?)'\s*/>\s*?</div>?\s*</row>",   
                r"<label\s+value='(.*?)'\s*/>\s*(?:<div\s+align='right'>\s*)?<label\s+id='(.*?)'\s*\+''\s*/>\s*</div>", 

                r"<label\s+value='(.*?)'\s*/>\s*</div>\s*<div align='right'>\s*<label\s+id='(.*?)'\s*/>\s*</div>\s*</row>", 
                r"<label\s+value='([^']+)'/>\s*<div[^>]*>\s*<label[^>]*id='\s*'([^']+)'",   
                r"<label\s+value='([^']+)'/>\s*<div[^>]*>\s*<label[^>]*id='\+component\.getName\(\)\+'([^']+)'",    
                r"<label\s+value='([^']+)'/>\s*<div[^>]*>\s*<label[^>]*id='\s*component\.getName\(\)\+'([^']+)'",   
                r"<row[^>]*>\s*<label\s+value\s*=\s*'([^']+)'\s*/>\s*<div[^>]*align\s*=\s*'right'[^>]*>\s*<label\s+id\s*=\s*'([^']+)'\s*/>\s*</div>\s*</row>",  
                r"<label\s+value\s*=\s*'([^']+)'\s*/>\s*<div[^>]*align\s*=\s*'right'[^>]*>\s*<label\s+id\s*=\s*'([^']+)'\s*/>\s*</div>",    
                r"<row[^>]*>\s*<label\s+value='([^']+)'/>\s*<div[^>]*align='right'[^>]*>\s*<label\s+id='([^']+)'/>\s*</div>\s*</row>",  
                r"<row[^>]*>\s*<label\s+value='([^']+)'/>\s*<div[^>]*height='[^']+'[^>]*align='right'[^>]*>\s*<label\s+id='([^']+)'/>\s*</div>\s*</row>",    
                r"<label\s+value='([^']+)'/>\s*<div[^>]*align='right'[^>]*>\s*<doublebox\s+id='([^']+)'",   
                r"<label\s+value='([^']+)'/>\s*<div[^>]*align='right'[^>]*>\s*<label\s+id='([^']+)'/>\s*</div>",   

                r"<label\s+value='([^']+)'/>\s*<div[^>]*align='right'[^>]*>\s*<label\s+id='\+component\.getName\(\)\+'([^']+)'",    
                r"<label\s+value='([^']+)'/>\s*<div[^>]*align='right'[^>]*>\s*<label\s+id='component\.getName\(\)\+'([^']+)'",  
                r"<label\s+value='([^']+)'/>\s*</div>\s*<div[^>]*align='right'[^>]*>\s*<label\s+id='([^']+)'/>\s*</div>\s*</row>",  
                r"<label\s+value='([^']+)'/>\s*<div\s*align='right'>\s*<image\s*width='[^']+'\s*height='[^']+'\s*id='([^']+)'/>\s*</div>",  
                r"<label\s+value='([^']+)'/>\s*<div\s*align='right'>\s*<label\s+id='([^']+)'/>\s*<label\s+value=''/>\s*</div>", 
                r"<label\s+value='([^']*)'\s*/>\s*<div\s+align='right'>\s*<label\s+id='([^']*)'\s*/>",
                r"\s*<label\s+value='([^']+)'/>\s*</div>\s*<div\s*align='right'>\s*<label\s+id='([^']+)'/>",                 
                r"<row>\s*<label\s+id='([^']*)'\s*value=''/>\s*<div\s*align='right'>\s*<label\s+id='([^']*)'/>\s*</div>\s*</row>",
                r"<label\s+id='([^']*)'\s*value=''/>\s*<div\s*align='right'>\s*<label\s+id='([^']*)'/>\s*</div>",             
                r"<label\s+id='([^']*)'\s*value=''/>\s*<div\s*align='right'>\s*<label\s+id='([^']*)'/>\s*</div>",
                         
                r"<row>\s*<label\s+id='([^']*)'\s*value=/>\s*<div\s*align='right'>\s*<label\s+id='([^']*)'/>\s*</div>\s*</row>",
                r"<label\s+id='([^']*)'\s*value=/>\s*<div\s*align='right'>\s*<label\s+id='([^']*)'/>\s*</div>",             
                r"<label\s+id='([^']*)'\s*value=/>\s*<div\s*align='right'>\s*<label\s+id='([^']*)'/>\s*</div>",


                r"<row.*?<label\s+id='([^']*)'\s+value='[^']*'\s*/>\s*<div\s+align='right'>\s*<label\s+id='([^']*)'/>\s*</div>",
                r"<label\s+id='([^']*)'\s+value=''\s*/>\s*<div\s*align='right'>\s*<label\s+id='([^']*)'/>\s*</div>",
                r'<row>\s*<label\s+id=\'(\d+Zona)\'\s+value=\'\'/>\s*<div\s+align=\'right\'>\s*<label\s+id=\'(zona\d+)\'/>\s*</div>\s*</row>',
                #r"<label\s+id='([^']*)'\s*(?:value='[^']*'\s*/>|/>)",
                #r"<label\s+id='([^']*)'\s+value=''\s*/>|<label\s+id='([^']*)'\s*/>",

 
                r"<row\s+id='.*?''>\s*<label\s+value='(.*?)'\s*/>\s*(?:<div\s+align='right'>\s*)?<label\s+id='(.*?)'\s*/>\s*\+\\'''?\s*</div>?\s*</row>",  
                r"<row\s+id='.*?'\s*>\s*<label\s+value='([^']+)'\s*/>\s*(?:<div[^>]*align='right'[^>]*>\s*)?<label\s+id='([^']+)'/>\s*</div>?\s*</row>",  
                r"<a\s+id='([^']+)'\s*tooltiptext='([^']+)'\s*style='font-size:\s*'[^']+'[^>]px'>\s*([^']+)\s*</a>",     

                r"<a\s+id='([^']+)'\s*tooltiptext='([^']+)'\s*style='font-size:\s*'[^']+'[^>]px'>\s*([^']+)\s*</a>",   
                r"<a\s+id='([^']+)'\s*tooltiptext='([^']+)'\s*width='[^']+'\s*sclass='btn\s*btn-primary'>\s*[^']\s*</a>"

                r"<label\s+id='([^']+)'\s*tooltiptext='([^']+)'\s*/>",
                r"<a\s+id='([^']+)'\s+tooltiptext='([^']+)'\s+width='[^']+'\s+sclass='[^']+'>\s*(.*?)\s*</a>"

                #r"<label\s+id='([^']*)'\s+value='([^']*)'\s*/>|<label\s+id='([^']*)'\s*/>",            
                #r"(?:<(?:row|label|a)\s+id='([^']*)'[^>]*(?:tooltiptext='([^']*)')?[^>]*>)"

                ]    

    matchRows = re.search(r'<rows>(.*?)</rows>', scriptData, re.DOTALL)
    if(matchRows):
        startRows = matchRows.span()[0]
        endRows = matchRows.span()[1]
        tempScriptData = tempScriptData[startRows:endRows]
    
    
    excludeLabelParts = ["+", "<div", "<div ", "</div", "/>", "component.getName()", "component.getName() +", "label value=", "'')", "''", "<row", "</row", "<div align='right'>\\n", "'right'",
                         "align", "label", ", ''),", "('',", "label id", "label style", "label value", "\\", "div align"]
      
    #print("\n\n##############################################\n\n", tempScriptData) 
    matchingMatches = [] 
    for index, pattern in enumerate(Patterns):            
        matches = re.findall(pattern, tempScriptData, re.DOTALL)
        if(matches): 
            checkFlag = not(any(element in str(matches) for element in excludeLabelParts))
            if(checkFlag == True):
               matchingMatches.append(matches) if matches not in matchingMatches else next
    if(matchingMatches):
        maxDim = 0
        maxIdx = 0
        for maxIndx, matchy in enumerate(matchingMatches):
            if(len(matchy) > maxDim):
                maxIdx = maxIndx
        return matchingMatches[maxIdx]
    return None


def labelFormating(scriptName, scriptData, extractedLabelData):
    """
    crea il formato: {script, data: [{id, label, uom}]}
    """
    labelHolder = []
    if(isinstance(extractedLabelData[0], tuple)):
        tipoElab = len(extractedLabelData[0])
        for index, labelData in enumerate(extractedLabelData):
            foundAny = False        
            if(labelData[0] != "" and labelData[1] != ""):        
                for indx, item in enumerate(labelHolder):
                    if(scriptName in item["script"]):
                        dicty = {"id": labelData[1], "label" : labelData[0], "uom" : None}
                        if(tipoElab == 3):
                            dicty["uom"] = labelData[2]
                        labelHolder[indx]["data"].append(dicty) if dicty not in labelHolder else next
                        foundAny = True
                if(foundAny == False):
                    dicty = {"script": scriptName, "data": [{"id": labelData[1], "label" : labelData[0], "uom" : None}] }
                    if(tipoElab == 3):
                        dicty["uom"] = labelData[2]
                    labelHolder.append(dicty) if dicty not in labelHolder else next
    else:
        for index, labelData in enumerate(extractedLabelData):
            scriptName = scriptName.split("donato")[1] if "donato" in scriptName else scriptName
            foundAny = False        
            if(labelData != ""):        
                for indx, item in enumerate(labelHolder):
                    if(scriptName in item["script"]):
                        dicty = {"id": labelData, "label" : labelData, "uom" : None}
                        labelHolder[indx]["data"].append(dicty) if dicty not in labelHolder else next
                        foundAny = True
                if(foundAny == False):
                    dicty = {"script": scriptName, "data": [{"id": labelData, "label" : labelData, "uom" : None}] }
                    labelHolder.append(dicty) if dicty not in labelHolder else next
    return labelHolder


def conditionBlockExtractor(scriptName, scriptData, formatedLabels):
    """
    Cerca di individuare il blocco condizionale da 'if' fino alla chiusura della prima parentesi graffa '}'
    """
    matchEndZul = re.search(r"component\.getElementContainer\(\)\s*,\s*null\s*\)\s*;", scriptData, re.DOTALL)
    if(matchEndZul):
        scriptData = scriptData[matchEndZul.span()[1]:]
        for idx, items in enumerate(formatedLabels):
            for jdx, label in enumerate(items["data"]):
                foundLabel = (re.search(rf"component\.getFellow\('({label["id"]})'\)\.setSclass\(.*?On\)", scriptData, re.DOTALL))
                if(foundLabel):
                    startPoint = foundLabel.span()[0]
                    endPoint = foundLabel.span()[1]
                    while("if" not in scriptData[startPoint:endPoint] and startPoint > 0):
                        startPoint -= 1
                    while("}" not in scriptData[startPoint:endPoint] and endPoint < len(scriptData)):
                        endPoint += 1
                    subScript = scriptData[startPoint:endPoint]
                    extractVars = re.findall(r"tags\.get\('(\$[a-zA-Z_][\w]*)'\)\?\.\s*getValue\(\)\s*==\s*(\d+)", subScript, re.DOTALL)
                    if(extractVars):
                        formatedLabels[idx]["data"][jdx]["logicBlock"] = extractVars
        return formatedLabels


def extractScriptData(scriptName, scriptData, variables):  
    if(scriptData != ""):
        scriptData = scriptData.replace('"',"'") 
        if(not variables):  
            extractedLabelData = labelDataExtractor(scriptName, str(scriptData).replace('"',"'"))
            if(not extractedLabelData):
                0#extractedLabelData = ollamaExtractor(scriptName, scriptData)  # partire da qui per falsi positivi da impastare a LLM
            if(extractedLabelData):
                formatedLabels = labelFormating(scriptName, scriptData, extractedLabelData)
                if(formatedLabels):
                    conditionBlocks = conditionBlockExtractor(scriptName, scriptData, formatedLabels)
                    return conditionBlocks
        elif(variables):
            0#conditionData = conditionBlockData(scriptData, scriptName, variables)


if __name__ == "__main__":    
    
    scriptFolder = "\\scripts\\Analisi_Elaborazione\\MappaturaDragonfly\\File Elaborati\\scriptsFolder\\"
    subFolder = "donato\\"

    cwd = os.getcwd() + scriptFolder + subFolder
    scripts = [os.path.join(cwd, f) for f in os.listdir(cwd) if 
    os.path.isfile(os.path.join(cwd, f))]

    used = []

    choicy = 1

    missingExtraction = []
    for scriptName in scripts:            
        #f = open(scriptName, "r")
        #scriptData = f.read().strip()        
        scriptData = sharedCode.rw_file(file = scriptName, mode = "load")
        if(choicy == 0):
            for usy in used:
                if(usy in scriptName):
                    extractedScriptData = extractScriptData(scriptName, scriptData.replace('"',"'"), None)
                    print("\n", scriptName)  
                    print(f">\t{extractedScriptData}")
                    print()

        elif(choicy == 1):
            print("\nscriptName:\t", scriptName) 
            extractedScriptData = extractScriptData(scriptName, scriptData.replace('"',"'"), None)
            if(not extractedScriptData):
                missingExtraction.append(scriptName) if scriptName not in missingExtraction else next

            print(f">\t{extractedScriptData}")
            print()
            input()
            #if("LARIA-MULTIMETRO-STATO@LARIA--LARIA-MULTIMETRO-DETT-SCRIPT.txt" in scriptName):
            #    input()
    #for item in missingExtraction:
    #    print(item.replace(cwd,""))