from datetime import date, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
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

from apps.core.models import ConfigurationAutoPilot


class Command(BaseCommand):
    help = "Cree un scenario de demonstration complet AutoPilot avec auto-ecole"

    def handle(self, *args, **options):
        self.stdout.write("Creation du scenario de demonstration complet AutoPilot...")

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
            try:
                a = Apprenant.objects.get(telephone=tel, etablissement=etab)
            except Apprenant.DoesNotExist:
                a = apprenant_svc.creer_apprenant(
                    etablissement=etab, nom=nom, prenom=prenom,
                    telephone=tel, email=email, cree_par=admin,
                )
            apprenants.append(a)
        self.stdout.write(f"  [OK] {len(apprenants)} apprenants")

        formation_svc = FormationService()
        formations_data = [
            ("CODE-B", "Permis B (Voiture)", 240, 30, 250000),
            ("CODE-A", "Permis A (Moto)", 120, 15, 150000),
            ("CODE-C", "Permis C (Poids lourd)", 180, 25, 300000),
        ]
        formations = []
        for code, nom, heures, duree_jours, tarif in formations_data:
            f, _ = Formation.objects.get_or_create(
                code=code, etablissement=etab,
                defaults={"nom": nom, "duree_heures": heures, "duree_jours": duree_jours, "tarif_indicatif": tarif},
            )
            if not f.statut == "PUBLIEE":
                formation_svc.publier_formation(f)
            formations.append(f)
        self.stdout.write(f"  [OK] {len(formations)} formations publiees")

        session_svc = SessionService()
        sessions_data = [
            ("B-2026-01", "Session Janvier 2026", date(2026, 1, 10), 20, formations[0]),
            ("B-2026-03", "Session Mars 2026", date(2026, 3, 15), 25, formations[0]),
            ("A-2026-01", "Session Moto Janvier", date(2026, 1, 15), 15, formations[1]),
            ("C-2026-01", "Session PL Fevrier", date(2026, 2, 1), 12, formations[2]),
            ("B-2026-06", "Session Juin 2026", date(2026, 6, 1), 30, formations[0]),
        ]
        sessions = []
        for code, nom, debut, capacite, formation in sessions_data:
            s, _ = SessionFormation.objects.get_or_create(
                code=code, etablissement=etab,
                defaults={"formation": formation, "nom": nom, "date_debut": debut, "capacite": capacite},
            )
            if s.statut != "INSCRIPTIONS_OUVERTES":
                session_svc.ouvrir_inscriptions(s)
            sessions.append(s)
        self.stdout.write(f"  [OK] {len(sessions)} sessions ouvertes")

        inscription_svc = InscriptionService()
        inscriptions = []
        for i, apprenant in enumerate(apprenants):
            session = sessions[i % len(sessions)]
            try:
                ins = Inscription.objects.get(apprenant=apprenant, session=session)
            except Inscription.DoesNotExist:
                ins = inscription_svc.creer_preinscription(
                    apprenant=apprenant, session=session,
                    commentaire=f"Inscription #{i+1}",
                    cree_par=admin,
                )
                if ins.statut != "CONFIRMEE":
                    ins = inscription_svc.confirmer_inscription(ins, modifie_par=admin)
            inscriptions.append(ins)
        self.stdout.write(f"  [OK] {len(inscriptions)} inscriptions (toutes confirmees)")

        from django_autoecole.models import CategoriePermis, Moniteur, Vehicule, DossierAutoEcole, LeconConduite, ExamenAutoEcole, EvaluationLecon
        from django_autoecole.services.dossiers import (
            creer_dossier_autoecole, ouvrir_dossier, demarrer_formation_dossier,
            declarer_dossier_pret_examen,
        )
        from django_autoecole.services.lecons import planifier_lecon, confirmer_lecon, demarrer_lecon, terminer_lecon
        from django_autoecole.services.examens import planifier_examen as planifier_examen_autoecole, confirmer_examen, marquer_candidat_presente, enregistrer_resultat_examen
        from django_autoecole.constants import (
            StatutDossier, StatutLecon, StatutExamen, ResultatExamen,
            TypeLecon, TypeExamen, TypeBoite, TypeCarburant, NiveauEvaluation,
        )

        cat_b, _ = CategoriePermis.objects.get_or_create(
            etablissement=etab, code="B",
            defaults={"nom": "Permis B (Voiture)", "heures_conduite_minimum": 20,
                      "heures_theorie_minimum": 12, "nombre_evaluations_minimum": 4},
        )
        cat_a, _ = CategoriePermis.objects.get_or_create(
            etablissement=etab, code="A",
            defaults={"nom": "Permis A (Moto)", "heures_conduite_minimum": 16,
                      "heures_theorie_minimum": 8, "nombre_evaluations_minimum": 3},
        )
        cat_c, _ = CategoriePermis.objects.get_or_create(
            etablissement=etab, code="C",
            defaults={"nom": "Permis C (Poids lourd)", "heures_conduite_minimum": 25,
                      "heures_theorie_minimum": 15, "nombre_evaluations_minimum": 4},
        )
        self.stdout.write("  [OK] Categories de permis")

        moniteurs_data = [
            ("MON-001", "Coulibaly", "Moussa", "moussa@autopilot.app"),
            ("MON-002", "Diarra", "Aminata", "aminata.m@autopilot.app"),
            ("MON-003", "Konate", "Samba", "samba@autopilot.app"),
        ]
        moniteurs = []
        for mat, nom, prenom, email in moniteurs_data:
            m, _ = Moniteur.objects.get_or_create(
                matricule=mat, etablissement=etab,
                defaults={"nom": nom, "prenom": prenom, "email": email, "telephone": "+223 70 00 00 01"},
            )
            m.categories_permis.add(cat_b)
            if "Moto" in mat or mat == "MON-003":
                m.categories_permis.add(cat_a)
            if mat == "MON-001":
                m.categories_permis.add(cat_c)
            moniteurs.append(m)
        self.stdout.write(f"  [OK] {len(moniteurs)} moniteurs")

        vehicules_data = [
            ("AA-001-B", "Toyota", "Yaris", 2020, cat_b),
            ("AA-002-B", "Renault", "Clio", 2021, cat_b),
            ("AA-003-A", "Yamaha", "MT-07", 2022, cat_a),
            ("AA-004-C", "Mercedes", "Sprinter", 2019, cat_c),
            ("AA-005-B", "Peugeot", "208", 2023, cat_b),
        ]
        vehicules = []
        for immat, marque, modele, annee, cat in vehicules_data:
            v, _ = Vehicule.objects.get_or_create(
                immatriculation=immat, etablissement=etab,
                defaults={
                    "marque": marque, "modele": modele, "annee": annee,
                    "categorie_permis": cat, "type_boite": TypeBoite.MANUELLE,
                    "type_carburant": TypeCarburant.ESSENCE,
                    "kilometrage_actuel": 50000,
                    "date_mise_en_service": date(2020, 1, 1),
                },
            )
            vehicules.append(v)
        self.stdout.write(f"  [OK] {len(vehicules)} vehicules")

        dossiers = []
        for i, ins in enumerate(inscriptions):
            if hasattr(ins, "dossier_autoecole"):
                dossier = ins.dossier_autoecole
            else:
                cat = cat_b
                if "Moto" in ins.session.formation.nom:
                    cat = cat_a
                elif "Poids lourd" in ins.session.formation.nom:
                    cat = cat_c
                dossier = creer_dossier_autoecole(
                    inscription=ins, categorie_permis_id=cat.pk,
                    moniteur_referent=moniteurs[i % len(moniteurs)],
                    cree_par=admin,
                )
            if dossier.statut == StatutDossier.BROUILLON:
                dossier = ouvrir_dossier(dossier, modifie_par=admin)
            dossiers.append(dossier)
        self.stdout.write(f"  [OK] {len(dossiers)} dossiers crees et ouverts")

        maintenants = timezone.now()
        lecons_crees = 0
        for i, dossier in enumerate(dossiers):
            if dossier.statut not in (StatutDossier.OUVERT, StatutDossier.EN_FORMATION):
                continue
            if dossier.statut == StatutDossier.OUVERT:
                dossier = demarrer_formation_dossier(dossier, modifie_par=admin)
            for j in range(25):
                debut_conduite = maintenants + timedelta(days=j, hours=9)
                fin_conduite = debut_conduite + timedelta(hours=1)
                try:
                    lecon = planifier_lecon(
                        dossier_id=dossier.pk, moniteur_id=moniteurs[i % len(moniteurs)].pk,
                        vehicule_id=vehicules[i % len(vehicules)].pk,
                        type_lecon=TypeLecon.CONDUITE, date_debut=debut_conduite, date_fin=fin_conduite,
                        cree_par=admin,
                    )
                    confirmer_lecon(lecon)
                    demarrer_lecon(lecon, kilometrage_depart=50000 + j * 10)
                    terminer_lecon(lecon, kilometrage_fin=50000 + (j + 1) * 10)
                    lecons_crees += 1
                except Exception:
                    pass
                if j < 13:
                    debut_theorie = maintenants + timedelta(days=j, hours=14)
                    fin_theorie = debut_theorie + timedelta(hours=1)
                    try:
                        lecon = planifier_lecon(
                            dossier_id=dossier.pk, moniteur_id=moniteurs[i % len(moniteurs)].pk,
                            type_lecon=TypeLecon.THEORIE, date_debut=debut_theorie, date_fin=fin_theorie,
                            cree_par=admin,
                        )
                        confirmer_lecon(lecon)
                        demarrer_lecon(lecon)
                        terminer_lecon(lecon)
                        lecons_crees += 1
                    except Exception:
                        pass
        self.stdout.write(f"  [OK] {lecons_crees} lecons planifiees et realisees")

        evaluations_crees = 0
        for dossier in dossiers:
            lecons_conduite = dossier.lecons.filter(
                statut=StatutLecon.REALISEE, type_lecon=TypeLecon.CONDUITE
            ).order_by("-date_debut")[:5]
            for lecon in lecons_conduite:
                EvaluationLecon.objects.get_or_create(
                    lecon=lecon,
                    defaults={
                        "moniteur": lecon.moniteur,
                        "niveau": NiveauEvaluation.EN_PROGRESSION,
                        "note_globale": Decimal("14.00"),
                        "competences_acquises": ["maitrise_volant", "changement_vitesse", "observation"],
                        "recommande_examen": True,
                    },
                )
                evaluations_crees += 1
        self.stdout.write(f"  [OK] {evaluations_crees} evaluations creees")

        examens_crees = 0
        for i, dossier in enumerate(dossiers):
            dossier.refresh_from_db()
            if dossier.statut != StatutDossier.EN_FORMATION or i > 2:
                continue
            try:
                dossier = declarer_dossier_pret_examen(dossier, modifie_par=admin)
                examen = planifier_examen_autoecole(
                    dossier_id=dossier.pk, type_examen=TypeExamen.CONDUITE_OFFICIELLE,
                    date_examen=maintenants + timedelta(days=30),
                    cree_par=admin,
                )
                confirmer_examen(examen)
                marquer_candidat_presente(examen)
                enregistrer_resultat_examen(
                    examen, resultat=ResultatExamen.ADMIS if i == 0 else ResultatExamen.AJOURNE,
                    score=Decimal("16.50") if i == 0 else Decimal("10.00"),
                )
                examens_crees += 1
            except Exception as e:
                self.stdout.write(f"  [WARN] Examen #{i}: {e}")
        self.stdout.write(f"  [OK] {examens_crees} examens crees")

        ConfigurationAutoPilot.objects.get_or_create(
            etablissement=etab,
            defaults={"devise": "XOF", "fuseau_horaire": "Africa/Bamako", "duree_lecon_defaut_minutes": 60},
        )
        self.stdout.write("  [OK] Configuration AutoPilot")

        self.stdout.write(self.style.SUCCESS(
            "\n[OK] Scenario de demonstration complet pret !\n"
            "   Admin : admin / admin123\n"
            "   Établissement : AutoPilot Demo (Bamako)\n"
            f"   {len(apprenants)} apprenants, {len(moniteurs)} moniteurs, {len(vehicules)} vehicules\n"
            f"   {len(dossiers)} dossiers, {lecons_crees} lecons, {examens_crees} examens\n"
            f"   URL : http://localhost:8000/admin/\n"
            f"   Docs API : http://localhost:8000/api/docs/\n"
        ))

