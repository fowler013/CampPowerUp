# 🏕️ Sample Camp Configuration
# Copy this file to create your own camp_config.py

# =============================================================================
# CAMP IDENTITY & BRANDING
# =============================================================================

CAMP_NAME = "Adventure Valley Summer Camp"
CAMP_TAGLINE = "Where Every Day is an Adventure!"
CAMP_YEAR = "2025"

# Contact Information
CAMP_CONTACT = {
    'address': '123 Forest Trail, Adventure Valley, CA 90210',
    'phone': '(555) 123-CAMP',
    'email': 'info@adventurevalley.com',
    'website': 'www.adventurevalley.com'
}

# Visual Branding
CAMP_COLORS = {
    'primary': '#2E7D32',        # Forest Green
    'secondary': '#FFA726',      # Sunset Orange  
    'accent': '#1976D2',         # Sky Blue
    'background': '#F1F8E9',     # Light Green
    'text': '#1B5E20',           # Dark Green
    'white': '#FFFFFF'
}

CAMP_LOGO = {
    'url': '/static/images/adventure_valley_logo.png',
    'alt_text': 'Adventure Valley Summer Camp',
    'width': '200px',
    'height': '80px'
}

# =============================================================================
# CAMP SESSIONS & SCHEDULING
# =============================================================================

CAMP_SESSIONS = {
    'explorers_week': {
        'name': 'Nature Explorers Week',
        'dates': 'June 15-19, 2025',
        'theme': 'Discover the wonders of nature!',
        'age_groups': ['little_explorers', 'junior_adventurers'],
        'capacity': 50,
        'price': 275.00
    },
    'adventure_week': {
        'name': 'Outdoor Adventure Week', 
        'dates': 'June 22-26, 2025',
        'theme': 'Challenge yourself with outdoor activities!',
        'age_groups': ['junior_adventurers', 'senior_scouts'],
        'capacity': 40,
        'price': 300.00
    },
    'stem_week': {
        'name': 'STEM Discovery Week',
        'dates': 'June 29-July 3, 2025', 
        'theme': 'Science, Technology, Engineering & Math fun!',
        'age_groups': ['junior_adventurers', 'senior_scouts', 'teen_leaders'],
        'capacity': 35,
        'price': 325.00
    },
    'leadership_week': {
        'name': 'Teen Leadership Camp',
        'dates': 'July 6-10, 2025',
        'theme': 'Develop leadership skills while having fun!',
        'age_groups': ['teen_leaders'],
        'capacity': 20,
        'price': 350.00
    }
}

# Age Group Definitions
AGE_GROUPS = {
    'little_explorers': {
        'name': 'Little Explorers',
        'min_age': 4,
        'max_age': 6,
        'description': 'Perfect for our youngest adventurers!',
        'counselor_ratio': 4  # 4 kids per counselor
    },
    'junior_adventurers': {
        'name': 'Junior Adventurers', 
        'min_age': 7,
        'max_age': 9,
        'description': 'Ready for bigger adventures!',
        'counselor_ratio': 6
    },
    'senior_scouts': {
        'name': 'Senior Scouts',
        'min_age': 10,
        'max_age': 12, 
        'description': 'Independent explorers seeking challenges!',
        'counselor_ratio': 8
    },
    'teen_leaders': {
        'name': 'Teen Leaders',
        'min_age': 13,
        'max_age': 15,
        'description': 'Future camp counselors in training!',
        'counselor_ratio': 10
    }
}

# Daily Schedule
DAILY_SCHEDULE = {
    'drop_off': {'time': '8:00 AM - 9:00 AM', 'activity': 'Arrival & Free Play'},
    'morning_circle': {'time': '9:00 AM - 9:15 AM', 'activity': 'Morning Circle Time'},
    'activity_1': {'time': '9:15 AM - 10:30 AM', 'activity': 'Morning Adventure'},
    'snack': {'time': '10:30 AM - 10:45 AM', 'activity': 'Snack Break'},
    'activity_2': {'time': '10:45 AM - 12:00 PM', 'activity': 'Exploration Time'},
    'lunch': {'time': '12:00 PM - 1:00 PM', 'activity': 'Lunch & Rest'},
    'activity_3': {'time': '1:00 PM - 2:15 PM', 'activity': 'Afternoon Adventure'},
    'reflection': {'time': '2:15 PM - 2:30 PM', 'activity': 'Reflection Circle'},
    'pickup': {'time': '2:30 PM - 3:00 PM', 'activity': 'Pickup & Goodbyes'}
}

# =============================================================================
# ACTIVITIES & PROGRAMMING
# =============================================================================

