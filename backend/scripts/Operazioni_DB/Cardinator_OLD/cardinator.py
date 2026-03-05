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


#def mainFunCall(filePath, plantName, chosenDB, **kwargs):
#    yieldFlag = kwargs.get("yieldFlag")    
#    if(plantName): 
#        client = None
#        yield f"Connessione al server."
#        #client = pymongo.MongoClient(sc.loadSettings("dragonFlySettings", "MongoClient"))   
#        if(chosenDB and "prod" in chosenDB.lower()):
#            client = pymongo.MongoClient(sc.loadSettings("dbSettings", "MongoProductionClient")) 
#        else:     
#            client = pymongo.MongoClient(sc.loadSettings("dbSettings", "MongoQualityClient")) 
#        if(not client):
#            yield f"Impossibile connettersi al db: {chosenDB}!"
#            return None
#        
#        yield f"Caricamento dati."
#        arrDatiPlant = caricaFileImpianto.CaricaDaFileImpianto(filePath + plantName)  
#        #for item in arrDatiPlant:
#        #    print(item.subPlantName)
#        for output in caricaFileImpianto.printaFunc(arrDatiPlant, yieldFlag = yieldFlag):
#            yield output
#        
#        print("creazione impianto.")
#        yield f"creazione impianto."
#        plantID = plantCreator.creaEdInserisci(client, arrDatiPlant[0])  
#        t_ID = copy.copy(str(plantID))
#        yield f"Impianto creato con id: | {t_ID} |"
#        
#        print("creazione sotto-impianti.")
#        yield f"creazione sotto-impianti."
#        subPlantIdsArry = subPlantCreator.creaSottoimpianti(client, plantID, arrDatiPlant)    # crea impianto con dati relativi (crea Gruppi prima) e restituisce gli ID dei subPlants
#        updated_subPlants = []
#        yield f"id impianti:"
#        for i in range(len(subPlantIdsArry)):        
#            updated_subPlants.append(DBRef("subPlant", ObjectId(subPlantIdsArry[i])))
#            yield f"\t{DBRef("subPlant", ObjectId(subPlantIdsArry[i]))}"  
#        yield f"update documento."          
#        plantCreator.update_document_by_id(client, "smartscada", "plant", plantID, updated_subPlants)   # inserisce i subPlants
#
#    else: 
#        return print("ERRORE")

