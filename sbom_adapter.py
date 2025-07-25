import os
import json
import urllib.parse
from datetime import datetime

# === Configuration globale ===
INPUT_FOLDER = "InputFiles"
OUTPUT_FOLDER = "OutputFiles"


# === Fonctions utilitaires ===

def clean_name(name):
    """Nettoie les noms encodés en URL (pour affichage)"""
    return urllib.parse.unquote_plus(name)

def to_generic_purl(raw_name, version):
    """Crée une purl au format pkg:generic sans nettoyage"""
    if version:
        return f"pkg:generic/{raw_name}@{version}"
    return f"pkg:generic/{raw_name}"

def get_device_name(cdx_data):
    """Retourne le nom du périphérique, par défaut 'Unknown Device'"""
    for component in cdx_data.get("components", []):
        if "properties" in component:
            for prop in component["properties"]:
                if prop.get("name") in ["computer_name", "hostname"]:
                    return clean_name(prop.get("value", "Unknown Device"))
    return "Unknown Device"


# === Fonction principale de conversion ===

def convert_cdxgen_to_cyberwatch(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        cdx_data = json.load(f)

    cyberwatch_bom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "metadata": {
            "timestamp": cdx_data.get("metadata", {}).get("timestamp", datetime.utcnow().isoformat() + "Z"),
            "tools": {
                "components": [
                    {
                        "type": cdx_data["metadata"]["tools"]["components"][0]["type"],
                        "publisher": cdx_data["metadata"]["tools"]["components"][0].get("publisher", "Unknown"),
                        "name": cdx_data["metadata"]["tools"]["components"][0]["name"],
                        "version": cdx_data["metadata"]["tools"]["components"][0].get("version", "unknown"),
                    }
                ]
            },
            "component": {
                "bom-ref": "CycloneDXRef-device-generated",
                "type": "device",
                "name": clean_name(get_device_name(cdx_data)),
                "version": cdx_data["metadata"]["component"].get("version", "unknown")
            }
        },
        "components": []
    }

    # Ajout du système d’exploitation
    os_component = {
        "bom-ref": "CycloneDXRef-OperatingSystem-generated",
        "type": "operating-system",
        "name": clean_name(cdx_data["metadata"]["component"]["name"]),
        "properties": []
    }

    os_properties = {prop["name"]: prop["value"] for prop in cdx_data["metadata"]["component"].get("properties", [])}
    if "arch" in os_properties:
        os_component["properties"].append({"name": "ARCH", "value": os_properties["arch"]})
    if "build_version" in os_properties:
        os_component["properties"].append({
            "name": "OS_PRETTYNAME",
            "value": clean_name(cdx_data["metadata"]["component"]["name"])
        })

    cyberwatch_bom["components"].append(os_component)

    # Ajout des componants
    seen_refs = set()
    for component in cdx_data.get("components", []):
        raw_name = component.get("name", "unknown")
        name = clean_name(raw_name)
        version = component.get("version", "unknown")

        if raw_name.startswith("KB"):
            bom_ref = to_generic_purl(raw_name, "")
            version = ""
        else:
            bom_ref = to_generic_purl(raw_name, version)

        if bom_ref in seen_refs:
            continue
        seen_refs.add(bom_ref)

        new_component = {
            "bom-ref": bom_ref,
            "type": component.get("type", "library"),
            "name": name,
            "version": version,
            "purl": bom_ref
        }

        cyberwatch_bom["components"].append(new_component)

    # Sauvegarde
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(cyberwatch_bom, f, indent=2)

    print(f"Conversion terminée : {output_file}")


# === Traitement en lot ===

def process_folder(input_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for filename in os.listdir(input_folder):
        if filename.endswith(".json"):
            input_file = os.path.join(input_folder, filename)
            output_file = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}_converted.json")
            convert_cdxgen_to_cyberwatch(input_file, output_file)


# === Main ===

if __name__ == "__main__":
    process_folder(INPUT_FOLDER, OUTPUT_FOLDER)