ACTIVITY_CATEGORIES = {
    'nature': {
        'name': 'Nature & Outdoor',
        'icon': '🌲',
        'color': '#4CAF50'
    },
    'arts': {
        'name': 'Arts & Crafts',
        'icon': '🎨', 
        'color': '#E91E63'
    },
    'science': {
        'name': 'Science & STEM',
        'icon': '🔬',
        'color': '#2196F3'
    },
    'sports': {
        'name': 'Sports & Games',
        'icon': '⚽',
        'color': '#FF9800'
    },
    'cooking': {
        'name': 'Cooking & Nutrition',
        'icon': '👩‍🍳',
        'color': '#795548'
    },
    'team_building': {
        'name': 'Team Building',
        'icon': '🤝',
        'color': '#9C27B0'
    }
}

# Custom Activities for Adventure Valley
CUSTOM_ACTIVITIES = [
    {
        'name': 'Nature Detective Challenge',
        'category': 'nature',
        'age_groups': ['little_explorers', 'junior_adventurers'],
        'duration': 45,
        'materials': ['magnifying glasses', 'field notebooks', 'collection bags'],
        'description': 'Become nature detectives and solve outdoor mysteries!',
        'learning_objectives': ['observation skills', 'nature awareness', 'problem solving']
    },
    {
        'name': 'Build a Bug Hotel',
        'category': 'nature',
        'age_groups': ['junior_adventurers', 'senior_scouts'],
        'duration': 60,
        'materials': ['bamboo tubes', 'pine cones', 'wooden blocks', 'drill'],
        'description': 'Create homes for beneficial insects in our garden!',
        'learning_objectives': ['ecosystem understanding', 'construction skills', 'environmental stewardship']
    },
    {
        'name': 'Volcano Eruption Lab',
        'category': 'science',
        'age_groups': ['junior_adventurers', 'senior_scouts', 'teen_leaders'],
        'duration': 90,
        'materials': ['baking soda', 'vinegar', 'food coloring', 'modeling clay'],
        'description': 'Create explosive science experiments!',
        'learning_objectives': ['chemical reactions', 'scientific method', 'hypothesis testing']
    },
    {
        'name': 'Camp Fire Cooking',
        'category': 'cooking',
        'age_groups': ['senior_scouts', 'teen_leaders'],
        'duration': 120,
        'materials': ['camp stove', 'cooking utensils', 'ingredients'],
        'description': 'Learn outdoor cooking skills and make delicious meals!',
        'learning_objectives': ['cooking skills', 'nutrition awareness', 'outdoor safety']
    }
]

# =============================================================================
# REGISTRATION & POLICIES
# =============================================================================

REGISTRATION_FIELDS = {
    'required': [
        'camper_first_name',
        'camper_last_name', 
        'camper_age',
        'parent_name',
        'parent_email',
        'parent_phone',
        'emergency_contact_name',
        'emergency_contact_phone',
        'selected_session'
    ],
    'optional': [
        'camper_nickname',
        'dietary_restrictions',
        'medical_conditions',
        'medications',
        'swimming_ability',
        'special_instructions',
        'how_did_you_hear'
    ]
}

# Policies & Important Information
CAMP_POLICIES = {
    'drop_off_pickup': {
        'title': 'Drop-off & Pickup Policy',
        'content': 'Please arrive during designated times. Late pickup fees may apply after 3:15 PM.'
    },
    'what_to_bring': {
        'title': 'What to Bring Daily',
        'content': [
            'Water bottle (labeled with name)',
            'Packed lunch and snack',
            'Sunscreen (SPF 30+)',
            'Hat or cap',
            'Comfortable closed-toe shoes',
            'Extra clothes in a labeled bag'
        ]
    },
    'weather_policy': {
        'title': 'Weather Policy', 
        'content': 'Camp runs rain or shine! We have indoor backup activities for severe weather.'
    },
    'medication_policy': {
        'title': 'Medication Policy',
        'content': 'All medications must be in original containers with dosage instructions.'
    }
}

# =============================================================================
# COMMUNICATION SETTINGS
# =============================================================================

EMAIL_TEMPLATES = {
    'welcome': {
        'subject': 'Welcome to Adventure Valley Summer Camp!',
        'template': '''
        Dear [PARENT_NAME],
        
        We're thrilled to welcome [CAMPER_NAME] to Adventure Valley Summer Camp!
        
        Your child is registered for: [SESSION_NAME]
        Dates: [SESSION_DATES]
        
        Important reminders:
        • Drop-off: 8:00-9:00 AM
        • Pickup: 2:30-3:00 PM  
        • Please pack lunch, snack, and water bottle daily
        • Don't forget sunscreen and hat!
        
        We can't wait to start this adventure together!
        
        The Adventure Valley Team
        '''
    },
    'daily_update': {
        'subject': '[CAMPER_NAME]\'s Adventure Today!',
        'template': '''
        Hi [PARENT_NAME]!
        
        [CAMPER_NAME] had an amazing day at Adventure Valley!
        
        Today's highlights:
        • [ACTIVITY_1]
        • [ACTIVITY_2] 
        • [SPECIAL_MOMENT]
        
        Tomorrow we'll be: [TOMORROW_PREVIEW]
        
        Have a great evening!
        Adventure Valley Staff
        '''
    }
}

