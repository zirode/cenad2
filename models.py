# data/models.py
# Modèles de données simples (dataclasses) pour l'application CENAD

from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class Membre:
    id: Optional[int] = None
    nom: str = ""
    prenom: str = ""
    etablissement: str = ""
    niveau: str = ""
    commune: str = ""
    telephone: str = ""
    batiment: str = ""
    photo_filename: str = ""

    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}"

    @classmethod
    def from_dict(cls, d: dict):
        return cls(
            id=d.get('id'),
            nom=d.get('nom', ''),
            prenom=d.get('prenom', ''),
            etablissement=d.get('etablissement', ''),
            niveau=d.get('niveau', ''),
            commune=d.get('commune', ''),
            telephone=d.get('telephone', ''),
            batiment=d.get('batiment', ''),
            photo_filename=d.get('photo_filename', ''),
        )


@dataclass
class President:
    id: Optional[int] = None
    nom: str = ""
    prenom: str = ""
    annee_mandat: str = ""
    photo_filename: str = ""
    actions_marquantes: str = ""

    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}"

    @classmethod
    def from_dict(cls, d: dict):
        return cls(
            id=d.get('id'),
            nom=d.get('nom', ''),
            prenom=d.get('prenom', ''),
            annee_mandat=d.get('annee_mandat', ''),
            photo_filename=d.get('photo_filename', ''),
            actions_marquantes=d.get('actions_marquantes', ''),
        )


@dataclass
class Batiment:
    id: Optional[int] = None
    nom: str = ""
    description: str = ""

    @classmethod
    def from_dict(cls, d: dict):
        return cls(
            id=d.get('id'),
            nom=d.get('nom', ''),
            description=d.get('description', '')
        )


@dataclass
class Etablissement:
    id: Optional[int] = None
    nom: str = ""
    mission: str = ""
    filieres: List['Filiere'] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict):
        return cls(
            id=d.get('id'),
            nom=d.get('nom', ''),
            mission=d.get('mission', '')
        )


@dataclass
class Filiere:
    id: Optional[int] = None
    nom: str = ""
    etablissement_id: Optional[int] = None

    @classmethod
    def from_dict(cls, d: dict):
        return cls(
            id=d.get('id'),
            nom=d.get('nom', ''),
            etablissement_id=d.get('etablissement_id')
        )


@dataclass
class Historique:
    id: Optional[int] = None
    annee: str = ""
    titre: str = ""
    description: str = ""
    photo_filename: str = ""

    @classmethod
    def from_dict(cls, d: dict):
        return cls(
            id=d.get('id'),
            annee=d.get('annee', ''),
            titre=d.get('titre', ''),
            description=d.get('description', ''),
            photo_filename=d.get('photo_filename', '')
        )


@dataclass
class Commune:
    id: Optional[int] = None
    nom: str = ""

    @classmethod
    def from_dict(cls, d: dict):
        return cls(
            id=d.get('id'),
            nom=d.get('nom', '')
        )


@dataclass
class AppMeta:
    cle: str = ""
    valeur: str = ""

    @classmethod
    def from_dict(cls, d: dict):
        return cls(
            cle=d.get('cle', ''),
            valeur=d.get('valeur', '')
        )

