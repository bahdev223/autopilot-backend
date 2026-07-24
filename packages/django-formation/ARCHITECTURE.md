# Architecture

## Layers

- `domain/` — Business logic (value objects, events, exceptions, validators)
- `models/` — Django ORM models (7 models)
- `services/` — Application services (wrapped in `@transaction.atomic`)
- `selectors/` — Read-side queries
- `api/` — REST API (views, serializers, permissions, urls)
- `admin/` — Django Admin
- `signals/` — Event-driven signals

## Status Machines

- **Apprenant**: ACTIF → INACTIF → ARCHIVE
- **Formation**: BROUILLON → PUBLIEE → SUSPENDUE → ARCHIVEE
- **Session**: BROUILLON → INSCRIPTIONS_OUVERTES → FERMEES → EN_COURS → TERMINEE/ANNULEE
- **Inscription**: PREINSCRITE → EN_ATTENTE → CONFIRMEE → EN_COURS → TERMINEE/ABANDONNEE/ANNULEE

## Multi-establishment

All models are scoped to an `Etablissement`. Querysets are filtered by user membership.
