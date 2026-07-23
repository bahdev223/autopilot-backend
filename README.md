# AutoPilot

La plateforme complète de gestion des auto-écoles.

## Architecture

```
autopilot/
├── config/              # Django project configuration
│   ├── settings/        # base.py, dev.py, prod.py
│   ├── urls.py
│   └── wsgi.py
├── apps/                # Custom applications
├── packages/            # Local packages (pip install -e)
│   ├── django-formation/
│   └── django-autoecole/
├── templates/
├── static/
├── media/
├── requirements/
├── manage.py
└── docker-compose.yml
```

## Moteurs techniques

- **[django-formation](https://github.com/bahdev223/django-formation)** — Gestion générique des formations
- **[django-autoecole](https://github.com/bahdev223/django-autoecole)** — Métier auto-école (candidats, examens, véhicules, moniteurs)

## Installation

```bash
# Cloner le projet
git clone https://github.com/bahdev223/autopilot-backend.git
cd autopilot-backend

# Environnement virtuel
python -m venv .venv
source .venv/bin/activate  # ou .venv\Scripts\activate sous Windows

# Installer les dépendances
pip install -r requirements/dev.txt

# Copier et configurer .env
cp .env.example .env
# Éditer .env avec vos paramètres

# Migrations
python manage.py migrate

# Démarrage
python manage.py runserver
```

## Prérequis

- Python ≥ 3.11
- Django ≥ 5.2
- PostgreSQL ≥ 16
- Node.js 20+ (pour le frontend si présent)

## Licence

MIT
