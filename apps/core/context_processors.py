def autopilot_context(request):
    """Injecte l'établissement actif et les données de contexte global."""
    return {
        "etablissement_actif": getattr(request, "etablissement_actif", None),
        "membre_actif": getattr(request, "membre_actif", None),
    }