SMS_TEMPLATES = {
    'pickup_reminder': 'Hi! Pickup for [CAMPER_NAME] is 2:30-3:00 PM today at Adventure Valley. Thanks!',
    'weather_alert': 'Weather update: Activities may move indoors today. [CAMPER_NAME] should bring a light jacket!',
    'late_pickup': 'This is a reminder that [CAMPER_NAME] is still at camp. Please arrange pickup ASAP. Late fees may apply.'
}

# =============================================================================
# STAFF & ADMINISTRATIVE SETTINGS  
# =============================================================================

STAFF_ROLES = {
    'camp_director': {
        'title': 'Camp Director',
        'permissions': ['all_access'],
        'description': 'Full administrative access to all systems'
    },
    'program_coordinator': {
        'title': 'Program Coordinator', 
        'permissions': ['activities', 'registration', 'communication'],
        'description': 'Manages daily programs and parent communication'
    },
    'lead_counselor': {
        'title': 'Lead Counselor',
        'permissions': ['activities', 'attendance', 'basic_communication'],
        'description': 'Supervises activities and tracks attendance'
    },
    'assistant_counselor': {
        'title': 'Assistant Counselor',
        'permissions': ['activities', 'attendance'],
        'description': 'Assists with daily activities and camper supervision'
    }
}

# Emergency Contacts
EMERGENCY_CONTACTS = {
    'camp_director': {
        'name': 'Sarah Johnson',
        'phone': '(555) 123-CAMP',
        'email': 'sarah@adventurevalley.com'
    },
    'nurse': {
        'name': 'Nurse Linda',
        'phone': '(555) 123-HEAL',
        'email': 'nurse@adventurevalley.com'
    },
    'local_emergency': {
        'police': '911',
        'fire': '911', 
        'hospital': 'Valley General Hospital - (555) 123-HELP'
    }
}

# =============================================================================
# SYSTEM CONFIGURATION
# =============================================================================

# Database Settings
DATABASE_CONFIG = {
    'registration_db': 'registration_submissions.db',
    'security_db': 'security.db',
    'camp_db': 'data/camp.db',
    'communication_db': 'communication/communication.db'
}

# Security Settings
SECURITY_CONFIG = {
    'session_timeout_minutes': 30,
    'password_min_length': 8,
    'max_login_attempts': 3,
    'lockout_duration_minutes': 15,
    'require_password_change_days': 90
}

# Backup Settings
BACKUP_CONFIG = {
    'auto_backup_enabled': True,
    'backup_frequency_hours': 24,
    'backup_retention_days': 30,
    'backup_location': './backups/'
}

# =============================================================================
# EXTERNAL INTEGRATIONS
# =============================================================================

# Email Configuration (Add to .env file)
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',  # Or your email provider
    'smtp_port': 587,
    'use_tls': True,
    'from_name': 'Adventure Valley Summer Camp'
    # Add SMTP_USERNAME and SMTP_PASSWORD to .env file
}

# SMS Configuration (Add to .env file) 
SMS_CONFIG = {
    'provider': 'twilio',  # or 'vonage', 'textmagic'
    'from_name': 'Adventure Valley'
    # Add TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER to .env file
}

# Photo Sharing (Optional)
PHOTO_CONFIG = {
    'enabled': True,
    'provider': 'google_photos',  # or 'shutterfly', 'smugmug'
    'album_naming': '[CAMP_NAME] - [SESSION_NAME] - [DATE]',
    'auto_upload': False  # Manual upload for privacy
}

# =============================================================================
# CUSTOMIZATION NOTES
# =============================================================================

"""
To customize this configuration for your camp:

1. Update CAMP_NAME, CAMP_TAGLINE, and CAMP_CONTACT with your information
2. Modify CAMP_SESSIONS to match your schedule and pricing
3. Adjust AGE_GROUPS for your camper demographics  
4. Add your custom activities to CUSTOM_ACTIVITIES
5. Update EMAIL_TEMPLATES and SMS_TEMPLATES with your messaging
6. Configure STAFF_ROLES based on your team structure
7. Set up EMAIL_CONFIG and SMS_CONFIG with your provider details
8. Review and update all policies in CAMP_POLICIES

Remember to:
- Test all changes in development first
- Keep backups of your configuration files
- Update documentation when making changes
- Train staff on any new features or processes
"""
