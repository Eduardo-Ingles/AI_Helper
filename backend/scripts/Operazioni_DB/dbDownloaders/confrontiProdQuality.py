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


def mainCall(nomeGallerie, UploadsFileFolder, DownloadsFileFolder, CpuCoreNumber, collectionSelector, **kwargs):
    """
    Confronto INCROCIATO:
        SmartScada / DragonFly  di QUALITY  <--->  Yarot di PROD
    """
    links = []
    try:
        yield {"progress": 0}

        # --- parsing nomeGallerie ---
        for dividerChar in dividerChars:
            if dividerChar in nomeGallerie:
                nomeGallerie = nomeGallerie.strip().split(dividerChar)
                break
        if isinstance(nomeGallerie, str):
            nomeGallerie = nomeGallerie.strip().split()

        if not collectionSelector:
            return None

        clientProd    = pymongo.MongoClient(sharedCode.loadSettings("globalSettings", "MongoProductionClient"))
        clientQuality = pymongo.MongoClient(sharedCode.loadSettings("globalSettings", "MongoQualityClient"))
        yarotProd     = "yarot2"

        savename = (
            f"{prefisso}-CROSS-{collectionSelector}"
            f"_{'-'.join(nomeGallerie)}"
            f"_{sharedCode.timeStamp(fullDate=True)}.xlsx"
        )

    except Exception as e:
        error = f"An error occurred: {str(e)}"
        print(error)
        errorsList.append(error) if error not in errorsList else next
        traceback.print_exc()
        return

    def buildDf(values, colName):
        df = pd.DataFrame(dtype=str)
        for i, v in enumerate(values):
            df.loc[i, colName] = v
        return df

    try:
        # =====================================================================
        #  SMARTSCADA QUALITY  <--->  YAROT PROD
        # =====================================================================
        if "SmartScada" in collectionSelector:
            msg = "Confronto CROSS  [SmartScada QUALITY  <--->  Yarot PROD]\n"
            yield msg if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print(msg)

            scadaQual_Name  = []
            scadaQual_ID   = []
            yarotProdData_id   = []
            yarotProdData_Name = []

            for nomeGalleria in nomeGallerie:
                nomeGalleria = nomeGalleria.strip()

                # --- SmartScada da QUALITY ---
                yield f"[QUALITY] Ricerca '{nomeGalleria}' in SmartScada..."
                SmartScadaDbData = mongoSearch.readCollectionData(
                    clientQuality["smartscada"], "device", name=nomeGalleria, regex=True
                )
                for d in SmartScadaDbData:
                    if "externalId" in d and d["externalId"]:
                        scadaQual_ID.append(d["externalId"]) if d["externalId"] not in scadaQual_ID else next
                    if "name" in d and d["name"]:
                        scadaQual_Name.append(d["name"]) if d["name"] not in scadaQual_Name else next

                # --- verifica ID in Yarot PROD ---
                yield f"[YAROT PROD] Verifica externalId in Yarot PROD..."
                for indx, sdevice in enumerate(scadaQual_ID):
                    results = mongoSearch.findCollectionData(clientProd[yarotProd], "assets", querry={"name": sdevice})
                    for result in results:
                        if result and "lifeCycle" in result and "READY" in result["lifeCycle"] and result["type"] == "DeviceSchema":
                            yarotProdData_id.append(result["name"]) if result["name"] not in yarotProdData_id else next
                        elif result:
                            msg = f"Errore: {result['name']} -> lifeCycle: {result['lifeCycle']} & type: {result['type']}"
                            yield msg if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print(msg)
                    prog = sharedCode.progressYield(indx + 1, len(scadaQual_ID))
                    if prog: yield prog

                # --- verifica Name in Yarot PROD ---
                yield f"[YAROT PROD] Verifica name in Yarot PROD..."
                for indx, sdevice in enumerate(scadaQual_Name):
                    results = mongoSearch.findCollectionData(clientProd[yarotProd], "assets", querry={"name": sdevice})
                    for result in results:
                        if result and "lifeCycle" in result and "READY" in result["lifeCycle"] and result["type"] == "DeviceSchema":
                            yarotProdData_Name.append(result["name"]) if result["name"] not in yarotProdData_Name else next
                        elif result:
                            msg = f"Errore: {result['name']} -> lifeCycle: {result['lifeCycle']} & type: {result['type']}"
                            yield msg if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print(msg)
                    prog = sharedCode.progressYield(indx + 1, len(scadaQual_Name))
                    if prog: yield prog

            # --- confronto ---
            commonA, onlyScadaQualA, onlyYarotProdA = sharedCode.compareLists(scadaQual_Name,  yarotProdData_Name + yarotProdData_id)
            commonB, onlyScadaQualB, onlyYarotProdB = sharedCode.compareLists(scadaQual_ID,   yarotProdData_id + yarotProdData_Name)

            yield " "
            msg = (
                f"SmartScadaQuality_Name: {len(scadaQual_Name)}\t-\tYarotProd: {len(yarotProdData_Name) + len(yarotProdData_id)}\n"
                f"common_Name: {len(commonA)}\t|\tonlyScadaQuality_Name: {len(onlyScadaQualA)}\t|\tonlyYarotProd_Name: {len(onlyYarotProdA)}\n"
                f"SmartScadaQuality_ID:  {len(scadaQual_ID)}\t-\tYarotProd: {len(yarotProdData_id) + len(yarotProdData_Name)}\n"
                f"common_ID:  {len(commonB)}\t|\tonlyScadaQuality_ID:  {len(onlyScadaQualB)}\t|\tonlyYarotProd_ID:  {len(onlyYarotProdB)}"
            )
            yield msg if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print(msg)

            df = {
                "common_Name":           buildDf(commonA,         "common_Name"),
                "onlyScadaQuality_Name": buildDf(onlyScadaQualA,  "onlyScadaQuality_Name"),
                "onlyYarotProd_Name":    buildDf(onlyYarotProdA,  "onlyYarotProd_Name"),
                "common_ID":            buildDf(commonB,         "common_ID"),
                "onlyScadaQuality_ID":  buildDf(onlyScadaQualB,  "onlyScadaQuality_ID"),
                "onlyYarotProd_ID":     buildDf(onlyYarotProdB,  "onlyYarotProd_ID"),
            }

            msg = ("Salvataggio...", sharedCode.rw_xlsx(path=DownloadsFileFolder, file=savename, df=df, mode="save"))
            link = {"link": f"{DownloadsFileFolder}{savename}", "linkName": f"{savename}"}
            links.append(link) if link not in links else next
            yield " "
            yield msg if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print(msg)

        # =====================================================================
        #  DRAGONFLY QUALITY  <--->  YAROT PROD
        # =====================================================================
        elif "DragonFly" in collectionSelector:
            msg = "Confronto CROSS  [DragonFly QUALITY  <--->  Yarot PROD]\n"
            yield msg if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print(msg)

            qualHolder    = {"tagData": [], "widgetData": []}
            yarotProd_tag    = []
            yarotProd_widget = []
            yarotProdData    = []

            for nomeGalleria in nomeGallerie:
                nomeGalleria = nomeGalleria.strip()

                yield f"[QUALITY] Ricerca '{nomeGalleria}' in DragonFly (tags)..."
                for d in mongoSearch.readCollectionData(clientQuality["scada"], "scada_tag", name=nomeGalleria, regex=True):
                    if "device" in d and d["device"]:
                        qualHolder["tagData"].append(d["device"]) if d["device"] not in qualHolder["tagData"] else next

                yield f"[QUALITY] Ricerca '{nomeGalleria}' in DragonFly (widgets)..."
                for d in mongoSearch.readCollectionData(clientQuality["scada"], "scada_widget", name=nomeGalleria, regex=True):
                    if "device" in d and d["device"]:
                        qualHolder["widgetData"].append(d["device"]) if d["device"] not in qualHolder["widgetData"] else next

                # Yarot PROD diretto per galleria
                yield f"[YAROT PROD] Ricerca '{nomeGalleria}'..."
                for d in mongoSearch.readCollectionData(clientProd[yarotProd], "assets", name=nomeGalleria, regex=True):
                    if d and "lifeCycle" in d and "READY" in d["lifeCycle"].upper() and d.get("type") == "DeviceSchema":
                        yarotProdData.append(d["name"]) if d["name"] not in yarotProdData else next

            # verifica device DragonFly QUALITY in Yarot PROD (tags)
            yield "[YAROT PROD] Verifica device DragonFly QUALITY (tags)..."
            for indx, dev in enumerate(qualHolder["tagData"]):
                for r in mongoSearch.findCollectionData(clientProd[yarotProd], "assets", querry={"name": dev}):
                    if r and "lifeCycle" in r and "READY" in r["lifeCycle"] and r.get("type") == "DeviceSchema":
                        yarotProd_tag.append(r["name"]) if r["name"] not in yarotProd_tag else next
                prog = sharedCode.progressYield(indx + 1, len(qualHolder["tagData"]))
                if prog: yield prog

            # verifica device DragonFly QUALITY in Yarot PROD (widgets)
            yield "[YAROT PROD] Verifica device DragonFly QUALITY (widgets)..."
            for indx, dev in enumerate(qualHolder["widgetData"]):
                for r in mongoSearch.findCollectionData(clientProd[yarotProd], "assets", querry={"name": dev}):
                    if r and "lifeCycle" in r and "READY" in r["lifeCycle"] and r.get("type") == "DeviceSchema":
                        yarotProd_widget.append(r["name"]) if r["name"] not in yarotProd_widget else next
                prog = sharedCode.progressYield(indx + 1, len(qualHolder["widgetData"]))
                if prog: yield prog

            common_tag,    onlyDfQual_tag,    onlyYarotProd_tag    = sharedCode.compareLists(qualHolder["tagData"],    yarotProd_tag + yarotProdData)
            common_widget, onlyDfQual_widget, onlyYarotProd_widget = sharedCode.compareLists(qualHolder["widgetData"], yarotProd_widget + yarotProdData)

            yield " "
            msg = (
                f"Tags:   DfQuality={len(qualHolder['tagData'])}\t-\tYarotProd={len(yarotProd_tag)}\n"
                f"        common={len(common_tag)}\t|\tonlyDfQuality={len(onlyDfQual_tag)}\t|\tonlyYarotProd={len(onlyYarotProd_tag)}\n"
                f"Widget: DfQuality={len(qualHolder['widgetData'])}\t-\tYarotProd={len(yarotProd_widget)}\n"
                f"        common={len(common_widget)}\t|\tonlyDfQuality={len(onlyDfQual_widget)}\t|\tonlyYarotProd={len(onlyYarotProd_widget)}"
            )
            yield msg if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print(msg)

            df = {
                "common_tag":           buildDf(common_tag,           "common_tag"),
                "onlyDfQuality_tag":    buildDf(onlyDfQual_tag,       "onlyDfQuality_tag"),
                "onlyYarotProd_tag":    buildDf(onlyYarotProd_tag,    "onlyYarotProd_tag"),
                "common_widget":        buildDf(common_widget,        "common_widget"),
                "onlyDfQuality_widget": buildDf(onlyDfQual_widget,    "onlyDfQuality_widget"),
                "onlyYarotProd_widget": buildDf(onlyYarotProd_widget, "onlyYarotProd_widget"),
            }

            msg = ("Salvataggio...", sharedCode.rw_xlsx(path=DownloadsFileFolder, file=savename, df=df, mode="save"))
            link = {"link": f"{DownloadsFileFolder}{savename}", "linkName": f"{savename}"}
            links.append(link) if link not in links else next
            yield " "
            yield msg if "yieldFlag" in kwargs and kwargs.get("yieldFlag") else print(msg)

        yield {"progress": 100}
        if errorsList:
            yield str(errorsList)

    except Exception as e:
        error = f"An error occurred: {str(e)}"
        print(error)
        errorsList.append(error) if error not in errorsList else next
        traceback.print_exc()

    yield {"links": links}


if __name__ == "__main__":
    None