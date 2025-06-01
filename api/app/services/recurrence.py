"""
Service de gestion des récurrences pour les tâches
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import date, datetime, time, timedelta
from dateutil.rrule import rrule, rrulestr, DAILY, WEEKLY, MONTHLY, YEARLY
from dateutil.parser import parse
from dataclasses import dataclass
import holidays
from uuid import UUID

from app.core.logging import get_logger
from app.core.exceptions import InvalidInput, BusinessRuleViolation

logger = get_logger(__name__)


@dataclass
class RecurrenceInfo:
    """Informations sur une règle de récurrence"""
    frequency: str  # DAILY, WEEKLY, MONTHLY, YEARLY
    interval: int
    days_of_week: Optional[List[str]] = None  # MO, TU, WE, TH, FR, SA, SU
    day_of_month: Optional[int] = None
    month_of_year: Optional[int] = None
    count: Optional[int] = None  # Nombre d'occurrences
    until: Optional[date] = None  # Date de fin
    is_valid: bool = True
    error_message: Optional[str] = None


class RecurrenceService:
    """Service pour gérer les règles de récurrence des tâches"""
    
    # Règles de récurrence prédéfinies courantes
    PRESETS = {
        "daily": "FREQ=DAILY",
        "weekdays": "FREQ=DAILY;BYDAY=MO,TU,WE,TH,FR",
        "weekends": "FREQ=WEEKLY;BYDAY=SA,SU",
        "weekly": "FREQ=WEEKLY",
        "biweekly": "FREQ=WEEKLY;INTERVAL=2",
        "monthly": "FREQ=MONTHLY",
        "quarterly": "FREQ=MONTHLY;INTERVAL=3",
        "yearly": "FREQ=YEARLY",
        
        # Tâches ménagères courantes
        "weekly_monday": "FREQ=WEEKLY;BYDAY=MO",
        "weekly_friday": "FREQ=WEEKLY;BYDAY=FR",
        "twice_weekly": "FREQ=WEEKLY;BYDAY=MO,TH",
        "every_two_weeks": "FREQ=WEEKLY;INTERVAL=2",
        "first_of_month": "FREQ=MONTHLY;BYMONTHDAY=1",
        "last_of_month": "FREQ=MONTHLY;BYMONTHDAY=-1",
        "seasonal": "FREQ=MONTHLY;INTERVAL=3;BYMONTHDAY=1",
    }
    
    # Limites de sécurité
    MAX_OCCURRENCES_PER_YEAR = 366  # 366 pour les années bissextiles
    MAX_GENERATION_DAYS = 365
    DEFAULT_GENERATION_DAYS = 90
    
    def __init__(self, country_code: str = "FR"):
        """
        Initialise le service avec les jours fériés du pays
        
        Args:
            country_code: Code pays pour les jours fériés (FR par défaut)
        """
        self.country_code = country_code
        self._holidays_cache: Dict[int, holidays.HolidayBase] = {}
    
    def get_holidays(self, year: int) -> holidays.HolidayBase:
        """
        Obtenir les jours fériés pour une année donnée
        
        Args:
            year: Année pour laquelle obtenir les jours fériés
        
        Returns:
            Objet holidays contenant les jours fériés
        """
        if year not in self._holidays_cache:
            if self.country_code == "FR":
                self._holidays_cache[year] = holidays.France(years=year)
            elif self.country_code == "US":
                self._holidays_cache[year] = holidays.UnitedStates(years=year)
            elif self.country_code == "UK":
                self._holidays_cache[year] = holidays.UnitedKingdom(years=year)
            else:
                # Par défaut, utiliser la France
                self._holidays_cache[year] = holidays.France(years=year)
        
        return self._holidays_cache[year]
    
    def validate_rrule(self, rrule_string: str) -> RecurrenceInfo:
        """
        Valider une règle RRULE et extraire ses informations
        
        Args:
            rrule_string: Chaîne RRULE à valider
        
        Returns:
            RecurrenceInfo avec les détails de la règle
        """
        # Vérification préliminaire pour les règles vides
        if not rrule_string or rrule_string.strip() == "":
            return RecurrenceInfo(
                frequency="INVALID",
                interval=0,
                is_valid=False,
                error_message="La règle de récurrence ne peut pas être vide"
            )
            
        try:
            # Parser la règle
            rule = rrulestr(rrule_string, dtstart=datetime.now())
            
            # Extraire les informations de base
            # Conversion de la fréquence numérique vers string
            freq_map = {
                DAILY: "DAILY",
                WEEKLY: "WEEKLY", 
                MONTHLY: "MONTHLY",
                YEARLY: "YEARLY"
            }
            
            info = RecurrenceInfo(
                frequency=freq_map.get(rule._freq, "UNKNOWN"),
                interval=rule._interval
            )
            
            # Extraire les jours de la semaine
            if rule._byweekday:
                weekdays = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]
                info.days_of_week = [
                    weekdays[day.weekday] if hasattr(day, 'weekday') else weekdays[day]
                    for day in rule._byweekday
                ]
            
            # Extraire le jour du mois
            if rule._bymonthday:
                if isinstance(rule._bymonthday, (list, tuple)):
                    info.day_of_month = rule._bymonthday[0]
                else:
                    info.day_of_month = rule._bymonthday
            
            # Extraire le mois de l'année
            if rule._bymonth:
                info.month_of_year = rule._bymonth[0] if isinstance(rule._bymonth, list) else rule._bymonth
            
            # Extraire le nombre d'occurrences ou la date de fin
            if rule._count:
                info.count = rule._count
            if rule._until:
                info.until = rule._until.date() if hasattr(rule._until, 'date') else rule._until
            
            # Valider les limites
            self._validate_limits(info, rrule_string)
            
            return info
            
        except BusinessRuleViolation:
            # Re-lancer les BusinessRuleViolation pour les tests et validation API
            raise
        except Exception as e:
            logger.warning(f"Règle RRULE invalide: {rrule_string}", exc_info=True)
            return RecurrenceInfo(
                frequency="INVALID",
                interval=0,
                is_valid=False,
                error_message=f"Règle de récurrence invalide: {str(e)}"
            )
    
    def _validate_limits(self, info: RecurrenceInfo, rrule_string: str) -> None:
        """
        Valider que la règle respecte les limites de sécurité
        
        Args:
            info: Informations de récurrence à valider
            rrule_string: Règle originale pour test
        
        Raises:
            BusinessRuleViolation: Si la règle dépasse les limites
        """
        # Tester la génération sur un an
        test_start = date.today()
        test_end = test_start + timedelta(days=365)
        
        try:
            # Convertir en datetime pour rrule
            test_start_dt = datetime.combine(test_start, datetime.min.time())
            test_end_dt = datetime.combine(test_end, datetime.max.time())
            
            rule = rrulestr(rrule_string, dtstart=test_start_dt)
            occurrences = list(rule.between(test_start_dt, test_end_dt, inc=True))
            
            if len(occurrences) > self.MAX_OCCURRENCES_PER_YEAR:
                raise BusinessRuleViolation(
                    rule="MAX_OCCURRENCES",
                    details=f"La règle génère trop d'occurrences ({len(occurrences)} par an, max: {self.MAX_OCCURRENCES_PER_YEAR})"
                )
        except BusinessRuleViolation:
            # Re-lancer les BusinessRuleViolation
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la validation des limites: {e}")
            # Ne pas lever l'exception pour les autres erreurs
    
    def calculate_next_occurrences(
        self,
        rrule_string: str,
        start_date: Optional[date] = None,
        count: int = 10,
        exclude_holidays: bool = False,
        exclude_weekends: bool = False
    ) -> List[date]:
        """
        Calculer les prochaines occurrences d'une règle
        
        Args:
            rrule_string: Règle RRULE
            start_date: Date de début (aujourd'hui par défaut)
            count: Nombre d'occurrences à calculer
            exclude_holidays: Exclure les jours fériés
            exclude_weekends: Exclure les weekends
        
        Returns:
            Liste des prochaines dates d'occurrence
        """
        if start_date is None:
            start_date = date.today()
        
        try:
            rule = rrulestr(rrule_string, dtstart=start_date)
            occurrences = []
            
            # Générer plus d'occurrences que nécessaire pour compenser les exclusions
            max_iterations = count * 3
            for dt in rule:
                if len(occurrences) >= count:
                    break
                
                occurrence_date = dt.date() if hasattr(dt, 'date') else dt
                
                # Vérifier les exclusions
                if exclude_weekends and occurrence_date.weekday() in [5, 6]:  # Samedi, Dimanche
                    continue
                
                if exclude_holidays:
                    year_holidays = self.get_holidays(occurrence_date.year)
                    if occurrence_date in year_holidays:
                        continue
                
                occurrences.append(occurrence_date)
                
                max_iterations -= 1
                if max_iterations <= 0:
                    break
            
            return occurrences
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des occurrences: {e}")
            return []
    
    def generate_occurrences_between(
        self,
        rrule_string: str,
        start_date: date,
        end_date: date,
        exclude_holidays: bool = False,
        exclude_weekends: bool = False,
        max_occurrences: Optional[int] = None
    ) -> List[Tuple[date, time]]:
        """
        Générer toutes les occurrences entre deux dates
        
        Args:
            rrule_string: Règle RRULE
            start_date: Date de début
            end_date: Date de fin
            exclude_holidays: Exclure les jours fériés
            exclude_weekends: Exclure les weekends
            max_occurrences: Nombre maximum d'occurrences
        
        Returns:
            Liste de tuples (date, heure) pour chaque occurrence
        """
        if max_occurrences is None:
            max_occurrences = self.MAX_OCCURRENCES_PER_YEAR
        
        # Valider la période
        if end_date < start_date:
            raise InvalidInput(
                field="date_range",
                value=f"{start_date} - {end_date}",
                reason="La date de fin doit être après la date de début"
            )
        
        if (end_date - start_date).days > self.MAX_GENERATION_DAYS:
            raise BusinessRuleViolation(
                rule="MAX_GENERATION_PERIOD",
                details=f"La période de génération ne peut pas dépasser {self.MAX_GENERATION_DAYS} jours"
            )
        
        try:
            rule = rrulestr(rrule_string, dtstart=datetime.combine(start_date, time.min))
            occurrences = []
            
            for dt in rule.between(
                datetime.combine(start_date, time.min),
                datetime.combine(end_date, time.max),
                inc=True
            ):
                if len(occurrences) >= max_occurrences:
                    break
                
                occurrence_date = dt.date()
                occurrence_time = dt.time()
                
                # Vérifier les exclusions
                if exclude_weekends and occurrence_date.weekday() in [5, 6]:
                    continue
                
                if exclude_holidays:
                    year_holidays = self.get_holidays(occurrence_date.year)
                    if occurrence_date in year_holidays:
                        continue
                
                occurrences.append((occurrence_date, occurrence_time))
            
            return occurrences
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération des occurrences: {e}")
            raise InvalidInput(
                field="rrule",
                value=rrule_string,
                reason=f"Impossible de générer les occurrences: {str(e)}"
            )
    
    def suggest_skip_until(
        self,
        rrule_string: str,
        current_date: date,
        skip_count: int = 1
    ) -> Optional[date]:
        """
        Suggérer une date pour reprendre après avoir sauté des occurrences
        
        Args:
            rrule_string: Règle RRULE
            current_date: Date actuelle
            skip_count: Nombre d'occurrences à sauter
        
        Returns:
            Date suggérée pour reprendre
        """
        try:
            occurrences = self.calculate_next_occurrences(
                rrule_string,
                start_date=current_date,
                count=skip_count + 1
            )
            
            if len(occurrences) > skip_count:
                return occurrences[skip_count]
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul de skip_until: {e}")
            return None
    
    def adjust_for_holiday(
        self,
        occurrence_date: date,
        strategy: str = "next_working_day"
    ) -> date:
        """
        Ajuster une date d'occurrence si elle tombe un jour férié
        
        Args:
            occurrence_date: Date d'occurrence originale
            strategy: Stratégie d'ajustement
                - "next_working_day": Reporter au prochain jour ouvré
                - "previous_working_day": Avancer au jour ouvré précédent
                - "skip": Ignorer l'occurrence (retourne None)
        
        Returns:
            Date ajustée ou None si l'occurrence doit être ignorée
        """
        year_holidays = self.get_holidays(occurrence_date.year)
        
        # Si ce n'est pas un jour férié, pas d'ajustement
        if occurrence_date not in year_holidays:
            return occurrence_date
        
        if strategy == "skip":
            return None
        
        elif strategy == "next_working_day":
            adjusted_date = occurrence_date
            while True:
                adjusted_date += timedelta(days=1)
                # Vérifier si c'est un jour ouvré
                if (adjusted_date.weekday() not in [5, 6] and 
                    adjusted_date not in self.get_holidays(adjusted_date.year)):
                    return adjusted_date
        
        elif strategy == "previous_working_day":
            adjusted_date = occurrence_date
            while True:
                adjusted_date -= timedelta(days=1)
                # Vérifier si c'est un jour ouvré
                if (adjusted_date.weekday() not in [5, 6] and 
                    adjusted_date not in self.get_holidays(adjusted_date.year)):
                    return adjusted_date
        
        else:
            # Stratégie non reconnue, retourner la date originale
            return occurrence_date
    
    @staticmethod
    def create_rrule_from_params(
        frequency: str,
        interval: int = 1,
        days_of_week: Optional[List[str]] = None,
        day_of_month: Optional[int] = None,
        months: Optional[List[int]] = None,
        count: Optional[int] = None,
        until: Optional[date] = None
    ) -> str:
        """
        Créer une règle RRULE à partir de paramètres
        
        Args:
            frequency: DAILY, WEEKLY, MONTHLY, YEARLY
            interval: Intervalle entre occurrences
            days_of_week: Jours de la semaine (MO, TU, etc.)
            day_of_month: Jour du mois (1-31 ou -1 pour dernier jour)
            months: Mois de l'année (1-12)
            count: Nombre total d'occurrences
            until: Date de fin
        
        Returns:
            Chaîne RRULE formatée
        """
        parts = [f"FREQ={frequency.upper()}"]
        
        if interval > 1:
            parts.append(f"INTERVAL={interval}")
        
        if days_of_week:
            parts.append(f"BYDAY={','.join(days_of_week)}")
        
        if day_of_month is not None:
            parts.append(f"BYMONTHDAY={day_of_month}")
        
        if months:
            parts.append(f"BYMONTH={','.join(map(str, months))}")
        
        if count is not None:
            parts.append(f"COUNT={count}")
        
        if until is not None:
            until_str = until.strftime("%Y%m%d")
            parts.append(f"UNTIL={until_str}")
        
        return ";".join(parts)
    
    @staticmethod
    def get_preset_rule(preset_name: str) -> Optional[str]:
        """
        Obtenir une règle prédéfinie par son nom
        
        Args:
            preset_name: Nom de la règle prédéfinie
        
        Returns:
            Règle RRULE ou None si non trouvée
        """
        return RecurrenceService.PRESETS.get(preset_name)
    
    @staticmethod
    def describe_rrule(rrule_string: str, locale: str = "fr") -> str:
        """
        Générer une description lisible d'une règle RRULE
        
        Args:
            rrule_string: Règle RRULE
            locale: Langue pour la description
        
        Returns:
            Description en langage naturel
        """
        try:
            rule = rrulestr(rrule_string)
            
            # Mapping des fréquences
            freq_map = {
                DAILY: "tous les jours",
                WEEKLY: "toutes les semaines", 
                MONTHLY: "tous les mois",
                YEARLY: "tous les ans"
            }
            
            # Mapping des jours
            day_map = {
                0: "lundi",
                1: "mardi",
                2: "mercredi",
                3: "jeudi",
                4: "vendredi",
                5: "samedi",
                6: "dimanche"
            }
            
            description = freq_map.get(rule._freq, "périodiquement")
            
            if rule._interval > 1:
                description = f"tous les {rule._interval} " + {
                    DAILY: "jours",
                    WEEKLY: "semaines",
                    MONTHLY: "mois",
                    YEARLY: "ans"
                }.get(rule._freq, "périodes")
            
            # Pour les règles hebdomadaires, éviter d'afficher le jour par défaut 
            # si BYDAY n'était pas explicitement spécifié
            show_weekdays = rule._byweekday is not None
            if rule._freq == WEEKLY and "BYDAY" not in rrule_string.upper():
                show_weekdays = False
                
            if show_weekdays and rule._byweekday:
                days = []
                for day in rule._byweekday:
                    weekday = day.weekday if hasattr(day, 'weekday') else day
                    days.append(day_map.get(weekday, str(weekday)))
                
                if len(days) == 1:
                    description += f" le {days[0]}"
                else:
                    description += f" les {', '.join(days[:-1])} et {days[-1]}"
            
            # Gérer BYMONTHDAY seulement si explicitement spécifié dans la règle
            if "BYMONTHDAY=" in rrule_string.upper():
                # Extraire BYMONTHDAY de la chaîne
                parts = rrule_string.upper().split(";")
                for part in parts:
                    if part.startswith("BYMONTHDAY="):
                        monthday_str = part.split("=")[1]
                        if monthday_str == "-1":
                            description += " le dernier jour du mois"
                        else:
                            description += f" le {monthday_str} du mois"
                        break
            
            if rule._count:
                description += f" ({rule._count} fois au total)"
            
            if rule._until:
                until_date = rule._until.strftime("%d/%m/%Y")
                description += f" jusqu'au {until_date}"
            
            return description.capitalize()
            
        except Exception as e:
            logger.error(f"Erreur lors de la description de la règle: {e}")
            return "Récurrence personnalisée"


# Instance singleton du service
recurrence_service = RecurrenceService()