def mainFunCall(filePath, plantName, chosenDB, **kwargs):
    yieldFlag = kwargs.get("yieldFlag")
    mode = kwargs.get("mode", "create")   
    
    if(plantName): 
        client = None
        yield f"Connessione al server."
        if(chosenDB and "prod" in chosenDB.lower()):
            client = pymongo.MongoClient(sc.loadSettings("dbSettings", "MongoProductionClient")) 
        else:     
            client = pymongo.MongoClient(sc.loadSettings("dbSettings", "MongoQualityClient")) 
        if(not client):
            yield f"Impossibile connettersi al db: {chosenDB}!"
            return None
        
        yield f"Caricamento dati."
        arrDatiPlant = caricaFileImpianto.CaricaDaFileImpianto(filePath + plantName)  
        for output in caricaFileImpianto.printaFunc(arrDatiPlant, yieldFlag=yieldFlag):
            yield output

        # --- BLOCCO MODIFICATO ---
        if mode == "update":
            yield f"Ricerca impianto esistente..."
            existingPlant = plantCreator.trovaImpiantoEsistente(client, arrDatiPlant[0].nomeGalleria)
            if not existingPlant:
                yield f"ERRORE: Impianto '{arrDatiPlant[0].nomeGalleria}' non trovato! Usa modalità 'Crea'."
                return
            plantID = existingPlant["_id"]
            existing_subPlants = existingPlant.get("subPlants", [])
            yield f"Impianto trovato con id: | {str(plantID)} |"

            # --- CONTROLLO SICUREZZA ---
            db = client["smartscada"]
            nomi_esistenti = []
            for sp_ref in existing_subPlants:
                sp_doc = db["subPlant"].find_one({"_id": sp_ref.id})
                if sp_doc:
                    nomi_esistenti.append(sp_doc["name"].upper())

            yield f"SubPlant già esistenti: {len(nomi_esistenti)}"

            nomi_nuovi = [
                (arrDatiPlant[0].nomeGalleria.replace(" ", "-") + "-" + d.subPlantName).upper()
                for d in arrDatiPlant[1:]
            ]
            duplicati = [n for n in nomi_nuovi if n in nomi_esistenti]

            if duplicati:
                yield f"ATTENZIONE: questi subPlant esistono già e verranno saltati:"
                for d in duplicati:
                    yield f"\t- {d}"

            arrDatiPlant_filtrato = [arrDatiPlant[0]] + [
                d for d in arrDatiPlant[1:]
                if (arrDatiPlant[0].nomeGalleria.replace(" ", "-") + "-" + d.subPlantName).upper() not in nomi_esistenti
            ]

            if len(arrDatiPlant_filtrato) == 1:
                yield f"NESSUN nuovo subPlant da aggiungere — tutti già presenti!"
                return

            yield f"Nuovi subPlant da aggiungere: {len(arrDatiPlant_filtrato) - 1}"
            arrDatiPlant = arrDatiPlant_filtrato
            # --- FINE CONTROLLO SICUREZZA ---

        else:
            yield f"Creazione impianto."
            plantID = plantCreator.creaEdInserisci(client, arrDatiPlant[0])  
            existing_subPlants = []
            t_ID = copy.copy(str(plantID))
            yield f"Impianto creato con id: | {t_ID} |"
        # --- FINE BLOCCO MODIFICATO ---

        yield f"Creazione sotto-impianti."
        subPlantIdsArry = subPlantCreator.creaSottoimpianti(client, plantID, arrDatiPlant)
        updated_subPlants = existing_subPlants + [DBRef("subPlant", ObjectId(id)) for id in subPlantIdsArry]

        yield f"id sotto-impianti:"
        for id in subPlantIdsArry:        
            yield f"\t{DBRef('subPlant', ObjectId(id))}"  

        yield f"Update documento."          
        plantCreator.update_document_by_id(client, "smartscada", "plant", plantID, updated_subPlants)

        # --- AGGIORNAMENTO LINK SU IMPIANTO-ELETTRICO ESISTENTE ---
        if mode == "update":
            db = client["smartscada"]
            nomeGalleria = arrDatiPlant[0].nomeGalleria.replace(" ", "-")
            nomeImpElettrico = (nomeGalleria + "-IMPIANTO-ELETTRICO").upper()
            
            impElettrico = db["subPlant"].find_one({"name": nomeImpElettrico})
            if impElettrico:
                yield f"Aggiornamento link su {nomeImpElettrico}..."
                
                nuovi_link = subPlantCreator.linkBuilder(arrDatiPlant, 0)
                
                if nuovi_link:
                    existing_configs = impElettrico.get("customTemplateConfigs", [])
                    existing_names = [c["name"] for c in existing_configs]
                    
                    link_da_aggiungere = [l for l in nuovi_link if l["name"] not in existing_names]
                    
                    if link_da_aggiungere:
                        updated_configs = existing_configs + link_da_aggiungere
                        db["subPlant"].update_one(
                            {"_id": impElettrico["_id"]},
                            {"$set": {"customTemplateConfigs": updated_configs}}
                        )
                        yield f"Aggiunti {len(link_da_aggiungere)} nuovi link a {nomeImpElettrico}"
                    else:
                        yield f"Nessun nuovo link da aggiungere a {nomeImpElettrico}"
                else:
                    yield f"Nessun link trovato nei nuovi subPlant"
            else:
                yield f"ATTENZIONE: {nomeImpElettrico} non trovato nel DB"
        # --- FINE AGGIORNAMENTO LINK ---

    else: 
        return print("ERRORE")

if __name__ == '__main__':
    filePath = r"c:\\path HERE\\"
    fileName = "creazione card galleria CASOLA" + ".xlsx"
    mainFunCall(filePath, fileName)