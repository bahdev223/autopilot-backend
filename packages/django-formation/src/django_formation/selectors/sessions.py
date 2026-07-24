from typing import Any, Optional

from django_formation.models.session import SessionFormation


class SessionSelector:
    def sessions_accessibles_par_utilisateur(self, user):
        return SessionFormation.objects.filter(etablissement__membres__utilisateur=user, etablissement__membres__actif=True)

    def sessions_ouvertes(self, etablissement_id: Optional[str] = None):
        qs = SessionFormation.objects.filter(statut=SessionFormation.Statut.INSCRIPTIONS_OUVERTES)
        if etablissement_id:
            qs = qs.filter(etablissement_id=etablissement_id)
        return qs.order_by("date_debut")

    def sessions_en_cours(self, etablissement_id: Optional[str] = None):
        qs = SessionFormation.objects.filter(statut=SessionFormation.Statut.EN_COURS)
        if etablissement_id:
            qs = qs.filter(etablissement_id=etablissement_id)
        return qs.order_by("date_debut")

    def sessions_par_formation(self, formation_id: str):
        return SessionFormation.objects.filter(formation_id=formation_id).order_by("-date_debut")

    def detail_session(self, session_id: str):
        return SessionFormation.objects.select_related("etablissement", "formation").prefetch_related("inscriptions__apprenant").filter(pk=session_id).first()

    def inscrits_session(self, session_id: Any):
        from django_formation.models.inscription import Inscription
        return Inscription.objects.filter(session_id=session_id).select_related("apprenant").order_by("-date_inscription")

    def places_restantes_session(self, session_id: str) -> int:
        session = SessionFormation.objects.get(pk=session_id)
        return session.nombre_places_restantes
