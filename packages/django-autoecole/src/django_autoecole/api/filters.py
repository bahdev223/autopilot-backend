import django_filters
from django_autoecole.models import (
    CategoriePermis, Moniteur, Vehicule, DossierAutoEcole,
    LeconConduite, ExamenAutoEcole,
)


class CategoriePermisFilter(django_filters.FilterSet):
    etablissement = django_filters.UUIDFilter()
    actif = django_filters.BooleanFilter()
    search = django_filters.CharFilter(method="filter_search")

    class Meta:
        model = CategoriePermis
        fields = ["etablissement", "actif"]

    def filter_search(self, queryset, name, value):
        return queryset.filter(code__icontains=value) | queryset.filter(nom__icontains=value)


class MoniteurFilter(django_filters.FilterSet):
    etablissement = django_filters.UUIDFilter()
    statut = django_filters.ChoiceFilter(choices=Moniteur._meta.get_field("statut").choices)
    categorie_permis = django_filters.UUIDFilter(field_name="categories_permis__id")

    class Meta:
        model = Moniteur
        fields = ["etablissement", "statut"]


class VehiculeFilter(django_filters.FilterSet):
    etablissement = django_filters.UUIDFilter()
    statut = django_filters.ChoiceFilter(choices=Vehicule._meta.get_field("statut").choices)
    categorie_permis = django_filters.UUIDFilter()
    type_boite = django_filters.ChoiceFilter(choices=Vehicule._meta.get_field("type_boite").choices)
    documents_expires = django_filters.BooleanFilter(method="filter_documents_expires")
    disponible = django_filters.BooleanFilter(method="filter_disponible")

    class Meta:
        model = Vehicule
        fields = ["etablissement", "statut", "categorie_permis", "type_boite"]

    def filter_documents_expires(self, queryset, name, value):
        from datetime import date
        today = date.today()
        if value:
            return queryset.filter(
                date_expiration_assurance__lt=today
            ) | queryset.filter(date_expiration_visite_technique__lt=today)
        return queryset

    def filter_disponible(self, queryset, name, value):
        from ..constants import StatutVehicule
        if value:
            return queryset.filter(statut=StatutVehicule.DISPONIBLE)
        return queryset.exclude(statut=StatutVehicule.DISPONIBLE)


class DossierAutoEcoleFilter(django_filters.FilterSet):
    etablissement = django_filters.UUIDFilter()
    statut = django_filters.ChoiceFilter(choices=DossierAutoEcole._meta.get_field("statut").choices)
    categorie_permis = django_filters.UUIDFilter()
    moniteur_referent = django_filters.UUIDFilter()
    inscrit_apres = django_filters.DateFilter(field_name="date_ouverture", lookup_expr="gte")
    inscrit_avant = django_filters.DateFilter(field_name="date_ouverture", lookup_expr="lte")

    class Meta:
        model = DossierAutoEcole
        fields = ["etablissement", "statut", "categorie_permis", "moniteur_referent"]


class LeconConduiteFilter(django_filters.FilterSet):
    etablissement = django_filters.UUIDFilter()
    dossier = django_filters.UUIDFilter()
    moniteur = django_filters.UUIDFilter()
    vehicule = django_filters.UUIDFilter()
    statut = django_filters.ChoiceFilter(choices=LeconConduite._meta.get_field("statut").choices)
    type_lecon = django_filters.ChoiceFilter(choices=LeconConduite._meta.get_field("type_lecon").choices)
    date_debut_after = django_filters.DateTimeFilter(field_name="date_debut", lookup_expr="gte")
    date_debut_before = django_filters.DateTimeFilter(field_name="date_debut", lookup_expr="lte")

    class Meta:
        model = LeconConduite
        fields = ["etablissement", "dossier", "moniteur", "vehicule", "statut", "type_lecon"]


class ExamenAutoEcoleFilter(django_filters.FilterSet):
    etablissement = django_filters.UUIDFilter()
    dossier = django_filters.UUIDFilter()
    type_examen = django_filters.ChoiceFilter(choices=ExamenAutoEcole._meta.get_field("type_examen").choices)
    statut = django_filters.ChoiceFilter(choices=ExamenAutoEcole._meta.get_field("statut").choices)
    resultat = django_filters.ChoiceFilter(choices=ExamenAutoEcole._meta.get_field("resultat").choices)
    date_after = django_filters.DateTimeFilter(field_name="date_examen", lookup_expr="gte")
    date_before = django_filters.DateTimeFilter(field_name="date_examen", lookup_expr="lte")

    class Meta:
        model = ExamenAutoEcole
        fields = ["etablissement", "dossier", "type_examen", "statut", "resultat"]
