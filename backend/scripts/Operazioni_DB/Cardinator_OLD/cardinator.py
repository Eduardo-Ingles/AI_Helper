#cardinator

import pymongo
from bson import ObjectId
from bson.dbref import DBRef
import sys
import os
import copy

project_root = os.getcwd()
sys.path.append(project_root)

#from scripts.SharedCode import sharedCode

from backend.scripts.Operazioni_DB.Cardinator_OLD import caricaFileImpianto
from backend.scripts.Operazioni_DB.Cardinator_OLD import subPlantCreator
from backend.scripts.Operazioni_DB.Cardinator_OLD import plantCreator
#from scripts.Operazioni_DB.Cardinator_OLD import sharedCode
#from scripts.Cardinator import caricaFileImpianto
#from scripts.Cardinator import subPlantCreator
#from scripts.Cardinator import plantCreator


from backend.scripts.SharedCode import sharedCode as sc


def mainFunCall(filePath, plantName, chosenDB, **kwargs):
    yieldFlag = kwargs.get("yieldFlag")    
    if(plantName): 
        client = None
        yield f"Connessione al server."
        #client = pymongo.MongoClient(sc.loadSettings("dragonFlySettings", "MongoClient"))   
        if(chosenDB and "prod" in chosenDB.lower()):
            client = pymongo.MongoClient(sc.loadSettings("dbSettings", "MongoProductionClient")) 
        else:     
            client = pymongo.MongoClient(sc.loadSettings("dbSettings", "MongoQualityClient")) 
        if(not client):
            yield f"Impossibile connettersi al db: {chosenDB}!"
            return None
        
        yield f"Caricamento dati."
        arrDatiPlant = caricaFileImpianto.CaricaDaFileImpianto(filePath + plantName)  
        #for item in arrDatiPlant:
        #    print(item.subPlantName)
        for output in caricaFileImpianto.printaFunc(arrDatiPlant, yieldFlag = yieldFlag):
            yield output
        
        print("creazione impianto.")
        yield f"creazione impianto."
        plantID = plantCreator.creaEdInserisci(client, arrDatiPlant[0])  
        t_ID = copy.copy(str(plantID))
        yield f"Impianto creato con id: | {t_ID} |"
        
        print("creazione sotto-impianti.")
        yield f"creazione sotto-impianti."
        subPlantIdsArry = subPlantCreator.creaSottoimpianti(client, plantID, arrDatiPlant)    # crea impianto con dati relativi (crea Gruppi prima) e restituisce gli ID dei subPlants
        updated_subPlants = []
        yield f"id impianti:"
        for i in range(len(subPlantIdsArry)):        
            updated_subPlants.append(DBRef("subPlant", ObjectId(subPlantIdsArry[i])))
            yield f"\t{DBRef("subPlant", ObjectId(subPlantIdsArry[i]))}"  
        yield f"update documento."          
        plantCreator.update_document_by_id(client, "smartscada", "plant", plantID, updated_subPlants)   # inserisce i subPlants

    else: 
        return print("ERRORE")


if __name__ == '__main__':
    filePath = r"c:\\path HERE\\"
    fileName = "creazione card galleria CASOLA" + ".xlsx"
    mainFunCall(filePath, fileName)