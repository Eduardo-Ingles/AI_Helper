import pandas as pd
import pymongo
import sys, os
import traceback

project_root = os.getcwd()
sys.path.append(project_root)


from backend.scripts.SharedCode import sharedCode, mongoSearch


# ----------------------------------- START COSTANTI -----------------------------------#  
errorsList = []
dividerChars = sharedCode.loadSettings("globalSettings", "dividers")
prefisso = sharedCode.loadSettings("yarotSettings", "prefix")

# ----------------------------------- END COSTANTI -----------------------------------# 

def mainCall(nomeGallerie, UploadsFileFolder, DownloadsFileFolder, CpuCoreNumber, chosenDB, collectionSelector, **kwargs):
    links = []
    try:
        yield {"progress": 0}
        for dividerChar in dividerChars:
            if(dividerChar in nomeGallerie):            
                nomeGallerie = nomeGallerie.strip().split(dividerChar)
                break
        if(isinstance(nomeGallerie, str)):
            nomeGallerie = nomeGallerie.strip().split()

        if(not collectionSelector):
            return None
        
        dbAddress = "MongoQualityClient"
        yarot = "yarot"
        if(chosenDB.upper().startswith("PROD") or chosenDB.upper().startswith("P")):
            dbAddress = "MongoProductionClient"
            yarot = "yarot2"

        savename = f"{prefisso}-{collectionSelector}_{chosenDB}_{"-".join(nomeGallerie)}_{sharedCode.timeStamp(fullDate = True)}.xlsx"
        
        client = pymongo.MongoClient(sharedCode.loadSettings("globalSettings", dbAddress)) 
    except Exception as e:               
        error = f"An error occurred: {str(e)}"
        print(error)
        errorsList.append(error) if error not in errorsList else next
        traceback.print_exc()
    
    try:
        if("SmartScada" in collectionSelector):
            msg = f"Confronti YAROT <---> SMARTSCADA\t<{chosenDB}>\n"
            yield(msg) if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print(msg)
            # SCADA
            smartScadaDataEID = []
            smartScadaDataName = [] 
            yarotData = []
            for nomeGalleria in nomeGallerie:
                nomeGalleria = nomeGalleria.strip()
                SmartScadaDbData = mongoSearch.readCollectionData(client["smartscada"], "device", name = nomeGalleria, regex = True)
                YarotDbData = mongoSearch.readCollectionData(client[yarot], "assets", name = nomeGalleria, regex = True)

                for dfData in SmartScadaDbData:
                    smartScadaDataEID.append(dfData["externalId"]) if "externalId" in dfData.keys() and dfData["externalId"] not in smartScadaDataEID else next
                    smartScadaDataName.append(dfData["name"]) if "name" in dfData.keys() and dfData["name"] not in smartScadaDataName else next

                for dfData in YarotDbData:
                    if("lifeCycle" in dfData.keys() and dfData["lifeCycle"] and "READY" in dfData["lifeCycle"].upper()):
                        yarotData.append(dfData["name"]) if "name" in dfData.keys() and dfData["name"] not in yarotData else next
                    else:
                        msg = (f"Errore: {dfData["name"]} -> lifeCycle: {dfData["lifeCycle"]}")
                        yield(msg) if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print(msg)

            commonA, uniqAA, uniqBA = (sharedCode.compareLists(smartScadaDataName, yarotData))

            dfCommonA = pd.DataFrame(dtype=str)
            dfDFA = pd.DataFrame(dtype=str)
            dfYRA = pd.DataFrame(dtype=str)

            for index, value in enumerate(commonA):
                dfCommonA.loc[index,"common_ScadaName"] = value

            for index, value in enumerate(uniqAA):
                dfDFA.loc[index,"OnlyScadaName"] = value

            for index, value in enumerate(uniqBA):
                dfYRA.loc[index,"OnlyYarot-Name"] = value

            commonB, uniqAB, uniqBB = (sharedCode.compareLists(smartScadaDataEID, yarotData))

            dfCommonB = pd.DataFrame(dtype=str)
            dfDFB = pd.DataFrame(dtype=str)
            dfYRB = pd.DataFrame(dtype=str)

            for index, value in enumerate(commonB):
                dfCommonB.loc[index,"common_ScadaID"] = value

            for index, value in enumerate(uniqAB):
                dfDFB.loc[index,"OnlyScadaID"] = value

            for index, value in enumerate(uniqBB):
                dfYRB.loc[index,"OnlyYarot-ID"] = value

            yield(" ") if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print()
            msg = (f"SmartScada_Name(totale): {len(smartScadaDataName)}\t-\tYarot(totale): {len(yarotData)}\ncommon_Name:{len(commonA)}\tsmartScadaOnly_Name: {len(uniqAA)}\tyarotOnly_Name: {len(uniqBA)}\n")
            yield(msg) if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print(msg)
            msg = (f"SmarScada_ID(totale): {len(smartScadaDataName)}\t-\tYarot(totale): {len(yarotData)}\ncommon_ID:{len(commonB)}\tsmartScadaOnly_Id: {len(uniqAB)}\tyarotOnly_Id: {len(uniqBB)}")
            yield(msg) if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print(msg)

            df = {"common_Name": dfCommonA, "smartScadaOnly_Name": dfDFA, "yarotOnly_Name": dfYRA, 
                "common_ID": dfCommonB, "smartScadaOnly_ID": dfDFB, "yarotOnly_ID": dfYRB}
            msg = ("Salvataggio...", sharedCode.rw_xlsx(path = DownloadsFileFolder, file = savename, df = df, mode = "save"))  
            link = {"link": f"{DownloadsFileFolder}{savename}" , "linkName": f"{savename}"}
            links.append(link) if link not in links else next
            yield(" ") if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print()
            yield(msg) if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print(msg)          

        elif("DragonFly" in collectionSelector):
            msg = "Confronti YAROT <---> DRAGONFLY\n"
            yield(msg) if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print(msg)
            # SCADA
            dfDataHolder = {"tagData":[], "widgetData": []}
            yarotData = []

            for nomeGalleria in nomeGallerie:
                nomeGalleria = nomeGalleria.strip()
                tagsData = mongoSearch.readCollectionData(client["scada"], "scada_tag", name = nomeGalleria, regex = True)
                widgetsData = mongoSearch.readCollectionData(client["scada"], "scada_widget", name = nomeGalleria, regex = True)

                for tData in tagsData:
                    if("device" in tData.keys() and tData["device"]):
                        dfDataHolder["tagData"].append(tData["device"]) if tData not in dfDataHolder["tagData"] else next 

                for wData in widgetsData:
                    dfDataHolder["widgetData"].append(wData["device"]) if "device" in wData.keys() and wData["device"] not in dfDataHolder["widgetData"] else next 

                # YAROT 
                assetsData = mongoSearch.readCollectionData(client[yarot], "assets", name = nomeGalleria, regex = True)
                for aData in assetsData:        
                    if(aData and "lifeCycle" in aData.keys() and "READY" in aData["lifeCycle"]):
                        yarotData.append(aData["name"]) if aData["name"] not in yarotData else next 


            commonTag_Yarot, uniqTag, uniqYarot_Tag = (sharedCode.compareLists(dfDataHolder["tagData"], yarotData))
            dfTagsYarot_Common = pd.DataFrame(dtype=str)
            dfTags = pd.DataFrame(dtype=str)
            dfYarot_Tags = pd.DataFrame(dtype=str)

            for index, value in enumerate(commonTag_Yarot):
                dfTagsYarot_Common.loc[index,"common Tags_Yarot"] = value

            for index, value in enumerate(uniqTag):
                dfTags.loc[index,"onlyTags"] = value

            for index, value in enumerate(uniqYarot_Tag):
                dfYarot_Tags.loc[index,"onlyYarot (tag)"] = value

            commonWidget_Yarot, uniqWidget, uniqYarot_Widget = (sharedCode.compareLists(dfDataHolder["widgetData"], yarotData))

            dfWidgetsYarot_Common = pd.DataFrame(dtype=str)
            dfWidgets = pd.DataFrame(dtype=str)
            dfYarot_Widgets = pd.DataFrame(dtype=str)

            for index, value in enumerate(commonWidget_Yarot):
                dfWidgetsYarot_Common.loc[index,"common Widgets_Yarot"] = value

            for index, value in enumerate(uniqWidget):
                dfWidgets.loc[index,"onlyWidgets"] = value

            for index, value in enumerate(uniqYarot_Widget):
                dfYarot_Widgets.loc[index,"onlyYarot (widget)"] = value

            yield(" ") if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print()
            msg = (f"total Tags: {len(dfDataHolder["tagData"])} | total Yarot: {len(yarotData)}")
            yield(msg) if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print(msg)

            msg = (f"\tcommon Tags: {len(dfTagsYarot_Common)} \nTags: {len(dfTags)} \tYarot{len(dfYarot_Tags)}")
            yield(msg) if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print(msg)

            msg = (f"\ntotal Tags: {len(dfDataHolder["widgetData"])} | total Yarot: {len(yarotData)}")
            yield(msg) if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print(msg)

            msg = (f"\tcommon Widgets: {len(commonWidget_Yarot)} \nTags: {len(uniqWidget)} \tYarot{len(uniqYarot_Widget)}")
            yield(msg) if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print(msg)

            df = {"common Tags_Yarot": dfTagsYarot_Common, "onlyTags": dfTags, "onlyYarot (tag)": dfYarot_Tags,
                "common Widgets_Yarot": dfWidgetsYarot_Common, "onlyWidgets": dfWidgets, "onlyYarot (widget)": dfYarot_Widgets}
            
            msg = ("Salvataggio...", sharedCode.rw_xlsx(path = DownloadsFileFolder, file = savename, df = df, mode = "save"))
            link = {"link": f"{DownloadsFileFolder}{savename}" , "linkName": f"{savename}"}
            links.append(link) if link not in links else next
            yield(" ") if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print()
            yield(msg) if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print(msg)
            
            yield {"progress": 100}
            if(errorsList):
                yield str(errorsList)
    
    except Exception as e:               
        error = f"An error occurred: {str(e)}"
        print(error)
        errorsList.append(error) if error not in errorsList else next
        traceback.print_exc()
        
    #yield(" ") if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print()
    #pathMsg = f"""<a href="downloads/{savename}" target="_blank">{savename}</a><br>"""     
    yield {"links": links}
    yield "Fine"
    #yield(pathMsg) if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print(pathMsg)
    

if __name__ == "__main__":
    None