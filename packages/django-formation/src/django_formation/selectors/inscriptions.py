from typing import Any

from django_formation.models.inscription import Inscription
from django_formation.models.historique import HistoriqueStatutInscription


class InscriptionSelector:
    def inscriptions_accessibles_par_utilisateur(self, user):
        return Inscription.objects.filter(etablissement__membres__utilisateur=user, etablissement__membres__actif=True)

    def inscriptions_par_session(self, session_id: Any):
        return Inscription.objects.filter(session_id=session_id).select_related("apprenant").order_by("-date_inscription")

    def inscriptions_par_apprenant(self, apprenant_id: str):
        return Inscription.objects.filter(apprenant_id=apprenant_id).select_related("session", "session__formation").order_by("-date_inscription")

    def inscriptions_par_statut(self, etablissement_id: str, statut: str):
        return Inscription.objects.filter(etablissement_id=etablissement_id, statut=statut).select_related("apprenant", "session").order_by("-date_inscription")

    def detail_inscription(self, inscription_id: str):
        return Inscription.objects.select_related("apprenant", "session", "session__formation", "etablissement").filter(pk=inscription_id).first()

    def historique_inscription(self, inscription_id: str):
        return HistoriqueStatutInscription.objects.filter(inscription_id=inscription_id).order_by("created_at")
