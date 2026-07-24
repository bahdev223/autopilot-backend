# Architecture

Les modèles portent les données et contraintes locales. Les services
transactionnels réalisent les écritures et transitions. Les selectors
centralisent les lectures. Les vues orchestrent HTTP sans modifier directement
les statuts. Les signaux métier sont enregistrés avec `transaction.on_commit`.

Toutes les ressources API sont limitées aux adhésions actives de l’utilisateur.
