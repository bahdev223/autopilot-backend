from django_autoecole.models import LeconConduite, IndisponibiliteMoniteur, IndisponibiliteVehicule


def verifier_disponibilites(*, moniteur_id, vehicule_id=None, date_debut, date_fin,
                             statuts_bloquants=None):
    if statuts_bloquants is None:
        from ..constants import StatutLecon
        statuts_bloquants = [StatutLecon.PLANIFIEE, StatutLecon.CONFIRMEE, StatutLecon.EN_COURS]

    conflit_moniteur = LeconConduite.objects.filter(
        moniteur_id=moniteur_id,
        date_debut__lt=date_fin,
        date_fin__gt=date_debut,
        statut__in=statuts_bloquants,
    ).exists()

    if not conflit_moniteur:
        conflit_moniteur = IndisponibiliteMoniteur.objects.filter(
            moniteur_id=moniteur_id,
            date_debut__lt=date_fin,
            date_fin__gt=date_debut,
            statut="ACTIVE",
        ).exists()

    result = {"moniteur": conflit_moniteur}

    if vehicule_id:
        conflit_vehicule = LeconConduite.objects.filter(
            vehicule_id=vehicule_id,
            date_debut__lt=date_fin,
            date_fin__gt=date_debut,
            statut__in=statuts_bloquants,
        ).exists()

        if not conflit_vehicule:
            conflit_vehicule = IndisponibiliteVehicule.objects.filter(
                vehicule_id=vehicule_id,
                date_debut__lt=date_fin,
                date_fin__gt=date_debut,
                statut="ACTIVE",
            ).exists()

        result["vehicule"] = conflit_vehicule

    return result


def lister_lecons_dossier(dossier_id):
    return LeconConduite.objects.filter(dossier_id=dossier_id).select_related(
        "moniteur", "vehicule"
    ).order_by("-date_debut")


def lister_lecons_moniteur(moniteur_id, date_from=None, date_to=None):
    qs = LeconConduite.objects.filter(moniteur_id=moniteur_id)
    if date_from:
        qs = qs.filter(date_debut__gte=date_from)
    if date_to:
        qs = qs.filter(date_fin__lte=date_to)
    return qs.order_by("date_debut")


def lister_lecons_vehicule(vehicule_id, date_from=None, date_to=None):
    qs = LeconConduite.objects.filter(vehicule_id=vehicule_id)
    if date_from:
        qs = qs.filter(date_debut__gte=date_from)
    if date_to:
        qs = qs.filter(date_fin__lte=date_to)
    return qs.order_by("date_debut")
