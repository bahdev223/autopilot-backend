# django-autoecole
Extension auto-école pour django-formation.

## Installation

```bash
pip install django-autoecole
```

```python
INSTALLED_APPS = [
    ...
    "django_formation",
    "django_autoecole",
]
```

## Configuration

```python
DJANGO_AUTOECOLE = {
    "DEFAULT_TIMEZONE": "Africa/Bamako",
    "DEFAULT_LESSON_DURATION_MINUTES": 60,
    "MAX_EVALUATION_SCORE": 20,
    "CHECK_VEHICLE_DOCUMENT_EXPIRY": True,
    "DOSSIER_NUMBER_PREFIX": "AE",
    "INSTRUCTOR_NUMBER_PREFIX": "MON",
}
```

## Modèles

| Modèle | Description |
|---|---|
| `CategoriePermis` | A, B, C, D, E… |
| `Moniteur` | Instructeur de conduite |
| `Vehicule` | Véhicule d'apprentissage |
| `DossierAutoEcole` | Dossier candidat (central) |
| `LeconConduite` | Séance de conduite |
| `EvaluationLecon` | Évaluation d'une leçon |
| `ExamenAutoEcole` | Examen code/conduite |
| `IndisponibiliteMoniteur` | Planning moniteur |
| `IndisponibiliteVehicule` | Planning véhicule |
| `HistoriqueStatutDossier` | Audit des transitions |

## Licence

MIT
