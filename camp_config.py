#!/usr/bin/env python3
"""
Camp Power-Up Session Configuration
==================================

This file contains the dynamic camp session information that changes
between different camp offerings throughout the year.

Update this file for each new camp session rather than modifying templates.
LAST UPDATED: 2026-04-06
"""

from datetime import datetime

# Current Camp Session Configuration
CAMP_CONFIG = {
    'age_range': 'K-8th Grade',
    'camp_dates': 'June 15-19, 2026',
    'camp_days': 5,
    'camp_name': 'Camp Power-Up Summer 2026',
    'camp_subtitle': 'A week of gaming fun this summer!',
    'daily_hours': '9:00 AM - 3:00 PM',
    'deposit_due': 'Upon Registration',
    'early_bird_deadline': 'May 15, 2026',
    'final_payment_due': 'June 1, 2026',
    'max_campers': 24,
    'pricing': {
        'new_camper': {
            'deposit': 55,
            'final_payment': 145,
            'total': 200
        },
        'returning_camper': {
            'deposit': 45,
            'final_payment': 125,
            'total': 170
        }
    },
    'registration_open': True,
    'session_type': 'Summer Camp',
    'special_features': [
        'Nintendo Switch Gaming',
        'Retro Gaming Station',
        'Multiplayer Tournaments',
        'Daily Park Time',
        'Prizes & Trophies'
    ],
    'total_hours': 30,
    'waitlist_available': True}

# Dynamic text generation functions
def get_camp_title():
    """Get the formatted camp title."""
    return CAMP_CONFIG["camp_name"]

def get_camp_subtitle():
    """Get the camp subtitle/description."""
    return CAMP_CONFIG["camp_subtitle"]

def get_pricing_text():
    """Generate the pricing information text."""
    returning = CAMP_CONFIG["pricing"]["returning_camper"]
    new = CAMP_CONFIG["pricing"]["new_camper"]
    
    return {
        "returning_text": f"Returning Campers: ${returning['deposit']} deposit + ${returning['final_payment']} final payment = ${returning['total']} total",
        "new_text": f"New Campers: ${new['deposit']} deposit + ${new['final_payment']} final payment = ${new['total']} total",
        "payment_deadline": f"Final payment due before {CAMP_CONFIG['final_payment_due']}. Camp runs {CAMP_CONFIG['camp_dates']}, {CAMP_CONFIG['daily_hours']} daily."
    }

def get_session_summary():
    """Get a complete session summary for admin reference."""
    pricing = get_pricing_text()
    return {
        "title": get_camp_title(),
        "subtitle": get_camp_subtitle(),
        "dates": CAMP_CONFIG["camp_dates"],
        "duration": f"{CAMP_CONFIG['camp_days']} days",
        "daily_schedule": CAMP_CONFIG["daily_hours"],
        "pricing": pricing,
        "features": CAMP_CONFIG.get("special_features", []),
        "status": "Open" if CAMP_CONFIG.get("registration_open", True) else "Closed"
    }

def validate_config():
    """Validate that all required config fields are present."""
    required_fields = ["camp_name", "camp_dates", "camp_days", "daily_hours", "pricing"]
    missing_fields = []
    
    for field in required_fields:
        if field not in CAMP_CONFIG or not CAMP_CONFIG[field]:
            missing_fields.append(field)
    
    if missing_fields:
        raise ValueError(f"Missing required config fields: {missing_fields}")
    
    # Validate pricing structure
    for camper_type in ["returning_camper", "new_camper"]:
        pricing = CAMP_CONFIG["pricing"][camper_type]
        total = pricing["deposit"] + pricing["final_payment"]
        if total != pricing["total"]:
            raise ValueError(f"Pricing calculation error for {camper_type}: {total} != {pricing['total']}")
    
    return True
