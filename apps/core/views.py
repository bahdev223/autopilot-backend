from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django_formation.models.etablissement import Etablissement
from django_formation.models.apprenant import Apprenant
from django_formation.models.formation import Formation
from django_formation.models.session import SessionFormation
from django_formation.models.inscription import Inscription


@login_required
def dashboard(request):
    etablissements = Etablissement.objects.filter(membres__utilisateur=request.user, membres__actif=True)
    etab = etablissements.first()
    context = {
        "etablissements": etablissements,
        "total_apprenants": Apprenant.objects.filter(etablissement=etab).count() if etab else 0,
        "total_formations": Formation.objects.filter(etablissement=etab).count() if etab else 0,
        "total_sessions": SessionFormation.objects.filter(etablissement=etab).count() if etab else 0,
        "total_inscriptions": Inscription.objects.filter(etablissement=etab).count() if etab else 0,
    }
    return render(request, "dashboard.html", context)


def health(request):
    return JsonResponse({"status": "ok", "version": "0.1.0", "product": "AutoPilot"})
