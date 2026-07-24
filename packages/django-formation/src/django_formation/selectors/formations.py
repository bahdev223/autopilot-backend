from typing import Optional

from django_formation.models.formation import Formation


class FormationSelector:
    def formations_accessibles_par_utilisateur(self, user):
        return Formation.objects.filter(etablissement__membres__utilisateur=user, etablissement__membres__actif=True)

    def formations_publiees(self, etablissement_id: Optional[str] = None):
        qs = Formation.objects.filter(statut=Formation.Statut.PUBLIEE)
        if etablissement_id:
            qs = qs.filter(etablissement_id=etablissement_id)
        return qs.order_by("nom")

    def formations_par_etablissement(self, etablissement_id: str):
        return Formation.objects.filter(etablissement_id=etablissement_id).order_by("nom")

    def detail_formation(self, formation_id: str):
        return Formation.objects.select_related("etablissement").prefetch_related("sessions").filter(pk=formation_id).first()

    def sessions_formation(self, formation_id: str):
        from django_formation.models.session import SessionFormation
        return SessionFormation.objects.filter(formation_id=formation_id).order_by("-date_debut")
