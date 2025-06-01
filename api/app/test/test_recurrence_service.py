"""
Tests pour le service de gestion des récurrences
"""
import pytest
from datetime import date, datetime, timedelta
from dateutil.rrule import DAILY, WEEKLY, MONTHLY

from app.services.recurrence import RecurrenceService, RecurrenceInfo, recurrence_service
from app.core.exceptions import InvalidInput, BusinessRuleViolation


class TestRecurrenceValidation:
    """Tests de validation des règles RRULE"""
    
    def test_validate_simple_rules(self):
        """Test de validation de règles simples"""
        # Règles valides
        valid_rules = [
            "FREQ=DAILY",
            "FREQ=WEEKLY",
            "FREQ=MONTHLY",
            "FREQ=YEARLY",
            "FREQ=DAILY;INTERVAL=2",
            "FREQ=WEEKLY;BYDAY=MO,WE,FR",
            "FREQ=MONTHLY;BYMONTHDAY=15",
            "FREQ=MONTHLY;BYMONTHDAY=-1",
            "FREQ=DAILY;COUNT=10",
            f"FREQ=WEEKLY;UNTIL={date.today() + timedelta(days=30):%Y%m%d}",
        ]
        
        for rule in valid_rules:
            info = recurrence_service.validate_rrule(rule)
            assert info.is_valid, f"Rule '{rule}' should be valid"
            assert info.error_message is None
    
    def test_validate_invalid_rules(self):
        """Test de validation de règles invalides"""
        invalid_rules = [
            "",
            "INVALID",
            "FREQ=INVALID",
            "FREQ=",
            "BYDAY=MO",  # Manque FREQ
            "FREQ=DAILY;INVALID=YES",
        ]
        
        for rule in invalid_rules:
            info = recurrence_service.validate_rrule(rule)
            assert not info.is_valid, f"Rule '{rule}' should be invalid"
            assert info.error_message is not None
    
    def test_extract_rule_info(self):
        """Test d'extraction des informations d'une règle"""
        # Règle hebdomadaire
        info = recurrence_service.validate_rrule("FREQ=WEEKLY;BYDAY=MO,FR;INTERVAL=2")
        assert info.frequency == "WEEKLY"
        assert info.interval == 2
        assert set(info.days_of_week) == {"MO", "FR"}
        
        # Règle mensuelle
        info = recurrence_service.validate_rrule("FREQ=MONTHLY;BYMONTHDAY=15")
        assert info.frequency == "MONTHLY"
        assert info.day_of_month == 15
        
        # Règle avec limite
        info = recurrence_service.validate_rrule("FREQ=DAILY;COUNT=5")
        assert info.count == 5
        
        # Règle avec date de fin
        end_date = date.today() + timedelta(days=30)
        info = recurrence_service.validate_rrule(f"FREQ=WEEKLY;UNTIL={end_date:%Y%m%d}")
        assert info.until == end_date
    
    def test_validate_too_many_occurrences(self):
        """Test de validation des limites d'occurrences"""
        # Règle qui génère trop d'occurrences (plusieurs fois par jour)
        with pytest.raises(BusinessRuleViolation) as exc_info:
            info = recurrence_service.validate_rrule("FREQ=HOURLY")
            if info.is_valid:  # Si la validation basique passe
                recurrence_service._validate_limits(info, "FREQ=HOURLY")
        
        # Une règle quotidienne devrait passer
        info = recurrence_service.validate_rrule("FREQ=DAILY")
        assert info.is_valid


