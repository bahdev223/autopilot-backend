from django.db import transaction
from django_autoecole.models import Vehicule
from django_autoecole.constants import StatutVehicule
from django_autoecole.exceptions import (
    AutoEcoleDomainError,
    CrossEstablishmentOperationError,
    InvalidMileageError,
)
from django_autoecole import signals


@transaction.atomic
def creer_vehicule(*, etablissement, categorie_permis_id, immatriculation, marque,
                    modele, annee=None, couleur="", type_boite="MANUELLE",
                    type_carburant="", kilometrage=0, cree_par=None):
    from django_autoecole.models import CategoriePermis
    cat = CategoriePermis.objects.get(id=categorie_permis_id)
    if cat.etablissement_id != etablissement.id:
        raise CrossEstablishmentOperationError(
            "La catégorie de permis n'appartient pas au même établissement"
        )
    vehicule = Vehicule.objects.create(
        etablissement=etablissement,
        categorie_permis=cat,
        immatriculation=immatriculation,
        marque=marque,
        modele=modele,
        annee=annee,
        couleur=couleur,
        type_boite=type_boite,
        type_carburant=type_carburant,
        kilometrage_actuel=kilometrage,
        statut=StatutVehicule.DISPONIBLE,
    )
    signals.emit_on_commit(signals.vehicule_cree, creer_vehicule, vehicule=vehicule, cree_par=cree_par)
    return vehicule


def _lock_vehicule(vehicule):
    Vehicule.objects.filter(pk=vehicule.pk).select_for_update()
    vehicule.refresh_from_db()


@transaction.atomic
def modifier_vehicule(vehicule, **data):
    _lock_vehicule(vehicule)
    for field in ("marque", "modele", "annee", "couleur", "type_boite", "type_carburant", "observation"):
        if field in data:
            setattr(vehicule, field, data[field])
    vehicule.save(update_fields=list(data.keys()) + ["updated_at"])
    signals.emit_on_commit(signals.vehicule_modifie, modifier_vehicule, vehicule=vehicule)
    return vehicule


@transaction.atomic
def reserver_vehicule(vehicule):
    _lock_vehicule(vehicule)
    if vehicule.statut != StatutVehicule.DISPONIBLE:
        raise AutoEcoleDomainError("Seul un véhicule disponible peut être réservé")
    vehicule.statut = StatutVehicule.RESERVE
    vehicule.save(update_fields=["statut", "updated_at"])
    signals.emit_on_commit(signals.vehicule_reserve, reserver_vehicule, vehicule=vehicule)
    return vehicule


@transaction.atomic
def liberer_vehicule(vehicule):
    _lock_vehicule(vehicule)
    vehicule.statut = StatutVehicule.DISPONIBLE
    vehicule.save(update_fields=["statut", "updated_at"])
    signals.emit_on_commit(signals.vehicule_liberer, liberer_vehicule, vehicule=vehicule)
    return vehicule


@transaction.atomic
def mettre_vehicule_en_entretien(vehicule):
    _lock_vehicule(vehicule)
    vehicule.statut = StatutVehicule.ENTRETIEN
    vehicule.save(update_fields=["statut", "updated_at"])
    signals.emit_on_commit(signals.vehicule_en_entretien, mettre_vehicule_en_entretien, vehicule=vehicule)
    return vehicule


@transaction.atomic
def declarer_vehicule_en_panne(vehicule):
    _lock_vehicule(vehicule)
    vehicule.statut = StatutVehicule.PANNE
    vehicule.save(update_fields=["statut", "updated_at"])
    signals.emit_on_commit(signals.vehicule_en_panne, declarer_vehicule_en_panne, vehicule=vehicule)
    return vehicule


@transaction.atomic
def remettre_vehicule_disponible(vehicule):
    _lock_vehicule(vehicule)
    vehicule.statut = StatutVehicule.DISPONIBLE
    vehicule.save(update_fields=["statut", "updated_at"])
    signals.emit_on_commit(signals.vehicule_disponible, remettre_vehicule_disponible, vehicule=vehicule)
    return vehicule


@transaction.atomic
def mettre_vehicule_hors_service(vehicule):
    _lock_vehicule(vehicule)
    vehicule.statut = StatutVehicule.HORS_SERVICE
    vehicule.save(update_fields=["statut", "updated_at"])
    signals.emit_on_commit(signals.vehicule_hors_service, mettre_vehicule_hors_service, vehicule=vehicule)
    return vehicule


@transaction.atomic
def archiver_vehicule(vehicule):
    _lock_vehicule(vehicule)
    if vehicule.lecons.filter(statut__in=["EN_COURS", "CONFIRMEE"]).exists():
        raise AutoEcoleDomainError("Impossible d'archiver un véhicule avec des leçons en cours")
    vehicule.statut = StatutVehicule.ARCHIVE
    vehicule.save(update_fields=["statut", "updated_at"])
    signals.emit_on_commit(signals.vehicule_archive, archiver_vehicule, vehicule=vehicule)
    return vehicule


@transaction.atomic
def mettre_a_jour_kilometrage(vehicule, nouveau_kilometrage):
    _lock_vehicule(vehicule)
    if nouveau_kilometrage < vehicule.kilometrage_actuel:
        raise InvalidMileageError("Le kilométrage ne peut pas diminuer")
    vehicule.kilometrage_actuel = nouveau_kilometrage
    vehicule.save(update_fields=["kilometrage_actuel", "updated_at"])
    signals.emit_on_commit(signals.vehicule_kilometrage_mis_a_jour, mettre_a_jour_kilometrage, vehicule=vehicule)
    return vehicule
