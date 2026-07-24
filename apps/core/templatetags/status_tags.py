from django import template

register = template.Library()

STATUS_COLORS = {
    # Brouillon / Init
    "BROUILLON": "bg-gray-100 text-gray-700",
    "BROUILLON,": "bg-gray-100 text-gray-700",
    "PLANIFIEE": "bg-yellow-100 text-yellow-700",
    "PLANIFIE": "bg-yellow-100 text-yellow-700",
    # Actif / Ouvert / Disponible
    "ACTIF": "bg-green-100 text-green-700",
    "OUVERT": "bg-green-100 text-green-700",
    "DISPONIBLE": "bg-green-100 text-green-700",
    "PUBLIE": "bg-green-100 text-green-700",

    "CONFIRMEE": "bg-blue-100 text-blue-700",
    "CONFIRME": "bg-blue-100 text-blue-700",
    "EN_COURS": "bg-blue-100 text-blue-700",
    "EN_FORMATION": "bg-blue-100 text-blue-700",
    "RESERVE": "bg-blue-100 text-blue-700",
    "PRET_EXAMEN": "bg-blue-100 text-blue-700",
    "PRESENTE": "bg-indigo-100 text-indigo-700",
    # Attente
    "EN_ATTENTE": "bg-yellow-100 text-yellow-700",
    "PREINSCRITE": "bg-yellow-100 text-yellow-700",
    # Oranges
    "SUSPENDU": "bg-orange-100 text-orange-700",
    "ENTRETIEN": "bg-orange-100 text-orange-700",
    "ABSENT": "bg-orange-100 text-orange-700",
    "ABSENT_CANDIDAT": "bg-orange-100 text-orange-700",
    "ABSENT_MONITEUR": "bg-orange-100 text-orange-700",
    "REPORTEE": "bg-orange-100 text-orange-700",
    # Reds
    "ANNULE": "bg-red-100 text-red-700",
    "ANNULEE": "bg-red-100 text-red-700",
    "ECHOUE": "bg-red-100 text-red-700",
    "AJOURNE": "bg-red-100 text-red-700",
    "PANNE": "bg-red-100 text-red-700",
    "HORS_SERVICE": "bg-red-100 text-red-700",
    "REFUSE": "bg-red-100 text-red-700",
    "ABANDON": "bg-red-100 text-red-700",
    "ERREUR": "bg-red-100 text-red-700",
    # Dark grays
    "CLOTURE": "bg-gray-200 text-gray-700",
    "ARCHIVE": "bg-gray-200 text-gray-700",
    "ARCHIVEE": "bg-gray-200 text-gray-700",
    "TERMINE": "bg-gray-200 text-gray-700",
    "INACTIF": "bg-gray-200 text-gray-700",
    "INDISPONIBLE": "bg-orange-100 text-orange-700",
    # Green darks
    "REUSSI": "bg-emerald-100 text-emerald-700",
    "ADMIS": "bg-emerald-100 text-emerald-700",
    "REALISEE": "bg-emerald-100 text-emerald-700",
}

STATUS_LABELS = {
    "BROUILLON": "Brouillon",
    "ACTIF": "Actif",
    "INACTIF": "Inactif",
    "OUVERT": "Ouvert",
    "EN_FORMATION": "En formation",
    "PRET_EXAMEN": "Prêt pour examen",
    "PRESENTE_EXAMEN": "Présenté à l'examen",
    "REUSSI": "Réussi",
    "ECHOUE": "Échoué",
    "SUSPENDU": "Suspendu",
    "ANNULE": "Annulé",
    "ANNULEE": "Annulée",
    "CLOTURE": "Clôturé",
    "PLANIFIEE": "Planifiée",
    "PLANIFIE": "Planifié",
    "CONFIRMEE": "Confirmée",
    "CONFIRME": "Confirmé",
    "EN_COURS": "En cours",
    "REALISEE": "Réalisée",
    "ABSENT_CANDIDAT": "Candidat absent",
    "ABSENT_MONITEUR": "Moniteur absent",
    "REPORTEE": "Reportée",
    "DISPONIBLE": "Disponible",
    "RESERVE": "Réservé",
    "EN_LECON": "En leçon",
    "ENTRETIEN": "En entretien",
    "PANNE": "En panne",
    "HORS_SERVICE": "Hors service",
    "ARCHIVE": "Archivé",
    "ARCHIVEE": "Archivée",
    "PREINSCRITE": "Préinscrite",
    "CONFIRMEE,": "Confirmée",
    "EN_ATTENTE": "En attente",
    "REFUSE": "Refusé",
    "ABANDON": "Abandon",
    "TERMINE": "Terminée",
    "PRESENTE": "Présenté",
    "ABSENT": "Absent",
    "RESULTAT_DISPONIBLE": "Résultat disponible",
    "ADMIS": "Admis",
    "AJOURNE": "Ajourné",
    "PUBLIE": "Publiée",
    "INDISPONIBLE": "Indisponible",
}


@register.filter
def status_color(value):
    return STATUS_COLORS.get(str(value).strip(), "bg-gray-100 text-gray-700")


@register.filter
def status_label(value):
    return STATUS_LABELS.get(str(value).strip(), str(value))


@register.filter
def startswith(value, arg):
    return str(value).startswith(str(arg))


@register.filter
def get(value, arg):
    return value.get(arg, "")