class TestOccurrenceCalculation:
    """Tests de calcul des occurrences"""
    
    def test_calculate_next_occurrences_daily(self):
        """Test de calcul pour une règle quotidienne"""
        occurrences = recurrence_service.calculate_next_occurrences(
            "FREQ=DAILY",
            start_date=date(2024, 1, 1),
            count=5
        )
        
        assert len(occurrences) == 5
        assert occurrences[0] == date(2024, 1, 1)
        assert occurrences[1] == date(2024, 1, 2)
        assert occurrences[4] == date(2024, 1, 5)
    
    def test_calculate_next_occurrences_weekly(self):
        """Test de calcul pour une règle hebdomadaire"""
        # Tous les lundis
        occurrences = recurrence_service.calculate_next_occurrences(
            "FREQ=WEEKLY;BYDAY=MO",
            start_date=date(2024, 1, 1),  # Un lundi
            count=4
        )
        
        assert len(occurrences) == 4
        for occ in occurrences:
            assert occ.weekday() == 0  # Lundi
    
    def test_calculate_with_exclude_weekends(self):
        """Test de calcul en excluant les weekends"""
        occurrences = recurrence_service.calculate_next_occurrences(
            "FREQ=DAILY",
            start_date=date(2024, 1, 1),  # Lundi
            count=5,
            exclude_weekends=True
        )
        
        assert len(occurrences) == 5
        for occ in occurrences:
            assert occ.weekday() not in [5, 6]  # Pas samedi/dimanche
    
    def test_calculate_with_exclude_holidays(self):
        """Test de calcul en excluant les jours fériés"""
        # Utiliser le 1er janvier qui est férié
        occurrences = recurrence_service.calculate_next_occurrences(
            "FREQ=DAILY",
            start_date=date(2024, 1, 1),
            count=3,
            exclude_holidays=True
        )
        
        # Le 1er janvier devrait être exclu
        assert date(2024, 1, 1) not in occurrences
    
    def test_generate_between_dates(self):
        """Test de génération entre deux dates"""
        occurrences = recurrence_service.generate_occurrences_between(
            "FREQ=WEEKLY;BYDAY=MO,WE,FR",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 15)
        )
        
        # Vérifier qu'on a bien les lundis, mercredis et vendredis
        dates = [occ[0] for occ in occurrences]
        weekdays = [d.weekday() for d in dates]
        assert all(wd in [0, 2, 4] for wd in weekdays)  # Lun=0, Mer=2, Ven=4
    
    def test_generate_with_max_occurrences(self):
        """Test de génération avec limite d'occurrences"""
        occurrences = recurrence_service.generate_occurrences_between(
            "FREQ=DAILY",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),  # Un an
            max_occurrences=10
        )
        
        assert len(occurrences) == 10


class TestRecurrencePresets:
    """Tests des règles prédéfinies"""
    
    def test_get_preset_rules(self):
        """Test de récupération des règles prédéfinies"""
        # Règles de base
        assert RecurrenceService.get_preset_rule("daily") == "FREQ=DAILY"
        assert RecurrenceService.get_preset_rule("weekly") == "FREQ=WEEKLY"
        assert RecurrenceService.get_preset_rule("monthly") == "FREQ=MONTHLY"
        
        # Règles spécifiques
        assert RecurrenceService.get_preset_rule("weekdays") == "FREQ=DAILY;BYDAY=MO,TU,WE,TH,FR"
        assert RecurrenceService.get_preset_rule("weekly_monday") == "FREQ=WEEKLY;BYDAY=MO"
        assert RecurrenceService.get_preset_rule("first_of_month") == "FREQ=MONTHLY;BYMONTHDAY=1"
        
        # Règle inexistante
        assert RecurrenceService.get_preset_rule("inexistant") is None
    
    def test_preset_rules_are_valid(self):
        """Test que toutes les règles prédéfinies sont valides"""
        for name, rule in RecurrenceService.PRESETS.items():
            info = recurrence_service.validate_rrule(rule)
            assert info.is_valid, f"Preset '{name}' with rule '{rule}' is invalid"


class TestRRuleCreation:
    """Tests de création de règles RRULE"""
    
    def test_create_simple_rules(self):
        """Test de création de règles simples"""
        # Quotidien
        rule = RecurrenceService.create_rrule_from_params(frequency="DAILY")
        assert rule == "FREQ=DAILY"
        
        # Hebdomadaire avec intervalle
        rule = RecurrenceService.create_rrule_from_params(
            frequency="WEEKLY",
            interval=2
        )
        assert rule == "FREQ=WEEKLY;INTERVAL=2"
        
        # Avec jours de la semaine
        rule = RecurrenceService.create_rrule_from_params(
            frequency="WEEKLY",
            days_of_week=["MO", "WE", "FR"]
        )
        assert rule == "FREQ=WEEKLY;BYDAY=MO,WE,FR"
    
    def test_create_complex_rules(self):
        """Test de création de règles complexes"""
        # Mensuel le 15
        rule = RecurrenceService.create_rrule_from_params(
            frequency="MONTHLY",
            day_of_month=15
        )
        assert rule == "FREQ=MONTHLY;BYMONTHDAY=15"
        
        # Annuel en janvier et juillet
        rule = RecurrenceService.create_rrule_from_params(
            frequency="YEARLY",
            months=[1, 7]
        )
        assert rule == "FREQ=YEARLY;BYMONTH=1,7"
        
        # Avec limite
        rule = RecurrenceService.create_rrule_from_params(
            frequency="DAILY",
            count=10
        )
        assert rule == "FREQ=DAILY;COUNT=10"
        
        # Avec date de fin
        end_date = date(2024, 12, 31)
        rule = RecurrenceService.create_rrule_from_params(
            frequency="WEEKLY",
            until=end_date
        )
        assert rule == "FREQ=WEEKLY;UNTIL=20241231"


