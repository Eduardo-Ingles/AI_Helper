# Download_DevicePositions.py
# Scarica le posizioni dei device di una galleria da smartscada
# e le esporta in un file Excel nella cartella downloads.
#
# Colonne output: subPlant | deviceName | left | top | zIndex | rotation

import pandas as pd
import traceback
import sys, os

from bson import ObjectId
import pymongo

project_root = os.getcwd()
sys.path.append(project_root)

from backend.scripts.SharedCode import sharedCode, mongoSearch


# ----------------------------------- START COSTANTI -----------------------------------#

DB_NAME      = "smartscada"
DOWNLOAD_DIR = project_root + sharedCode.loadSettings("paths", "downloadsFolder")

# ----------------------------------- END COSTANTI -----------------------------------#


def roundPosition(value):
    """
    Arrotondamento personalizzato:
        <= .5  → difetto  (es: 55.3 → 55 | 55.5 → 55)
         > .5  → eccesso  (es: 55.7 → 56)
    """
    try:
        f = float(value)
        truncated = int(f)
        return truncated if (f - truncated) <= 0.5 else truncated + 1
    except (ValueError, TypeError):
        return value


def process_files(sio, client_id, data, script, **kwargs):
    """
    Entry point chiamato da mainServer.py.

    Parametri in 'data':
        data["database"]  → "Quality" | "Produzione"
        data["galleria"]  → nome della galleria (es. "MONACO")
    """
    links = []
    try:
        chosenDB     = data.get("database", "Quality")
        nomeGalleria = str(data.get("galleria", "")).strip().upper()

        if not nomeGalleria:
            yield "Errore: nome galleria mancante."
            return

        # -- Connessione DB --
        dbAddress = "MongoProductionClient" if "prod" in chosenDB.lower() else "MongoQualityClient"
        client    = pymongo.MongoClient(sharedCode.loadSettings("dbSettings", dbAddress))
        currDB    = client[DB_NAME]

        yield f"Connesso a: {'PRODUZIONE' if 'prod' in chosenDB.lower() else 'QUALITY'} → {DB_NAME}"

        # -- Recupero plant --
        currPlant = mongoSearch.readCollectionData(currDB, "plant", name=nomeGalleria)
        if not currPlant:
            yield f"Galleria '{nomeGalleria}' non trovata."
            return

        totalSP = len(currPlant["subPlants"])
        yield f"Galleria trovata: {currPlant['name']} — {totalSP} subPlant"

        rows = []

        # -- Scansione subPlant --
        for prgrss, plantSubPlant in enumerate(currPlant["subPlants"]):
            subPlant = mongoSearch.readCollectionData(currDB, "subPlant", id=plantSubPlant.id)

            if not subPlant:
                yield f"SubPlant {plantSubPlant.id} non trovato, saltato."
                continue

            subPlantName    = subPlant.get("name", str(plantSubPlant.id))
            devicePositions = subPlant.get("devicePositions", [])

            yield f"{prgrss + 1}|{totalSP}: {subPlantName} — {len(devicePositions)} device"

            for devPos in devicePositions:
                deviceId = devPos.get("deviceId", "")

                # Risolve il nome del device
                deviceName = deviceId
                if deviceId:
                    try:
                        device     = mongoSearch.readCollectionData(currDB, "device", id=ObjectId(deviceId))
                        deviceName = device.get("name", deviceId) if device else deviceId
                    except Exception:
                        deviceName = deviceId

                rows.append({
                    "subPlant":   subPlantName,
                    "deviceName": deviceName,
                    "left":       roundPosition(devPos.get("left",     "")),
                    "top":        roundPosition(devPos.get("top",      "")),
                    "zIndex":     roundPosition(devPos.get("zIndex",   "")),
                    "rotation":   roundPosition(devPos.get("rotation", "")),
                })

            # Avanzamento percentuale
            progressMsg = sharedCode.progressYield(prgrss + 1, totalSP)
            if progressMsg:
                yield progressMsg

        # -- Salvataggio Excel --
        if not rows:
            yield "Nessuna posizione trovata, file non generato."
            return

        df = pd.DataFrame(rows, columns=["subPlant", "deviceName", "left", "top", "zIndex", "rotation"])

        outputFileName = f"DevicePositions_{nomeGalleria}_{sharedCode.timeStamp()}.xlsx"
        outputPath     = os.path.join(DOWNLOAD_DIR, outputFileName)
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)

        df.to_excel(outputPath, index=False)

        yield f"File salvato: {outputFileName} ({len(rows)} righe)"

        # -- Link di download per il frontend --
        ylink = {"link": outputPath, "linkName": outputFileName}
        links.append(ylink)
        yield {"links": links}

        yield {"status": "completed"}

    except Exception as e:
        yield f"Errore: {str(e)}"
        yield {"status": f"failed: {str(e)}"}
        traceback.print_exc()


# ----------------------------------- MAIN (test locale) -----------------------------------#

if __name__ == "__main__":
    testData = {
        "database": "Quality",
        "galleria": "MONACO",
    }
    for msg in process_files(None, None, testData, None):
        print(msg)