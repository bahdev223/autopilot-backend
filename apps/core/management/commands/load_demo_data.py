"""
Commande de demonstration — cree un etablissement, des utilisateurs et des donnees de test.
"""
from datetime import date
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django_formation.models.etablissement import Etablissement
from django_formation.models.membre import MembreEtablissement
from django_formation.models.apprenant import Apprenant
from django_formation.models.formation import Formation
from django_formation.models.session import SessionFormation
from django_formation.models.inscription import Inscription
from django_formation.services.apprenants import ApprenantService
from django_formation.services.formations import FormationService
from django_formation.services.sessions import SessionService
from django_formation.services.inscriptions import InscriptionService


class Command(BaseCommand):
    help = "Charge des donnees de demonstration pour AutoPilot"

    def handle(self, *args, **options):
        self.stdout.write("Creation des donnees de demonstration AutoPilot...")

        admin, _ = User.objects.get_or_create(username="admin", defaults={"is_staff": True, "is_superuser": True})
        if not admin.password or admin.password.startswith("!"):
            admin.set_password("admin123")
            admin.save()

        etab, _ = Etablissement.objects.get_or_create(
            code="autopilot-demo",
            defaults={
                "nom": "AutoPilot Demo",
                "ville": "Bamako",
                "pays": "Mali",
                "telephone": "+223 70 00 00 00",
                "email": "contact@autopilot.app",
            },
        )

        MembreEtablissement.objects.get_or_create(
            etablissement=etab, utilisateur=admin,
            defaults={"role": "PROPRIETAIRE"},
        )

        apprenant_svc = ApprenantService()
        apprenants_data = [
            ("Diarra", "Mamadou", "+223 70 11 11 11", "mamadou@email.com"),
            ("Traore", "Fatoumata", "+223 70 22 22 22", "fatou@email.com"),
            ("Diallo", "Amadou", "+223 70 33 33 33", "amadou@email.com"),
            ("Sissoko", "Aminata", "+223 70 44 44 44", "aminata@email.com"),
            ("Kone", "Ousmane", "+223 70 55 55 55", "ousmane@email.com"),
        ]
        apprenants = []
        for nom, prenom, tel, email in apprenants_data:
            a = apprenant_svc.creer_apprenant(
                etablissement=etab, nom=nom, prenom=prenom,
                telephone=tel, email=email, cree_par=admin,
            )
            apprenants.append(a)
        self.stdout.write(f"  [OK] {len(apprenants)} apprenants crees")

        formation_svc = FormationService()
        formations_data = [
            ("CODE-A", "Permis A (Moto)", 120, 15),
            ("CODE-B", "Permis B (Voiture)", 240, 30),
            ("CODE-C", "Permis C (Poids lourd)", 180, 25),
            ("CODE-ACE", "Permis ACE (Moto + Voiture)", 300, 40),
        ]
        formations = []
        for code, nom, heures, duree_jours in formations_data:
            f = formation_svc.creer_formation(
                etablissement=etab, code=code, nom=nom,
                duree_heures=heures, duree_jours=duree_jours,
                tarif_indicatif=150000,
            )
            formation_svc.publier_formation(f)
            formations.append(f)
        self.stdout.write(f"  [OK] {len(formations)} formations creees et publiees")

        session_svc = SessionService()
        sessions_data = [
            ("B-2026-01", "Session Janvier 2026", date(2026, 1, 10), 20, formations[1]),
            ("B-2026-03", "Session Mars 2026", date(2026, 3, 15), 25, formations[1]),
            ("B-2026-06", "Session Juin 2026", date(2026, 6, 1), 30, formations[1]),
            ("A-2026-01", "Session Moto Janvier", date(2026, 1, 15), 15, formations[0]),
            ("C-2026-01", "Session PL Janvier", date(2026, 2, 1), 12, formations[2]),
        ]
        sessions = []
        for code, nom, debut, capacite, formation in sessions_data:
            s = session_svc.creer_session(
                etablissement=etab, formation=formation,
                code=code, nom=nom, date_debut=debut, capacite=capacite,
            )
            session_svc.ouvrir_inscriptions(s)
            sessions.append(s)
        self.stdout.write(f"  [OK] {len(sessions)} sessions creees et ouvertes")

        inscription_svc = InscriptionService()
        for i, apprenant in enumerate(apprenants):
            session = sessions[i % len(sessions)]
            inscription = inscription_svc.creer_preinscription(
                apprenant=apprenant, session=session,
                commentaire=f"Inscription de demonstration #{i+1}",
                cree_par=admin,
            )
            if i < 3:
                inscription_svc.confirmer_inscription(inscription, modifie_par=admin)
        self.stdout.write("  [OK] Inscriptions creees")

        self.stdout.write(self.style.SUCCESS(
            "\n[OK] Donnees de demonstration pretes !\n"
            "   Admin : admin / admin123\n"
            f"   URL : http://localhost:8000/admin/\n"
            f"   API : http://localhost:8000/api/v1/formation/\n"
            f"   Docs : http://localhost:8000/api/docs/\n"
        ))
