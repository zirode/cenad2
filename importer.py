# data/importer.py
# Import de données via fichier ZIP (CSV + photos) pour CENAD
# Version améliorée : compatibilité Android, sécurité, validation, rapport structuré

import zipfile
import csv
import os
import shutil
import logging
import io
import threading
import re

from kivy.app import App
from kivy.clock import Clock

from data import database as db

logger = logging.getLogger(__name__)

# Colonnes attendues dans chaque CSV
CSV_SCHEMAS = {
    'membres.csv':       ['id', 'nom', 'prenom', 'etablissement', 'niveau',
                          'commune', 'telephone', 'batiment', 'photo_filename'],
    'presidents.csv':    ['id', 'nom', 'prenom', 'annee_mandat',
                          'photo_filename', 'actions_marquantes'],
    'batiments.csv':     ['id', 'nom', 'description'],
    'etablissements.csv':['id', 'nom', 'mission'],
    'filieres.csv':      ['id', 'nom', 'etablissement_id'],
}

# Option : taille max du ZIP en octets (None = pas de limite)
MAX_ZIP_SIZE = None  # ex: 200 * 1024 * 1024  # 200 MB
# Taille max d'une photo copiée (en octets) — optionnel
MAX_PHOTO_SIZE = 10 * 1024 * 1024  # 10 MB


def get_photos_dir():
    """Retourne un dossier d'images en écriture dans user_data_dir (compatible Android)."""
    try:
        app = App.get_running_app()
        base = getattr(app, 'user_data_dir', None) or os.path.expanduser('~')
    except Exception:
        base = os.path.expanduser('~')
    photos = os.path.join(base, 'images')
    os.makedirs(photos, exist_ok=True)
    return photos


def safe_filename(name: str) -> str:
    """Sanitise un nom de fichier pour éviter path traversal et caractères dangereux."""
    name = os.path.basename(name or '')
    name = name.replace(' ', '_')
    safe = re.sub(r'[^A-Za-z0-9._-]', '', name)
    return safe[:200] if safe else 'file'


def import_zip_async(zip_path: str, on_done=None):
    """
    Lance import_zip dans un thread pour ne pas bloquer l'UI.
    on_done(rapport) sera appelé sur le thread UI via Clock.
    """
    def _worker():
        rapport = import_zip(zip_path)
        if on_done:
            Clock.schedule_once(lambda dt: on_done(rapport), 0)
    threading.Thread(target=_worker, daemon=True).start()


