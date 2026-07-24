from django_formation.models.membre import MembreEtablissement


class EtablissementActifMiddleware:
    """Définit request.etablissement_actif avant les vues."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        etab = None
        if request.user.is_authenticated:
            membre = MembreEtablissement.objects.filter(
                utilisateur=request.user, actif=True,
            ).select_related("etablissement").first()
            if membre:
                etab = membre.etablissement
                request.membre_actif = membre
        request.etablissement_actif = etab
        return self.get_response(request)
