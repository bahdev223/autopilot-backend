# Permissions

- `PROPRIETAIRE` : gestion complète, y compris les membres.
- `ADMINISTRATEUR` : gestion de l’établissement et des données métier.
- `RESPONSABLE` : apprenants, formations et sessions, hors annulation critique.
- `AGENT_INSCRIPTION` : lecture du catalogue et gestion des inscriptions.
- `LECTEUR` : lecture seule.

Un identifiant d’établissement, session ou apprenant fourni dans une requête ne
donne jamais accès à une ressource hors des adhésions actives.