def import_zip(zip_path: str) -> dict:
    """
    Parse un fichier ZIP contenant des CSV + dossier photos/.
    Retourne un rapport structuré :
      {'succes': int, 'erreurs': [dict], 'ignores': int, 'photos_copiees': int}
    """
    rapport = {'succes': 0, 'erreurs': [], 'ignores': 0, 'photos_copiees': 0}

    if not zip_path or not os.path.exists(zip_path):
        rapport['erreurs'].append({'type': 'file', 'msg': f"Fichier introuvable : {zip_path}"})
        return rapport

    try:
        if MAX_ZIP_SIZE:
            size = os.path.getsize(zip_path)
            if size > MAX_ZIP_SIZE:
                rapport['erreurs'].append({'type': 'file', 'msg': f"ZIP trop volumineux ({size} bytes). Limite {MAX_ZIP_SIZE}."})
                return rapport

        with zipfile.ZipFile(zip_path, 'r') as zf:
            noms = zf.namelist()

            # 1) Copier les photos (vers user_data_dir/images)
            photos_copiees = _copier_photos(zf, noms, rapport)
            rapport['photos_copiees'] = photos_copiees
            rapport['succes'] += photos_copiees

            # 2) Importer chaque CSV (validation d'en-têtes)
            csv_tasks = [
                ('membres.csv',        _import_membres),
                ('presidents.csv',     _import_presidents),
                ('batiments.csv',      _import_batiments),
                ('etablissements.csv', _import_etablissements),
                ('filieres.csv',       _import_filieres),
            ]
            for csv_name, upsert_fn in csv_tasks:
                if csv_name in noms:
                    try:
                        with zf.open(csv_name) as f:
                            content = io.TextIOWrapper(f, encoding='utf-8-sig', errors='replace')
                            reader = csv.DictReader(content)
                            fieldnames = [fn.strip() for fn in (reader.fieldnames or [])]
                            expected = CSV_SCHEMAS.get(csv_name, [])
                            missing = [c for c in expected if c not in fieldnames]
                            content.seek(0)
                            if missing:
                                rapport['erreurs'].append({'type': 'csv', 'file': csv_name, 'msg': f'Colonnes manquantes: {missing}'})
                                continue
                            s, e, i = upsert_fn(content)
                            rapport['succes'] += s
                            for err in e:
                                if isinstance(err, dict):
                                    rapport['erreurs'].append(err)
                                else:
                                    rapport['erreurs'].append({'type': 'csv', 'file': csv_name, 'msg': str(err)})
                            rapport['ignores'] += i
                    except Exception as ex:
                        rapport['erreurs'].append({'type': 'csv', 'file': csv_name, 'msg': f'Erreur lecture: {ex}'})
                else:
                    logger.info(f"{csv_name} absent du ZIP, ignoré.")

    except zipfile.BadZipFile:
        rapport['erreurs'].append({'type': 'file', 'msg': "Le fichier n'est pas un ZIP valide."})
    except Exception as e:
        rapport['erreurs'].append({'type': 'exception', 'msg': f"Erreur générale import : {e}"})

    return rapport


def _copier_photos(zf: zipfile.ZipFile, noms: list, rapport: dict) -> int:
    """Copie les fichiers du dossier photos/ vers user_data_dir/images/ en sécurisant les noms."""
    photos_dir = get_photos_dir()
    count = 0
    for nom in noms:
        if nom.startswith('photos/') and not nom.endswith('/'):
            if '..' in nom or nom.startswith('/') or nom.startswith('\\'):
                rapport['erreurs'].append({'type': 'photo', 'file': nom, 'msg': 'Nom de fichier invalide (path traversal).'})
                continue
            filename = safe_filename(os.path.basename(nom))
            dest = os.path.join(photos_dir, filename)
            try:
                info = zf.getinfo(nom)
                if info.file_size and info.file_size > MAX_PHOTO_SIZE:
                    rapport['erreurs'].append({'type': 'photo', 'file': nom, 'msg': f"Photo trop grosse ({info.file_size} bytes), ignorée."})
                    continue
            except Exception:
                pass
            try:
                with zf.open(nom) as src, open(dest, 'wb') as dst:
                    shutil.copyfileobj(src, dst)
                count += 1
            except Exception as e:
                rapport['erreurs'].append({'type': 'photo', 'file': nom, 'msg': f'Erreur copie: {e}'})
    return count


# ---------- Fonctions d'import CSV (robustifiées) ----------
def _import_membres(f) -> tuple:
    succes, erreurs, ignores = 0, [], 0
    try:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 2):
            row = { (k.strip() if k else ''): (v.strip() if v else '') for k, v in row.items() }
            if not row.get('nom') or not row.get('prenom'):
                ignores += 1
                erreurs.append({'type': 'csv', 'file': 'membres.csv', 'line': i, 'msg': "nom ou prenom manquant, ligne ignorée."})
                continue
            try:
                ok = db.upsert_membre(row)
                if ok:
                    succes += 1
                else:
                    erreurs.append({'type': 'db', 'file': 'membres.csv', 'line': i, 'msg': 'échec insertion.'})
            except Exception as e:
                erreurs.append({'type': 'exception', 'file': 'membres.csv', 'line': i, 'msg': str(e)})
    except Exception as e:
        erreurs.append({'type': 'csv', 'file': 'membres.csv', 'msg': str(e)})
    return succes, erreurs, ignores


