# Configuration

```python
DJANGO_FORMATION = {
    "DEFAULT_COUNTRY": "Mali",
    "DEFAULT_CURRENCY": "XOF",
    "LEARNER_NUMBER_PREFIX": "APP",
    "ENROLLMENT_NUMBER_PREFIX": "INS",
    "LEARNER_NUMBER_GENERATOR": "mon_projet.numerotation.matricule",
    "ENROLLMENT_NUMBER_GENERATOR": "mon_projet.numerotation.inscription",
    "ALLOW_LEARNER_USER_LINK": True,
    "ENABLE_API": True,
}
```

Une fonction de numérotation reçoit les arguments nommés `queryset` et `prefix`
et retourne une chaîne unique. La stratégie par défaut produit
`PREFIX-ANNEE-SEQUENCE`.
