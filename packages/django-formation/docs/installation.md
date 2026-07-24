# Installation

Le package exige Python 3.12+, Django 5.2+ et Django REST Framework 3.15+.

```bash
pip install django-formation
python manage.py migrate
```

Ajoutez `rest_framework`, `django_filters` et `django_formation` à
`INSTALLED_APPS`, puis incluez `django_formation.urls` sous le préfixe souhaité.
