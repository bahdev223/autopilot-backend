from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django_autoecole.models import CategoriePermis


class Command(BaseCommand):
    help = "Configure AutoPilot : groupes, permissions, categories de permis par defaut"

    def handle(self, *args, **options):
        self.stdout.write("Configuration d'AutoPilot...")

        groupes = {
            "DIRECTION": [
                "django_formation.add_etablissement",
                "django_formation.change_etablissement",
                "django_formation.view_etablissement",
                "django_formation.add_apprenant",
                "django_formation.change_apprenant",
                "django_formation.view_apprenant",
                "django_formation.delete_apprenant",
                "django_formation.add_formation",
                "django_formation.change_formation",
                "django_formation.view_formation",
                "django_formation.add_session",
                "django_formation.change_session",
                "django_formation.view_session",
                "django_formation.add_inscription",
                "django_formation.change_inscription",
                "django_formation.view_inscription",
                "django_autoecole.add_categoriepermis",
                "django_autoecole.change_categoriepermis",
                "django_autoecole.view_categoriepermis",
                "django_autoecole.add_moniteur",
                "django_autoecole.change_moniteur",
                "django_autoecole.view_moniteur",
                "django_autoecole.delete_moniteur",
                "django_autoecole.add_vehicule",
                "django_autoecole.change_vehicule",
                "django_autoecole.view_vehicule",
                "django_autoecole.add_dossierautoecole",
                "django_autoecole.change_dossierautoecole",
                "django_autoecole.view_dossierautoecole",
                "django_autoecole.add_leconconduite",
                "django_autoecole.change_leconconduite",
                "django_autoecole.view_leconconduite",
                "django_autoecole.add_examenautoecole",
                "django_autoecole.change_examenautoecole",
                "django_autoecole.view_examenautoecole",
            ],
            "RESPONSABLE_PEDAGOGIQUE": [
                "django_formation.add_apprenant",
                "django_formation.change_apprenant",
                "django_formation.view_apprenant",
                "django_formation.add_formation",
                "django_formation.change_formation",
                "django_formation.view_formation",
                "django_formation.add_session",
                "django_formation.change_session",
                "django_formation.view_session",
                "django_formation.add_inscription",
                "django_formation.change_inscription",
                "django_formation.view_inscription",
                "django_autoecole.view_categoriepermis",
                "django_autoecole.view_moniteur",
                "django_autoecole.view_vehicule",
                "django_autoecole.add_dossierautoecole",
                "django_autoecole.change_dossierautoecole",
                "django_autoecole.view_dossierautoecole",
                "django_autoecole.add_leconconduite",
                "django_autoecole.change_leconconduite",
                "django_autoecole.view_leconconduite",
                "django_autoecole.add_examenautoecole",
                "django_autoecole.change_examenautoecole",
                "django_autoecole.view_examenautoecole",
            ],
            "AGENT_PLANNING": [
                "django_formation.view_apprenant",
                "django_formation.view_formation",
                "django_formation.view_session",
                "django_formation.view_inscription",
                "django_autoecole.view_categoriepermis",
                "django_autoecole.view_moniteur",
                "django_autoecole.view_vehicule",
                "django_autoecole.view_dossierautoecole",
                "django_autoecole.add_leconconduite",
                "django_autoecole.change_leconconduite",
                "django_autoecole.view_leconconduite",
                "django_autoecole.view_examenautoecole",
            ],
            "LECTEUR": [
                "django_formation.view_apprenant",
                "django_formation.view_formation",
                "django_formation.view_session",
                "django_formation.view_inscription",
                "django_autoecole.view_categoriepermis",
                "django_autoecole.view_moniteur",
                "django_autoecole.view_vehicule",
                "django_autoecole.view_dossierautoecole",
                "django_autoecole.view_leconconduite",
                "django_autoecole.view_examenautoecole",
            ],
        }

        for nom_groupe, perms_codes in groupes.items():
            groupe, created = Group.objects.get_or_create(name=nom_groupe)
            if created:
                self.stdout.write(f"  [OK] Groupe '{nom_groupe}' cree")
            for code in perms_codes:
                try:
                    perm = Permission.objects.get(codename=code.split(".")[1])
                    groupe.permissions.add(perm)
                except Permission.DoesNotExist:
                    pass
            self.stdout.write(f"  [OK] Groupe '{nom_groupe}' : {groupe.permissions.count()} permissions")

        categories_defaut = [
            ("A", "Permis A (Moto)", 16, 8, 20, 4),
            ("A1", "Permis A1 (Moto legere)", 14, 6, 16, 3),
            ("B", "Permis B (Voiture)", 30, 12, 20, 5),
            ("B1", "Permis B1 (Voiture legere)", 20, 8, 16, 3),
            ("C", "Permis C (Poids lourd)", 25, 15, 25, 4),
            ("D", "Permis D (Transport en commun)", 30, 15, 25, 4),
            ("E", "Permis E (Remorque)", 15, 10, 20, 3),
            ("ACE", "Permis ACE (Moto + Voiture)", 40, 20, 30, 6),
        ]
        self.stdout.write("  [OK] Categories de permis par defaut disponibles (creees par etablissement)")

        self.stdout.write(self.style.SUCCESS("\n[OK] AutoPilot configure avec succes !\n"
            "   Lancez 'python manage.py setup_demo_autoecole' pour les donnees de demonstration."))
