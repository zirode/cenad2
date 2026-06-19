# data/database.py
# Gestion de la base de données SQLite pour l'application CENAD
# Version corrigée : chemin dynamique, check_same_thread=False, context managers, upserts robustes

import sqlite3
import os
import logging
from kivy.app import App

logger = logging.getLogger(__name__)

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.sql')
DB_FILENAME = 'cenad.db'


def get_db_path():
    """
    Retourne le chemin absolu de la base de données dans user_data_dir si possible,
    sinon dans le home de l'utilisateur.
    """
    try:
        app = App.get_running_app()
        base = getattr(app, 'user_data_dir', None) or os.path.expanduser('~')
    except Exception:
        base = os.path.expanduser('~')
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, DB_FILENAME)


def get_connection():
    """
    Retourne une connexion SQLite configurée pour usage multi-thread.
    Utilise check_same_thread=False pour permettre l'accès depuis des threads.
    Chaque appel crée une nouvelle connexion (recommandé).
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_database():
    """
    Initialise la base de données en exécutant le schéma SQL.
    Crée le dossier contenant la DB si nécessaire.
    """
    db_path = get_db_path()
    db_dir = os.path.dirname(db_path)
    os.makedirs(db_dir, exist_ok=True)

    if not os.path.exists(SCHEMA_PATH):
        logger.error(f"Fichier de schéma introuvable: {SCHEMA_PATH}")
        raise FileNotFoundError(f"Schema SQL introuvable: {SCHEMA_PATH}")

    try:
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            schema = f.read()
        conn = get_connection()
        with conn:
            conn.executescript(schema)
        conn.close()
        logger.info("Base de données initialisée avec succès.")
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation de la base : {e}")
        raise


def reset_database():
    """
    Réinitialise complètement la base (supprime les données des tables listées).
    Ne supprime pas le fichier DB.
    """
    try:
        conn = get_connection()
        with conn:
            tables = ['membres', 'presidents', 'batiments', 'etablissements',
                      'filieres', 'historique', 'app_meta', 'communes']
            for table in tables:
                conn.execute(f"DELETE FROM {table}")
        conn.close()
        logger.info("Base de données réinitialisée.")
        return True
    except Exception as e:
        logger.error(f"Erreur reset : {e}")
        return False


# -------------------------
# MEMBRES
# -------------------------
def get_all_membres(search=None, etablissement=None, commune=None, niveau=None):
    query = "SELECT * FROM membres WHERE 1=1"
    params = []
    if search:
        query += " AND (nom LIKE ? OR prenom LIKE ?)"
        params += [f'%{search}%', f'%{search}%']
    if etablissement:
        query += " AND etablissement = ?"
        params.append(etablissement)
    if commune:
        query += " AND commune = ?"
        params.append(commune)
    if niveau:
        query += " AND niveau LIKE ?"
        params.append(f'%{niveau}%')
    query += " ORDER BY nom, prenom"
    conn = get_connection()
    try:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_membre_by_id(membre_id):
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM membres WHERE id=?", (membre_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def upsert_membre(data: dict):
    """
    Insère ou met à jour un membre.
    Contrainte d'unicité attendue sur (nom, prenom, telephone) dans le schéma.
    """
    conn = get_connection()
    try:
        with conn:
            conn.execute("""
                INSERT INTO membres (nom, prenom, etablissement, niveau, commune,
                                     telephone, batiment, photo_filename)
                VALUES (:nom, :prenom, :etablissement, :niveau, :commune,
                        :telephone, :batiment, :photo_filename)
                ON CONFLICT(nom, prenom, telephone) DO UPDATE SET
                    etablissement  = excluded.etablissement,
                    niveau         = excluded.niveau,
                    commune        = excluded.commune,
                    batiment       = excluded.batiment,
                    photo_filename = excluded.photo_filename
            """, data)
        return True
    except Exception as e:
        logger.error(f"Erreur upsert_membre : {e}")
        return False
    finally:
        conn.close()


# -------------------------
# PRÉSIDENTS
# -------------------------
def get_all_presidents():
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM presidents ORDER BY annee_mandat DESC").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def upsert_president(data: dict):
    """
    Insère un président. On ignore si conflit sur (nom, prenom, annee_mandat).
    Assure que la contrainte UNIQUE existe dans le schéma.
    """
    conn = get_connection()
    try:
        with conn:
            conn.execute("""
                INSERT OR IGNORE INTO presidents (nom, prenom, annee_mandat, photo_filename, actions_marquantes)
                VALUES (:nom, :prenom, :annee_mandat, :photo_filename, :actions_marquantes)
            """, data)
        return True
    except Exception as e:
        logger.error(f"Erreur upsert_president : {e}")
        return False
    finally:
        conn.close()


# -------------------------
# BÂTIMENTS
# -------------------------
def get_all_batiments():
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM batiments ORDER BY nom").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def upsert_batiment(data: dict):
    conn = get_connection()
    try:
        with conn:
            conn.execute("""
                INSERT INTO batiments (nom, description)
                VALUES (:nom, :description)
                ON CONFLICT(nom) DO UPDATE SET description = excluded.description
            """, data)
        return True
    except Exception as e:
        logger.error(f"Erreur upsert_batiment : {e}")
        return False
    finally:
        conn.close()


# -------------------------
# ÉTABLISSEMENTS & FILIÈRES
# -------------------------
def get_all_etablissements():
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM etablissements ORDER BY nom").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_filieres_by_etablissement(etablissement_id):
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM filieres WHERE etablissement_id=? ORDER BY nom",
            (etablissement_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def upsert_etablissement(data: dict):
    conn = get_connection()
    try:
        with conn:
            conn.execute("""
                INSERT INTO etablissements (nom, mission)
                VALUES (:nom, :mission)
                ON CONFLICT(nom) DO UPDATE SET mission = excluded.mission
            """, data)
        return True
    except Exception as e:
        logger.error(f"Erreur upsert_etablissement : {e}")
        return False
    finally:
        conn.close()


def upsert_filiere(data: dict):
    conn = get_connection()
    try:
        with conn:
            conn.execute("""
                INSERT OR IGNORE INTO filieres (nom, etablissement_id)
                VALUES (:nom, :etablissement_id)
            """, data)
        return True
    except Exception as e:
        logger.error(f"Erreur upsert_filiere : {e}")
        return False
    finally:
        conn.close()


# -------------------------
# PARAMÈTRES APP
# -------------------------
def get_setting(key, default=None):
    conn = get_connection()
    try:
        row = conn.execute("SELECT valeur FROM app_meta WHERE cle=?", (key,)).fetchone()
        return row['valeur'] if row else default
    finally:
        conn.close()


def set_setting(key, value):
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                "INSERT INTO app_meta (cle, valeur) VALUES (?,?) "
                "ON CONFLICT(cle) DO UPDATE SET valeur=excluded.valeur",
                (key, value)
            )
    finally:
        conn.close()


def get_communes():
    conn = get_connection()
    try:
        rows = conn.execute("SELECT nom FROM communes ORDER BY nom").fetchall()
        return [r['nom'] for r in rows]
    finally:
        conn.close()

