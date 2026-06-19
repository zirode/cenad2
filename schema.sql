-- ============================================================
-- Schéma SQLite - Application CENAD
-- ============================================================

-- Table des membres
CREATE TABLE IF NOT EXISTS membres (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nom             TEXT NOT NULL,
    prenom          TEXT NOT NULL,
    etablissement   TEXT,
    niveau          TEXT,
    commune         TEXT,
    telephone       TEXT,
    batiment        TEXT,
    photo_filename  TEXT,
    date_ajout      TEXT DEFAULT (datetime('now')),
    UNIQUE(nom, prenom, telephone)
);

-- Table des présidents
CREATE TABLE IF NOT EXISTS presidents (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    nom                 TEXT NOT NULL,
    prenom              TEXT NOT NULL,
    annee_mandat        TEXT NOT NULL,
    photo_filename      TEXT,
    actions_marquantes  TEXT,
    date_ajout          TEXT DEFAULT (datetime('now')),
    UNIQUE(nom, prenom, annee_mandat)
);

-- Table des bâtiments
CREATE TABLE IF NOT EXISTS batiments (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nom         TEXT NOT NULL UNIQUE,
    description TEXT
);

-- Table des établissements
CREATE TABLE IF NOT EXISTS etablissements (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    nom     TEXT NOT NULL UNIQUE,
    mission TEXT
);

-- Table des filières
CREATE TABLE IF NOT EXISTS filieres (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    nom              TEXT NOT NULL,
    etablissement_id INTEGER NOT NULL,
    FOREIGN KEY (etablissement_id) REFERENCES etablissements(id) ON DELETE CASCADE,
    UNIQUE(nom, etablissement_id)
);

-- Table de l'historique
CREATE TABLE IF NOT EXISTS historique (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    annee          TEXT,
    titre          TEXT NOT NULL,
    description    TEXT,
    photo_filename TEXT
);

-- Table des communes
CREATE TABLE IF NOT EXISTS communes (
    id  INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL UNIQUE
);

-- Données initiales — Communes d'Andapa (22 communes, sans doublons)
INSERT OR IGNORE INTO communes (nom) VALUES
    ('Andapa'),('Antsahamena'),('Ambalamanasy II'),('Ambodiangezoka'),
    ('Ambodimanga'),('Ambodidivaina'),('Matsohely'),
    ('Andasibe'),('Andrakata'),('Anjialavabe'),
    ('Ambalavelona'),('Bealampona'),('Belaoko Marovato'),
    ('Andranomena'),('Doany'),('Anoviara'),('Marovato'),
    ('Matsobe'),('Tanandava'),('B Andranotsara');

-- Table des métadonnées
CREATE TABLE IF NOT EXISTS app_meta (
    cle     TEXT PRIMARY KEY,
    valeur  TEXT
);

INSERT OR IGNORE INTO app_meta (cle, valeur) VALUES
    ('version', '1.0.0'),
    ('theme', 'dark'),
    ('assets_path', 'assets/'),
    ('derniere_mise_a_jour', datetime('now'));

