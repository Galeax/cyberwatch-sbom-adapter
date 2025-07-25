import os
import json
import re, urllib.parse
from typing import Optional
from datetime import datetime, timezone

# === Configuration globale ===
INPUT_FOLDER = "InputFiles"
OUTPUT_FOLDER = "OutputFiles"

# === Utilitaires === ---------------------------------------------------------

def clean_name(name: str) -> str:
    """Décodage lisible pour affichage."""
    return urllib.parse.unquote_plus(name)

def to_generic_purl(raw_name: str, version: str) -> str:
    """PURL au format pkg:generic (encodé brut)."""
    return f"pkg:generic/{raw_name}@{version}" if version else f"pkg:generic/{raw_name}"

def get_device_name(cdx_data: dict) -> str:
    """Nom du poste (hostname/computer_name)."""
    for comp in cdx_data.get("components", []):
        for prop in comp.get("properties", []):
            if prop.get("name") in ("computer_name", "hostname"):
                return clean_name(prop.get("value", "Unknown Device"))
    return "Unknown Device"

def normalize_arch(raw_arch: str) -> str:
    """Mappe l’architecture vers la notation Cyberwatch."""
    raw_lower = raw_arch.lower()
    if "64" in raw_lower:
        return "AMD64"
    if "32" in raw_lower:
        return "x86"
    return raw_arch.upper()

def build_os_pretty_name(raw_name: str, version: Optional[str] = "") -> str:
    """
    Exemples :
      - 'Microsoft Windows 11 Business' + '24H2'  -> 'Windows 11 24H2'
      - 'Windows 10 Enterprise 22H2'    + ''      -> 'Windows 10 22H2'
      - 'Windows 10 Pro'                + ''      -> 'Windows 10'
    """
    text = re.sub(r"\s+", " ", urllib.parse.unquote_plus(raw_name)).strip()

    m = re.search(r"(windows)\s+(\d+)", text, flags=re.IGNORECASE)
    if not m:          
        base = text
        release = version
    else:
        base = f"Windows {m.group(2)}"   # Windows + numéro majeur

        after = text[m.end():].strip()
        tag_match = re.match(r"(\d{2}H[12])", after, flags=re.IGNORECASE)
        release = tag_match.group(1).upper() if tag_match else version

    pretty = f"{base} {release}".strip()
    return pretty

# === Conversion principale === ----------------------------------------------

def convert_cdxgen_to_cyberwatch(input_file: str, output_file: str) -> None:
    with open(input_file, encoding="utf-8") as f:
        cdx_data = json.load(f)

    ts_raw = cdx_data.get("metadata", {}).get("timestamp")
    ts_obj = (
        datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
        if ts_raw else datetime.now(timezone.utc)
    )
    ts_iso = ts_obj.strftime("%Y-%m-%dT%H:%M:%SZ")           
    ts_version = ts_iso                                      

    # --- Bloc metadata ------------------------------------------------------
    cyberwatch_bom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "metadata": {
            "timestamp": ts_iso,
            "tools": {
                "components": [
                    {   # Outil Cyberwatch imposé
                        "type": "application",
                        "publisher": "Cyberwatch",
                        "name": "Cyberwatch",
                        "version": "14.8.5"
                    }
                ]
            },
            "component": {
                "bom-ref": "CycloneDXRef-desktop-generated",
                "type": "device",
                "name": get_device_name(cdx_data),
                "version": ts_version
            }
        },
        "components": []
    }

    # --- Composant OS -------------------------------------------------------
    os_meta = cdx_data["metadata"]["component"]
    os_arch = normalize_arch(
        next((p["value"] for p in os_meta.get("properties", [])
              if p["name"] == "arch"), "unknown")
    )
    os_pretty = build_os_pretty_name(os_meta["name"], os_meta.get("version", ""))

    os_component = {
        "bom-ref": "CycloneDXRef-OperatingSystem-generated",
        "type": "operating-system",
        "name": os_pretty,
        "properties": [
            {"name": "OS_PRETTYNAME", "value": os_pretty},
            {"name": "ARCH", "value": os_arch}
        ]
    }
    cyberwatch_bom["components"].append(os_component)

    # --- Composants logiciels ----------------------------------------------
    seen_refs = set()
    for comp in cdx_data.get("components", []):
        raw_name = comp.get("name", "unknown")
        version = comp.get("version", "unknown")

        bom_ref = to_generic_purl(raw_name, "" if raw_name.startswith("KB") else version)
        if bom_ref in seen_refs:
            continue
        seen_refs.add(bom_ref)

        cyberwatch_bom["components"].append({
            "bom-ref": bom_ref,
            "type": comp.get("type", "library"),
            "name": clean_name(raw_name),
            "version": "" if raw_name.startswith("KB") else version,
            "purl": bom_ref
        })

    # --- Écriture fichier ---------------------------------------------------
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(cyberwatch_bom, f, indent=2)
    print(f"✅ Conversion terminée : {output_file}")

def process_folder(input_folder: str, output_folder: str) -> None:
    os.makedirs(output_folder, exist_ok=True)
    for fname in os.listdir(input_folder):
        if fname.endswith(".json"):
            in_file = os.path.join(input_folder, fname)
            out_file = os.path.join(
                output_folder, f"{os.path.splitext(fname)[0]}_converted.json"
            )
            convert_cdxgen_to_cyberwatch(in_file, out_file)

# === Point d’entrée ----------------------------------------------------------

if __name__ == "__main__":
    process_folder(INPUT_FOLDER, OUTPUT_FOLDER)
