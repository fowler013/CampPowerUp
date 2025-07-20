#!/usr/bin/env python3
"""
Camp Power-Up Session Configuration
==================================

This file contains the dynamic camp session information that changes
between different camp offerings throughout the year.

Update this file for each new camp session rather than modifying templates.
"""

from datetime import datetime

# Current Camp Session Configuration
CAMP_CONFIG = {
    # Camp Identity
    "camp_name": "Camp Power-Up 2025",
    "camp_subtitle": "Gaming Camp Registration Form",
    
    # Session Details
    "camp_dates": "June 9th-13th",  # Update for each session
    "camp_days": 5,  # Number of camp days (3, 4, 5, etc.)
    "daily_hours": "10am-3pm",
    "total_hours": 25,  # Calculated: days * hours_per_day
    
    # Pricing Structure
    "pricing": {
        "returning_camper": {
            "deposit": 50,
            "final_payment": 130,
            "total": 180
        },
        "new_camper": {
            "deposit": 50,
            "final_payment": 150,
            "total": 200
        }
    },
    
    # Payment Deadlines
    "deposit_due": "Upon Registration",
    "final_payment_due": "June 8th",  # Usually day before camp starts
    
    # Session-specific Details
    "session_type": "Summer Intensive",  # Summer Intensive, Spring Break, Holiday, etc.
    "age_range": "5-18",
    "max_campers": 24,
    
    # Features for this session
    "special_features": [
        "Nintendo Switch Gaming",
        "Board Game Library",
        "Team Building Activities",
        "Daily Tournaments"
    ],
    
    # Registration Status
    "registration_open": True,
    "early_bird_deadline": None,  # Set if there's an early bird discount
    "waitlist_available": True
}

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
        "features": CAMP_CONFIG["special_features"],
        "status": "Open" if CAMP_CONFIG["registration_open"] else "Closed"
    }

# Validation functions
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

# Example configurations for different sessions
SAMPLE_CONFIGS = {
    "summer_5_day": {
        "camp_name": "Camp Power-Up 2025 - Summer Session",
        "camp_dates": "June 9th-13th",
        "camp_days": 5,
        "daily_hours": "10am-3pm",
        "pricing": {
            "returning_camper": {"deposit": 50, "final_payment": 130, "total": 180},
            "new_camper": {"deposit": 50, "final_payment": 150, "total": 200}
        }
    },
    
    "spring_break_3_day": {
        "camp_name": "Camp Power-Up 2025 - Spring Break",
        "camp_dates": "March 15th-17th",
        "camp_days": 3,
        "daily_hours": "9am-2pm",
        "pricing": {
            "returning_camper": {"deposit": 40, "final_payment": 80, "total": 120},
            "new_camper": {"deposit": 40, "final_payment": 95, "total": 135}
        }
    },
    
    "holiday_4_day": {
        "camp_name": "Camp Power-Up 2025 - Holiday Gaming",
        "camp_dates": "December 26th-29th",
        "camp_days": 4,
        "daily_hours": "10am-3pm",
        "pricing": {
            "returning_camper": {"deposit": 45, "final_payment": 105, "total": 150},
            "new_camper": {"deposit": 45, "final_payment": 120, "total": 165}
        }
    }
}

def load_session_config(session_name):
    """Load a predefined session configuration."""
    if session_name in SAMPLE_CONFIGS:
        global CAMP_CONFIG
        CAMP_CONFIG.update(SAMPLE_CONFIGS[session_name])
        return True
    return False

if __name__ == "__main__":
    # Test the configuration
    try:
        validate_config()
        print("✅ Configuration is valid!")
        
        summary = get_session_summary()
        print(f"\n🏕️ Current Session: {summary['title']}")
        print(f"📅 Dates: {summary['dates']}")
        print(f"⏰ Duration: {summary['duration']} ({summary['daily_schedule']})")
        print(f"💰 Pricing:")
        print(f"   • {summary['pricing']['returning_text']}")
        print(f"   • {summary['pricing']['new_text']}")
        print(f"📝 {summary['pricing']['payment_deadline']}")
        
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
