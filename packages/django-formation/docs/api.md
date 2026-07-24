# API

L’API est montée avec `include("django_formation.urls")`. Toutes les routes
métier exigent une authentification.

Les listes sont paginées :

```json
{"count": 1, "next": null, "previous": null, "results": []}
```

Les erreurs métier utilisent :

```json
{"code": "SESSION_COMPLETE", "message": "La capacité est atteinte", "details": {}}
```

Les transitions de statut passent exclusivement par les actions dédiées
documentées dans le README.