def _import_presidents(f) -> tuple:
    succes, erreurs, ignores = 0, [], 0
    try:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 2):
            row = { (k.strip() if k else ''): (v.strip() if v else '') for k, v in row.items() }
            if not row.get('nom'):
                ignores += 1
                erreurs.append({'type': 'csv', 'file': 'presidents.csv', 'line': i, 'msg': "nom manquant, ligne ignorée."})
                continue
            try:
                ok = db.upsert_president(row)
                if ok:
                    succes += 1
                else:
                    erreurs.append({'type': 'db', 'file': 'presidents.csv', 'line': i, 'msg': 'échec insertion.'})
            except Exception as e:
                erreurs.append({'type': 'exception', 'file': 'presidents.csv', 'line': i, 'msg': str(e)})
    except Exception as e:
        erreurs.append({'type': 'csv', 'file': 'presidents.csv', 'msg': str(e)})
    return succes, erreurs, ignores


def _import_batiments(f) -> tuple:
    succes, erreurs, ignores = 0, [], 0
    try:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 2):
            row = { (k.strip() if k else ''): (v.strip() if v else '') for k, v in row.items() }
            if not row.get('nom'):
                ignores += 1
                erreurs.append({'type': 'csv', 'file': 'batiments.csv', 'line': i, 'msg': "nom manquant, ligne ignorée."})
                continue
            try:
                ok = db.upsert_batiment(row)
                if ok:
                    succes += 1
                else:
                    erreurs.append({'type': 'db', 'file': 'batiments.csv', 'line': i, 'msg': 'échec insertion.'})
            except Exception as e:
                erreurs.append({'type': 'exception', 'file': 'batiments.csv', 'line': i, 'msg': str(e)})
    except Exception as e:
        erreurs.append({'type': 'csv', 'file': 'batiments.csv', 'msg': str(e)})
    return succes, erreurs, ignores


def _import_etablissements(f) -> tuple:
    succes, erreurs, ignores = 0, [], 0
    try:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 2):
            row = { (k.strip() if k else ''): (v.strip() if v else '') for k, v in row.items() }
            if not row.get('nom'):
                ignores += 1
                erreurs.append({'type': 'csv', 'file': 'etablissements.csv', 'line': i, 'msg': "nom manquant, ligne ignorée."})
                continue
            try:
                ok = db.upsert_etablissement(row)
                if ok:
                    succes += 1
                else:
                    erreurs.append({'type': 'db', 'file': 'etablissements.csv', 'line': i, 'msg': 'échec insertion.'})
            except Exception as e:
                erreurs.append({'type': 'exception', 'file': 'etablissements.csv', 'line': i, 'msg': str(e)})
    except Exception as e:
        erreurs.append({'type': 'csv', 'file': 'etablissements.csv', 'msg': str(e)})
    return succes, erreurs, ignores


def _import_filieres(f) -> tuple:
    succes, erreurs, ignores = 0, [], 0
    try:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 2):
            row = { (k.strip() if k else ''): (v.strip() if v else '') for k, v in row.items() }
            if not row.get('nom') or not row.get('etablissement_id'):
                ignores += 1
                erreurs.append({'type': 'csv', 'file': 'filieres.csv', 'line': i, 'msg': "nom ou etablissement_id manquant, ligne ignorée."})
                continue
            try:
                ok = db.upsert_filiere(row)
                if ok:
                    succes += 1
                else:
                    erreurs.append({'type': 'db', 'file': 'filieres.csv', 'line': i, 'msg': 'échec insertion.'})
            except Exception as e:
                erreurs.append({'type': 'exception', 'file': 'filieres.csv', 'line': i, 'msg': str(e)})
    except Exception as e:
        erreurs.append({'type': 'csv', 'file': 'filieres.csv', 'msg': str(e)})
    return succes, erreurs, ignores