class TestRRuleDescription:
    """Tests de description en langage naturel"""
    
    def test_describe_simple_rules(self):
        """Test de description de règles simples"""
        # Quotidien
        desc = RecurrenceService.describe_rrule("FREQ=DAILY")
        assert desc == "Tous les jours"
        
        # Hebdomadaire
        desc = RecurrenceService.describe_rrule("FREQ=WEEKLY")
        assert desc == "Toutes les semaines"
        
        # Mensuel
        desc = RecurrenceService.describe_rrule("FREQ=MONTHLY")
        assert desc == "Tous les mois"
    
    def test_describe_with_interval(self):
        """Test de description avec intervalle"""
        desc = RecurrenceService.describe_rrule("FREQ=DAILY;INTERVAL=2")
        assert desc == "Tous les 2 jours"
        
        desc = RecurrenceService.describe_rrule("FREQ=WEEKLY;INTERVAL=3")
        assert desc == "Tous les 3 semaines"
    
    def test_describe_with_weekdays(self):
        """Test de description avec jours de la semaine"""
        desc = RecurrenceService.describe_rrule("FREQ=WEEKLY;BYDAY=MO")
        assert "lundi" in desc.lower()
        
        desc = RecurrenceService.describe_rrule("FREQ=WEEKLY;BYDAY=MO,WE,FR")
        assert "lundi" in desc.lower()
        assert "mercredi" in desc.lower()
        assert "vendredi" in desc.lower()
    
    def test_describe_with_monthday(self):
        """Test de description avec jour du mois"""
        desc = RecurrenceService.describe_rrule("FREQ=MONTHLY;BYMONTHDAY=15")
        assert "15 du mois" in desc
        
        desc = RecurrenceService.describe_rrule("FREQ=MONTHLY;BYMONTHDAY=-1")
        assert "dernier jour du mois" in desc
    
    def test_describe_with_limits(self):
        """Test de description avec limites"""
        desc = RecurrenceService.describe_rrule("FREQ=DAILY;COUNT=5")
        assert "5 fois" in desc
        
        desc = RecurrenceService.describe_rrule("FREQ=WEEKLY;UNTIL=20241231")
        assert "jusqu'au" in desc
        assert "31/12/2024" in desc


class TestHolidayHandling:
    """Tests de gestion des jours fériés"""
    
    def test_get_holidays(self):
        """Test de récupération des jours fériés"""
        # Jours fériés français 2024
        holidays_2024 = recurrence_service.get_holidays(2024)
        
        # Vérifier quelques jours fériés connus
        assert date(2024, 1, 1) in holidays_2024  # Jour de l'an
        assert date(2024, 5, 1) in holidays_2024  # Fête du travail
        assert date(2024, 12, 25) in holidays_2024  # Noël
    
    def test_adjust_for_holiday_next_working_day(self):
        """Test d'ajustement au jour ouvré suivant"""
        # 1er janvier 2024 est un lundi férié
        holiday = date(2024, 1, 1)
        adjusted = recurrence_service.adjust_for_holiday(
            holiday,
            strategy="next_working_day"
        )
        
        assert adjusted == date(2024, 1, 2)  # Mardi
    
    def test_adjust_for_holiday_previous_working_day(self):
        """Test d'ajustement au jour ouvré précédent"""
        # 1er mai 2024 est un mercredi férié
        holiday = date(2024, 5, 1)
        adjusted = recurrence_service.adjust_for_holiday(
            holiday,
            strategy="previous_working_day"
        )
        
        assert adjusted == date(2024, 4, 30)  # Mardi
    
    def test_adjust_for_holiday_skip(self):
        """Test d'ignorer un jour férié"""
        holiday = date(2024, 1, 1)
        adjusted = recurrence_service.adjust_for_holiday(
            holiday,
            strategy="skip"
        )
        
        assert adjusted is None
    
    def test_adjust_non_holiday(self):
        """Test d'ajustement d'un jour non férié"""
        regular_day = date(2024, 1, 15)  # Pas un jour férié
        adjusted = recurrence_service.adjust_for_holiday(
            regular_day,
            strategy="next_working_day"
        )
        
        assert adjusted == regular_day  # Pas de changement


class TestSkipSuggestion:
    """Tests de suggestion de saut d'occurrences"""
    
    def test_suggest_skip_until(self):
        """Test de suggestion pour reprendre après un saut"""
        # Pour une règle hebdomadaire
        next_date = recurrence_service.suggest_skip_until(
            "FREQ=WEEKLY",
            current_date=date(2024, 1, 1),  # Lundi
            skip_count=1
        )
        
        assert next_date == date(2024, 1, 8)  # Lundi suivant
        
        # Sauter 3 occurrences
        next_date = recurrence_service.suggest_skip_until(
            "FREQ=DAILY",
            current_date=date(2024, 1, 1),
            skip_count=3
        )
        
        assert next_date == date(2024, 1, 4)  # 3 jours plus tard