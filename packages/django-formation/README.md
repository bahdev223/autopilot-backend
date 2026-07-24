# django-formation

Universal training center management engine for Django.

Manages establishments, learners, training programs, sessions, and enrollments with full lifecycle management, role-based permissions, and multi-establishment isolation.

## Requirements

- Python ≥ 3.11
- Django ≥ 5.2, < 6.1
- DRF ≥ 3.15
- PostgreSQL ≥ 16 (SQLite OK for dev/testing)
- django-filter ≥ 24

## Installation

```bash
pip install django-formation
```

## Quick Start

```python
# settings.py
INSTALLED_APPS = [
    ...
    "rest_framework",
    "django_filters",
    "django_formation",
]

REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": "django_formation.api.exceptions.formation_exception_handler",
}

# urls.py
urlpatterns = [
    path("api/v1/formation/", include("django_formation.urls")),
]
```

```bash
python manage.py migrate
```

## Architecture

```
src/django_formation/
├── domain/              # Business logic
│   ├── value_objects/   # Status machines with transition rules
│   ├── events/          # Domain events
│   ├── exceptions/      # Domain exceptions with error codes
│   ├── validators/      # Business validators
│   └── services/        # Domain services
├── models/              # Django ORM models (7 models)
├── services/            # Application services (@transaction.atomic)
├── selectors/           # Read-side queries
├── api/                 # REST API
│   ├── views.py         # 40+ endpoints
│   ├── serializers.py   # Create/Update/Read serializers
│   ├── permissions.py   # Role-based permissions
│   ├── exceptions.py    # Central error handler
│   └── urls.py
├── admin.py             # Django Admin with readonly statuses + actions
├── signals/             # 15 business signals
└── migrations/
```

## Models

| Model | Description | Status Machine |
|-------|-------------|---------------|
| `Etablissement` | Training center | active/inactive |
| `MembreEtablissement` | User membership + role | active/inactive |
| `Apprenant` | Learner | ACTIF → INACTIF → ARCHIVE |
| `Formation` | Training program | BROUILLON → PUBLIEE → SUSPENDUE → ARCHIVEE |
| `SessionFormation` | Session of a training | BROUILLON → INSCRIPTIONS_OUVERTES → FERMEES → EN_COURS → TERMINEE/ANNULEE |
| `Inscription` | Enrollment | PREINSCRITE → EN_ATTENTE → CONFIRMEE → EN_COURS → TERMINEE/ABANDONNEE/ANNULEE |
| `HistoriqueStatutInscription` | Status change history | — |

## Roles & Permissions

| Role | Learners | Formations | Sessions | Enrollments | Members |
|------|----------|------------|----------|-------------|---------|
| PROPRIETAIRE | CRUD | CRUD | CRUD | CRUD | CRUD |
| ADMINISTRATEUR | CRUD | CRUD | CRUD | CRUD | Read |
| RESPONSABLE | CRUD | CRUD | CRUD (no cancel) | Read | — |
| AGENT_INSCRIPTION | Create/Read | Read | Read | Manage | — |
| LECTEUR | Read | Read | Read | Read | — |

## API Endpoints

### Establishments
- `GET/POST /etablissements/` — List/create
- `GET/PATCH /etablissements/<uuid:pk>/` — Detail/update
- `POST /etablissements/<uuid:pk>/activer/` — Activate
- `POST /etablissements/<uuid:pk>/desactiver/` — Deactivate

### Members
- `GET/POST /etablissements/<uuid:pk>/membres/` — List/add
- `PATCH/DELETE /membres/<uuid:pk>/` — Update/remove

### Learners
- `GET/POST /apprenants/` — List/create
- `GET/PATCH /apprenants/<uuid:pk>/` — Detail/update
- `POST /apprenants/<uuid:pk>/activer/` — Activate
- `POST /apprenants/<uuid:pk>/desactiver/` — Deactivate
- `POST /apprenants/<uuid:pk>/archiver/` — Archive
- `GET /apprenants/<uuid:pk>/inscriptions/` — Learner's enrollments

### Formations
- `GET/POST /formations/` — List/create
- `GET/PATCH /formations/<uuid:pk>/` — Detail/update
- `POST /formations/<uuid:pk>/publier/` — Publish
- `POST /formations/<uuid:pk>/suspendre/` — Suspend
- `POST /formations/<uuid:pk>/reactiver/` — Reactivate
- `POST /formations/<uuid:pk>/archiver/` — Archive
- `GET /formations/<uuid:pk>/sessions/` — Sessions for a training

### Sessions
- `GET/POST /sessions/` — List/create
- `GET/PATCH /sessions/<uuid:pk>/` — Detail/update
- `POST /sessions/<uuid:pk>/ouvrir-inscriptions/` — Open enrollments
- `POST /sessions/<uuid:pk>/fermer-inscriptions/` — Close enrollments
- `POST /sessions/<uuid:pk>/demarrer/` — Start session
- `POST /sessions/<uuid:pk>/terminer/` — End session
- `POST /sessions/<uuid:pk>/annuler/` — Cancel session
- `GET /sessions/<uuid:pk>/inscriptions/` — Enrollments for a session
- `GET /sessions/<uuid:pk>/statistiques/` — Session stats

### Enrollments
- `GET/POST /inscriptions/` — List/pre-enroll
- `GET /inscriptions/<uuid:pk>/` — Detail
- `POST /inscriptions/<uuid:pk>/mettre-en-attente/` — Put on hold
- `POST /inscriptions/<uuid:pk>/confirmer/` — Confirm
- `POST /inscriptions/<uuid:pk>/refuser/` — Reject
- `POST /inscriptions/<uuid:pk>/annuler/` — Cancel
- `POST /inscriptions/<uuid:pk>/demarrer/` — Start
- `POST /inscriptions/<uuid:pk>/abandonner/` — Drop out
- `POST /inscriptions/<uuid:pk>/terminer/` — Complete
- `GET /inscriptions/<uuid:pk>/historique/` — Status history

## Multi-establishment Isolation

All objects are scoped to an `Etablissement`. API views filter by the authenticated user's establishment membership. A user from establishment A cannot read or modify objects from establishment B. Role-based permissions further restrict actions within the same establishment.

## Error Format

All domain errors return:
```json
{
  "code": "TRANSACTION_INVALIDE",
  "message": "Transition invalide de 'CONFIRMEE' vers 'TERMINEE'",
  "details": {}
}
```

## Status Machines

### Inscription transitions
```
PREINSCRITE → EN_ATTENTE → CONFIRMEE → EN_COURS → TERMINEE
           ↘            ↘         ↘           ↘
             REFUSEE    REFUSEE   ANNULEE      ABANDONNEE
           ↘
             ANNULEE
```

### Session transitions
```
BROUILLON → INSCRIPTIONS_OUVERTES → FERMEES → EN_COURS → TERMINEE
         ↘                       ↘           ↘          ↘
           ANNULEE                EN_COURS    EN_COURS   ANNULEE
                                ↘           ↘
                                  ANNULEE    ANNULEE
```

## License

MIT
