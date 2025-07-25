# CDXGen to Cyberwatch BOM Converter

Ce script Python permet de convertir un fichier OBOM CycloneDX (type `obom.json`) généré avec [`cdxgen`](https://cyclonedx.github.io/cdxgen/#/CLI) en un format compatible avec Cyberwatch.

## Installation

```
git clone https://github.com/Galeax/cyberwatch-sbom-adapter.git
```

## Utilisation

1. Générer les fichiers OBOM avec CDXGen, à l'aide de la commande `cdxgen -t os` (à générer sur chaque machine).
2. Placer les fichiers obtenus dans le dossier `InputFiles`
3. Lancer le script :

```bash
python3 sbom_adapter.py
```

4. Les fichiers convertis seront générés automatiquement dans le dossier `OutputFiles/`.

5. Vous pourrez alors importer le tout dans Cyberwatch via `cyberwatch-cli airgap upload` ou via l'interface (Actifs > Airgap).

## Licence

Ce projet est couvert par la licence MIT.

## Contact

Fait avec ❤️ en 🇫🇷 par <a href="https://galeax.com"><img src="https://galeax.com/wp-content/uploads/2024/01/logo_galeax_blue-e1705315482396.png" width=25%>
