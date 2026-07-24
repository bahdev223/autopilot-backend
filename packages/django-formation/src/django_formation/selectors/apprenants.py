from typing import Optional

from django.db.models import Q
from django_formation.models.apprenant import Apprenant


class ApprenantSelector:
    def apprenants_accessibles_par_utilisateur(self, user):
        return Apprenant.objects.filter(etablissement__membres__utilisateur=user, etablissement__membres__actif=True)

    def apprenants_par_etablissement(self, etablissement_id: str):
        return Apprenant.objects.filter(etablissement_id=etablissement_id)

    def rechercher_apprenants(self, etablissement_id: str, query: str = "", statut: Optional[str] = None):
        qs = Apprenant.objects.filter(etablissement_id=etablissement_id)
        if query:
            qs = qs.filter(Q(nom__icontains=query) | Q(prenom__icontains=query) | Q(matricule__icontains=query) | Q(email__icontains=query))
        if statut:
            qs = qs.filter(statut=statut)
        return qs.order_by("nom", "prenom")

    def detail_apprenant(self, apprenant_id: str):
        return Apprenant.objects.select_related("etablissement", "utilisateur").prefetch_related("inscriptions__session__formation").filter(pk=apprenant_id).first()

    def inscriptions_apprenant(self, apprenant):
        return apprenant.inscriptions.select_related("session", "session__formation").all()
