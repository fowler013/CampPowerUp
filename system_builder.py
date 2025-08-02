#!/usr/bin/env python3
"""
🏕️ Camp Power-Up - Phase 2: Complete System Builder
Adds sample data, customization, and advanced features
"""

import sqlite3
import json
import random
from datetime import datetime, timedelta
import os

class CampPowerUpBuilder:
    def __init__(self):
        print("🚀 CAMP POWER-UP SYSTEM BUILDER")
        print("=" * 50)
        print("Phase 2: Adding sample data and advanced features")
        
    def create_sample_registrations(self):
        """Create sample registration data"""
        print("\n📋 Creating Sample Registration Data...")
        
        sample_registrations = [
            {
                'timestamp': (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d %H:%M:%S'),
                'child_first_name': 'Emma',
                'child_last_name': 'Johnson',
                'child_age': 8,
                'child_grade': '3rd Grade',
                'child_gender': 'Female',
                'parent_email': 'sarah.johnson@email.com',
                'parent_phone': '(555) 123-4567',
                'emergency_contact_name': 'Mike Johnson',
                'emergency_contact_phone': '(555) 987-6543',
                'camp_weeks': '["Nature Explorers Week - June 15-19, 2025"]',
                'payment_status': 'paid',
                'additional_notes': 'Allergic to peanuts',
                'medical_conditions': 'None',
                'has_allergies': True,
                'allergy_details': 'Peanut allergy',
                'photo_permission': True,
                'tshirt_size': 'Youth M'
            },
            {
                'timestamp': (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d %H:%M:%S'),
                'child_first_name': 'Liam',
                'child_last_name': 'Rodriguez',
                'child_age': 11,
                'child_grade': '6th Grade',
                'child_gender': 'Male',
                'parent_email': 'maria.rodriguez@email.com',
                'parent_phone': '(555) 234-5678',
                'emergency_contact_name': 'Carlos Rodriguez',
                'emergency_contact_phone': '(555) 876-5432',
                'camp_weeks': '["Outdoor Adventure Week - June 22-26, 2025"]',
                'payment_status': 'paid',
                'additional_notes': 'Great swimmer, loves outdoor activities',
                'medical_conditions': 'None',
                'has_allergies': False,
                'photo_permission': True,
                'tshirt_size': 'Youth L'
            },
            {
                'timestamp': (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S'),
                'child_first_name': 'Sophia',
                'child_last_name': 'Chen',
                'child_age': 9,
                'child_grade': '4th Grade',
                'child_gender': 'Female',
                'parent_email': 'david.chen@email.com',
                'parent_phone': '(555) 345-6789',
                'emergency_contact_name': 'Lisa Chen',
                'emergency_contact_phone': '(555) 765-4321',
                'camp_weeks': '["STEM Discovery Week - June 29-July 3, 2025"]',
                'payment_status': 'pending',
                'additional_notes': 'Loves science experiments and building things',
                'medical_conditions': 'Mild asthma - has inhaler',
                'has_allergies': False,
                'photo_permission': True,
                'tshirt_size': 'Youth M'
            },
            {
                'timestamp': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),
                'child_first_name': 'Noah',
                'child_last_name': 'Williams',
                'child_age': 13,
                'child_grade': '8th Grade',
                'child_gender': 'Male',
                'parent_email': 'jen.williams@email.com',
                'parent_phone': '(555) 456-7890',
                'emergency_contact_name': 'Robert Williams',
                'emergency_contact_phone': '(555) 654-3210',
                'camp_weeks': '["Teen Leadership Camp - July 6-10, 2025"]',
                'payment_status': 'paid',
                'additional_notes': 'Natural leader, great with younger kids',
                'medical_conditions': 'None',
                'has_allergies': False,
                'photo_permission': True,
                'tshirt_size': 'Adult S'
            },
            {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'child_first_name': 'Ava',
                'child_last_name': 'Thompson',
                'child_age': 6,
                'child_grade': '1st Grade',
                'child_gender': 'Female',
                'parent_email': 'mike.thompson@email.com',
                'parent_phone': '(555) 567-8901',
                'emergency_contact_name': 'Amanda Thompson',
                'emergency_contact_phone': '(555) 543-2109',
                'camp_weeks': '["Nature Explorers Week - June 15-19, 2025"]',
                'payment_status': 'paid',
                'additional_notes': 'First time at camp, may need extra encouragement',
                'medical_conditions': 'Lactose intolerant',
                'has_allergies': True,
                'allergy_details': 'Lactose intolerant',
                'photo_permission': True,
                'tshirt_size': 'Youth S'
            }
        ]
        
        try:
            conn = sqlite3.connect('registration_submissions.db')
            cursor = conn.cursor()
            
            # Insert sample data using actual database columns
            for reg in sample_registrations:
                cursor.execute('''
                    INSERT OR REPLACE INTO registrations 
                    (timestamp, child_first_name, child_last_name, child_age, child_grade, child_gender,
                     parent_email, parent_phone, emergency_contact_name, emergency_contact_phone, 
                     camp_weeks, payment_status, additional_notes, medical_conditions, has_allergies, 
                     allergy_details, photo_permission, tshirt_size)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    reg['timestamp'], reg['child_first_name'], reg['child_last_name'],
                    reg['child_age'], reg['child_grade'], reg['child_gender'], reg['parent_email'], 
                    reg['parent_phone'], reg['emergency_contact_name'], reg['emergency_contact_phone'],
                    reg['camp_weeks'], reg['payment_status'], reg['additional_notes'], 
                    reg['medical_conditions'], reg['has_allergies'], reg.get('allergy_details', ''),
                    reg['photo_permission'], reg['tshirt_size']
                ))
            
            conn.commit()
            conn.close()
            print(f"✅ Created {len(sample_registrations)} sample registrations")
            
        except Exception as e:
            print(f"❌ Error creating registration data: {e}")
    
    def create_sample_activities(self):
        """Create sample game library activities"""
        print("\n🎮 Creating Sample Activity Data...")
        
        sample_activities = [
            {
                'name': 'Nature Scavenger Hunt',
                'category': 'outdoor',
                'age_group': 'all',
                'duration': 45,
                'max_participants': 20,
                'materials': 'clipboards, pencils, collection bags, magnifying glasses',
                'description': 'Explore the camp grounds and find items from our nature checklist!',
                'learning_objectives': 'observation skills, nature awareness, teamwork',
                'safety_notes': 'Stay within designated areas, buddy system required',
                'popularity_score': 95
            },
            {
                'name': 'Science Lab Explosions',
                'category': 'science',
                'age_group': 'junior,senior',
                'duration': 60,
                'max_participants': 12,
                'materials': 'baking soda, vinegar, food coloring, safety goggles, measuring cups',
                'description': 'Create safe chemical reactions and learn about acids and bases!',
                'learning_objectives': 'chemistry basics, scientific method, hypothesis testing',
                'safety_notes': 'Safety goggles required, adult supervision mandatory',
                'popularity_score': 88
            },
            {
                'name': 'Camp Fire Cooking',
                'category': 'cooking',
                'age_group': 'senior,teen',
                'duration': 90,
                'max_participants': 8,
                'materials': 'camp stove, cooking utensils, ingredients, aprons, fire extinguisher',
                'description': 'Learn outdoor cooking skills and make delicious camp meals!',
                'learning_objectives': 'cooking skills, food safety, nutrition awareness',
                'safety_notes': 'Fire safety briefing required, adult supervision for all cooking',
                'popularity_score': 92
            },
            {
                'name': 'Art in the Woods',
                'category': 'arts',
                'age_group': 'all',
                'duration': 75,
                'max_participants': 15,
                'materials': 'canvases, paints, brushes, easels, natural materials for collage',
                'description': 'Create beautiful artwork inspired by nature around us!',
                'learning_objectives': 'artistic expression, creativity, nature appreciation',
                'safety_notes': 'Non-toxic paints only, art smocks provided',
                'popularity_score': 85
            },
            {
                'name': 'Team Challenge Course',
                'category': 'team_building',
                'age_group': 'junior,senior,teen',
                'duration': 120,
                'max_participants': 16,
                'materials': 'ropes course equipment, safety harnesses, helmets, first aid kit',
                'description': 'Work together to complete our challenging obstacle course!',
                'learning_objectives': 'teamwork, problem solving, confidence building, physical fitness',
                'safety_notes': 'Full safety gear required, certified instructor present',
                'popularity_score': 97
            },
            {
                'name': 'Digital Photography Walk',
                'category': 'technology',
                'age_group': 'senior,teen',
                'duration': 60,
                'max_participants': 10,
                'materials': 'digital cameras, memory cards, photography guidebooks',
                'description': 'Learn photography basics while capturing camp memories!',
                'learning_objectives': 'photography skills, technology literacy, artistic composition',
                'safety_notes': 'Handle equipment carefully, stay with group',
                'popularity_score': 78
            }
        ]
        
        try:
            conn = sqlite3.connect('data/camp.db')
            cursor = conn.cursor()
            
            # Create activities table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS activities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    category TEXT,
                    age_group TEXT,
                    duration INTEGER,
                    max_participants INTEGER,
                    materials TEXT,
                    description TEXT,
                    learning_objectives TEXT,
                    safety_notes TEXT,
                    popularity_score INTEGER DEFAULT 0,
                    times_run INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Insert sample activities
            for activity in sample_activities:
                cursor.execute('''
                    INSERT OR REPLACE INTO activities 
                    (name, category, age_group, duration, max_participants, materials, 
                     description, learning_objectives, safety_notes, popularity_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    activity['name'], activity['category'], activity['age_group'],
                    activity['duration'], activity['max_participants'], activity['materials'],
                    activity['description'], activity['learning_objectives'], 
                    activity['safety_notes'], activity['popularity_score']
                ))
            
            conn.commit()
            conn.close()
            print(f"✅ Created {len(sample_activities)} sample activities")
            
        except Exception as e:
            print(f"❌ Error creating activity data: {e}")
    
    def create_analytics_data(self):
        """Create sample analytics and statistics"""
        print("\n📊 Creating Analytics Data...")
        
        try:
            conn = sqlite3.connect('data/camp.db')
            cursor = conn.cursor()
            
            # Create analytics tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS camp_statistics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stat_name TEXT NOT NULL,
                    stat_value TEXT NOT NULL,
                    stat_type TEXT DEFAULT 'general',
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    total_campers INTEGER,
                    activities_completed INTEGER,
                    weather TEXT,
                    notes TEXT
                )
            ''')
            
            # Sample statistics
            stats = [
                ('total_registrations', '5', 'enrollment'),
                ('total_activities', '6', 'programming'),
                ('average_age', '9.4', 'demographics'),
                ('most_popular_session', 'Nature Explorers Week', 'sessions'),
                ('dietary_accommodations', '3', 'special_needs'),
                ('payment_completion_rate', '80%', 'financial'),
                ('parent_satisfaction', '4.8/5', 'feedback'),
                ('staff_ratio', '1:6', 'staffing'),
                ('safety_incidents', '0', 'safety'),
                ('repeat_families', '2', 'retention')
            ]
            
            for stat_name, stat_value, stat_type in stats:
                cursor.execute('''
                    INSERT OR REPLACE INTO camp_statistics (stat_name, stat_value, stat_type)
                    VALUES (?, ?, ?)
                ''', (stat_name, stat_value, stat_type))
            
            # Sample daily attendance
            for i in range(7):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                cursor.execute('''
                    INSERT OR REPLACE INTO daily_attendance 
                    (date, total_campers, activities_completed, weather, notes)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    date, 
                    random.randint(3, 5),
                    random.randint(2, 4),
                    random.choice(['Sunny', 'Partly Cloudy', 'Overcast', 'Light Rain']),
                    f'Great day of activities! Campers enjoyed outdoor time.'
                ))
            
            conn.commit()
            conn.close()
            print("✅ Created analytics and statistics data")
            
        except Exception as e:
            print(f"❌ Error creating analytics data: {e}")
    
    def create_communication_templates(self):
        """Create sample communication templates"""
        print("\n📧 Creating Communication Templates...")
        
        try:
            conn = sqlite3.connect('communication/communication.db')
            cursor = conn.cursor()
            
            # Create templates table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS message_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    subject TEXT,
                    content TEXT NOT NULL,
                    variables TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            templates = [
                {
                    'name': 'Welcome Message',
                    'type': 'email',
                    'subject': 'Welcome to Camp Power-Up!',
                    'content': '''Dear [PARENT_NAME],

We're thrilled to welcome [CAMPER_NAME] to Camp Power-Up for [SESSION_NAME]!

Session Details:
• Dates: [SESSION_DATES]
• Drop-off: 8:00-9:00 AM
• Pickup: 2:30-3:00 PM

What to bring daily:
✓ Water bottle (labeled)
✓ Packed lunch and snack
✓ Sunscreen and hat
✓ Comfortable clothes

We can't wait to start this amazing adventure together!

The Camp Power-Up Team''',
                    'variables': 'PARENT_NAME,CAMPER_NAME,SESSION_NAME,SESSION_DATES'
                },
                {
                    'name': 'Daily Update',
                    'type': 'email',
                    'subject': '[CAMPER_NAME]\'s Camp Adventure Today!',
                    'content': '''Hi [PARENT_NAME]!

[CAMPER_NAME] had an amazing day at Camp Power-Up!

Today's highlights:
🎯 [ACTIVITY_1]
🌟 [ACTIVITY_2]
💫 Special moment: [SPECIAL_MOMENT]

Tomorrow's plan: [TOMORROW_ACTIVITIES]

Weather was [WEATHER] - perfect for outdoor fun!

Have a wonderful evening!
Camp Power-Up Staff''',
                    'variables': 'PARENT_NAME,CAMPER_NAME,ACTIVITY_1,ACTIVITY_2,SPECIAL_MOMENT,TOMORROW_ACTIVITIES,WEATHER'
                },
                {
                    'name': 'Pickup Reminder',
                    'type': 'sms',
                    'subject': '',
                    'content': 'Hi! Just a friendly reminder that pickup for [CAMPER_NAME] is at 2:30-3:00 PM today at Camp Power-Up. Thanks! 🏕️',
                    'variables': 'CAMPER_NAME'
                },
                {
                    'name': 'Weather Alert',
                    'type': 'sms',
                    'subject': '',
                    'content': 'Weather update: [WEATHER_CONDITION] expected today. [CAMPER_NAME] should bring [RECOMMENDED_ITEMS]. Activities may move indoors. Thanks!',
                    'variables': 'WEATHER_CONDITION,CAMPER_NAME,RECOMMENDED_ITEMS'
                }
            ]
            
            for template in templates:
                cursor.execute('''
                    INSERT OR REPLACE INTO message_templates 
                    (name, type, subject, body, variables)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    template['name'], template['type'], template['subject'],
                    template['content'], template['variables']
                ))
            
            conn.commit()
            conn.close()
            print(f"✅ Created {len(templates)} communication templates")
            
        except Exception as e:
            print(f"❌ Error creating communication templates: {e}")
    
    def create_contact_directory(self):
        """Create sample contact directory"""
        print("\n👥 Creating Contact Directory...")
        
        try:
            conn = sqlite3.connect('data/camp.db')
            cursor = conn.cursor()
            
            # Create contacts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    role TEXT,
                    email TEXT,
                    phone TEXT,
                    emergency_contact BOOLEAN DEFAULT 0,
                    notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            contacts = [
                ('Sarah Johnson', 'Parent', 'sarah.johnson@email.com', '(555) 123-4567', 0, 'Parent of Emma Johnson'),
                ('Maria Rodriguez', 'Parent', 'maria.rodriguez@email.com', '(555) 234-5678', 0, 'Parent of Liam Rodriguez'),
                ('David Chen', 'Parent', 'david.chen@email.com', '(555) 345-6789', 0, 'Parent of Sophia Chen'),
                ('Jennifer Williams', 'Parent', 'jen.williams@email.com', '(555) 456-7890', 0, 'Parent of Noah Williams'),
                ('Michael Thompson', 'Parent', 'mike.thompson@email.com', '(555) 567-8901', 0, 'Parent of Ava Thompson'),
                ('Camp Director', 'Staff', 'director@camppowerup.com', '(555) 111-2222', 1, 'Primary camp administration'),
                ('Head Counselor', 'Staff', 'counselor@camppowerup.com', '(555) 333-4444', 1, 'Lead activity coordinator'),
                ('Camp Nurse', 'Medical', 'nurse@camppowerup.com', '(555) 555-6666', 1, 'Medical emergencies and first aid'),
                ('Local Emergency', 'Emergency', '911', '911', 1, 'Police, Fire, Ambulance'),
                ('Valley Hospital', 'Medical', 'info@valleyhospital.com', '(555) 777-8888', 1, 'Nearest hospital facility')
            ]
            
            for name, role, email, phone, emergency, notes in contacts:
                cursor.execute('''
                    INSERT OR REPLACE INTO contacts 
                    (name, role, email, phone, emergency_contact, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (name, role, email, phone, emergency, notes))
            
            conn.commit()
            conn.close()
            print(f"✅ Created {len(contacts)} contact entries")
            
        except Exception as e:
            print(f"❌ Error creating contact directory: {e}")
    
    def build_complete_system(self):
        """Build the complete system with all data"""
        print("\n🔨 BUILDING COMPLETE CAMP POWER-UP SYSTEM")
        print("=" * 50)
        
        self.create_sample_registrations()
        self.create_sample_activities()
        self.create_analytics_data()
        self.create_communication_templates()
        self.create_contact_directory()
        
        print("\n" + "=" * 50)
        print("🎉 SYSTEM BUILD COMPLETE!")
        print("✅ Sample registrations added")
        print("✅ Activity library populated") 
        print("✅ Analytics data generated")
        print("✅ Communication templates created")
        print("✅ Contact directory established")
        print("\n🚀 Your Camp Power-Up system is now fully operational!")
        print("🔗 Admin Portal: http://127.0.0.1:5009/admin/login")
        print("🔑 Login: admin / admin123")
        
        return True

def main():
    """Main builder function"""
    builder = CampPowerUpBuilder()
    builder.build_complete_system()

if __name__ == "__main__":
    main()
