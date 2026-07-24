# Architecture

Le package étend `django-formation`. Chaque dossier référence une inscription.
Les écritures passent par des services transactionnels et l’API isole les
ressources selon les adhésions actives.
