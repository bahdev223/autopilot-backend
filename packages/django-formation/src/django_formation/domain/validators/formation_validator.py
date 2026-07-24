from datetime import date
from typing import Optional
from decimal import Decimal


class FormationValidator:
    @staticmethod
    def valider_tarif(tarif) -> None:
        if tarif is not None:
            val = Decimal(str(tarif))
            if val < 0:
                raise ValueError("Le tarif ne peut pas être négatif")

    @staticmethod
    def valider_duree(duree) -> None:
        if duree is not None and duree < 0:
            raise ValueError("La durée ne peut pas être négative")

    @staticmethod
    def valider_capacite(capacite) -> None:
        if capacite is not None and capacite <= 0:
            raise ValueError("La capacité doit être supérieure à zéro")

    @staticmethod
    def valider_dates(date_debut: date, date_fin: Optional[date] = None) -> None:
        if date_fin and date_fin < date_debut:
            raise ValueError("La date de fin doit être postérieure à la date de début")

    @staticmethod
    def valider_periodes_inscription(
        date_ouverture: Optional[date],
        date_fermeture: Optional[date] = None,
    ) -> None:
        if date_ouverture and date_fermeture and date_fermeture < date_ouverture:
            raise ValueError("La date de fermeture des inscriptions doit être postérieure à la date d'ouverture")
