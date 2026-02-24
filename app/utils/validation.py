import re
from typing import Tuple


class ValidationService:
    def __init__(self):
        self.email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        self.disposable_domains = {
            'tempmail.com', 'mailinator.com', '10minutemail.com', 'guerrillamail.com',
            'throwaway.email', 'temp-mail.org', 'yopmail.com', 'maildrop.cc',
            'getairmail.com', '20minutemail.com', 'tempmail.net', 'mailnesia.com'
        }

    def validate_email_format(self, email: str) -> Tuple[bool, str]:
        """Validate email format using regex"""
        if not self.email_pattern.match(email):
            return False, "Invalid email format"
        return True, ""

    def validate_disposable_email(self, email: str) -> Tuple[bool, str]:
        """Check if email is from a disposable email service"""
        domain = email.split('@')[1].lower()
        if domain in self.disposable_domains:
            return False, "Disposable email addresses are not allowed"
        return True, ""

    def validate_player_name(self, name: str) -> Tuple[bool, str]:
        """Validate player name"""
        if not name or len(name.strip()) < 1:
            return False, "Player name cannot be empty"
        if len(name.strip()) > 50:
            return False, "Player name too long (max 50 characters)"
        return True, ""

    def validate_game_setup(self, player_names: list, score_cutoff: int) -> Tuple[bool, str]:
        """Validate game setup parameters"""
        if len(player_names) < 2:
            return False, "At least 2 players are required"
        if len(player_names) > 8:
            return False, "Maximum 8 players allowed"
        
        # Check for duplicate names
        clean_names = [name.strip().lower() for name in player_names]
        if len(set(clean_names)) != len(clean_names):
            return False, "Player names must be unique"
        
        # Validate each name
        for name in player_names:
            is_valid, error = self.validate_player_name(name)
            if not is_valid:
                return False, error
        
        # Validate score cutoff
        if not isinstance(score_cutoff, int) or score_cutoff <= 0:
            return False, "Score cutoff must be a positive number"
        
        return True, ""


validation_service = ValidationService()