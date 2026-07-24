from django.db import transaction
from django_autoecole.models import CategoriePermis
from django_autoecole import signals


@transaction.atomic
def activer_categorie_permis(categorie):
    CategoriePermis.objects.filter(pk=categorie.pk).select_for_update()
    categorie.refresh_from_db()
    categorie.actif = True
    categorie.save(update_fields=["actif"])
    signals.emit_on_commit(signals.categorie_permis_activee, activer_categorie_permis, categorie=categorie)
    return categorie


@transaction.atomic
def desactiver_categorie_permis(categorie):
    CategoriePermis.objects.filter(pk=categorie.pk).select_for_update()
    categorie.refresh_from_db()
    categorie.actif = False
    categorie.save(update_fields=["actif"])
    signals.emit_on_commit(signals.categorie_permis_desactivee, desactiver_categorie_permis, categorie=categorie)
    return categorie
