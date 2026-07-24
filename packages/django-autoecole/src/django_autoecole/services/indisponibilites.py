from django.db import transaction
from django_autoecole.models import IndisponibiliteMoniteur, IndisponibiliteVehicule
from django_autoecole.constants import StatutIndisponibilite
from django_autoecole import signals


@transaction.atomic
def annuler_indisponibilite_moniteur(indispo):
    IndisponibiliteMoniteur.objects.filter(pk=indispo.pk).select_for_update()
    indispo.refresh_from_db()
    indispo.statut = StatutIndisponibilite.ANNULEE
    indispo.save(update_fields=["statut", "updated_at"])
    signals.emit_on_commit(signals.indisponibilite_moniteur_annulee, annuler_indisponibilite_moniteur, indisponibilite=indispo)
    return indispo


@transaction.atomic
def annuler_indisponibilite_vehicule(indispo):
    IndisponibiliteVehicule.objects.filter(pk=indispo.pk).select_for_update()
    indispo.refresh_from_db()
    indispo.statut = StatutIndisponibilite.ANNULEE
    indispo.save(update_fields=["statut", "updated_at"])
    signals.emit_on_commit(signals.indisponibilite_vehicule_annulee, annuler_indisponibilite_vehicule, indisponibilite=indispo)
    return indispo
