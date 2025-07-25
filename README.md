# CDXGen to Cyberwatch BOM Converter

Ce script Python permet de convertir un fichier CycloneDX (`obom.json`) généré avec [`cdxgen`](https://cyclonedx.github.io/cdxgen/#/CLI) en un format compatible avec Cyberwatch.

## ▶️ Utilisation

1. Placer les fichiers générés avec `cdxgen -t os` dans le dossier `inputjson`
2. Lancer le script :

```bash
python sbom_adapter.py
```

3. Les fichiers convertis seront générés automatiquement dans le dossier `outputjson/`.
