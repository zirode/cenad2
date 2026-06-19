# README — Application CENAD
## Université Nord d'Antsiranana | Association CENAD (fondée 2012)

---

## 1. Structure du projet

```
cenad/
├── main.py                    # Point d'entrée
├── buildozer.spec             # Config build Android
├── cenad.db                   # Base SQLite (auto-créée au 1er lancement)
│
├── data/
│   ├── schema.sql             # Schéma de la base de données
│   ├── database.py            # CRUD SQLite
│   ├── models.py              # Dataclasses (Membre, President...)
│   └── importer.py            # Import fichier ZIP (CSV + photos)
│
├── ui/
│   ├── screens.py             # Tous les écrans Kivy
│   ├── widgets.py             # Composants réutilisables
│   └── themes.py              # Gestion thème sombre/clair
│
├── utils/
│   └── helpers.py             # Fonctions utilitaires
│
└── assets/
    ├── images/                # Photos membres et présidents
    ├── icones/                # Icônes de l'UI
    │   └── avatar_default.png # Avatar par défaut (obligatoire)
    └── logos/
        └── cenad_logo.png     # Logo de l'association
```

---

## 2. Installation (PC / Test)

```bash
# Créer un environnement virtuel
python3 -m venv venv
source venv/bin/activate       # Linux/Mac
venv\Scripts\activate          # Windows

# Installer les dépendances
pip install kivy kivymd

# Lancer l'application
cd cenad/
python main.py
```

---

## 3. Build Android (Buildozer)

```bash
# Installer buildozer (Linux recommandé / WSL2 sur Windows)
pip install buildozer

# Installer les dépendances système (Ubuntu/Debian)
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip \
    autoconf libtool pkg-config zlib1g-dev libncurses5-dev \
    libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev

# Premier build (télécharge NDK/SDK automatiquement — peut prendre 30 min)
cd cenad/
buildozer android debug

# Le fichier APK se trouve dans :
# cenad/bin/cenad-1.0.0-arm64-v8a_armeabi-v7a-debug.apk
```

---

## 4. Structure du fichier ZIP d'import

Votre fichier ZIP doit respecter exactement cette structure :

```
import_cenad.zip
├── membres.csv
├── presidents.csv
├── batiments.csv
├── etablissements.csv
├── filieres.csv
└── photos/
    ├── photo_jean_rakoto.jpg
    ├── photo_marie_razafy.jpg
    └── logo_president_2023.jpg
```

### membres.csv
```csv
id,nom,prenom,etablissement,niveau,commune,telephone,batiment,photo_filename
1,Rakoto,Jean,FSS,Licence 2,Andapa,0341234567,Bâtiment A,photo_jean_rakoto.jpg
2,Razafy,Marie,IUT,DUT 1,Antsahanoro,0341234568,,
```

### presidents.csv
```csv
id,nom,prenom,annee_mandat,photo_filename,actions_marquantes
1,Andriamaro,Hery,2012-2013,,Fondation de l'association
2,Rakoto,Jean,2023-2024,logo_president_2023.jpg,Organisation journée culturelle
```

### batiments.csv
```csv
id,nom,description
1,Bâtiment A,Résidence principale nord du campus
2,Bâtiment B,Résidence secondaire avec cafétéria
```

### etablissements.csv
```csv
id,nom,mission
1,FSS,Faculté des Sciences et Santé
2,IUT,Institut Universitaire de Technologie
```

### filieres.csv
```csv
id,nom,etablissement_id
1,Biologie,1
2,Chimie,1
3,Génie Informatique,2
```

---

## 5. Ajouter le logo et les assets manuellement

1. Placer le logo : `assets/logos/cenad_logo.png`
2. Placer un avatar par défaut : `assets/icons/avatar_default.png`
3. Les photos importées via ZIP sont automatiquement copiées dans `assets/images/`

---

## 6. Communes d'Andapa disponibles (22)

Andapa, Antsahanoro, Ambalamanasy II, Ambodiangezoka, Ambodimanga Rantabe,
Ambodivoahangy, Ambohimanana, Ambohimitsinjo, Andrakata, Anjialavabe,
Antsahamena, Antsambaharo, Antsoha, Bealampona, Belaoko Marovato,
Belanitra, Doany, Mantaly, Marovato Papango, Matsobe, Tanandava, Tsaratanana

---

## 7. Prochaines étapes de développement

- [ ] Écran Historique de l'association (timeline)
- [ ] Export PDF de la liste des membres
- [ ] Notifications locales (événements de l'association)
- [ ] QR code par membre
- [ ] Mode hors-ligne complet (déjà supporté)
# andapa
# cenad2
