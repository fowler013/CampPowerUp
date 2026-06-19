cursor.execute('''
            SELECT submission_id, timestamp, child_first_name, child_last_name, 
                   child_age, parent_first_name, parent_last_name, parent_email,
                   parent_phone, emergency_contact_name, emergency_contact_phone,
                   has_allergies, allergies_description, has_medical_conditions,
                   medical_conditions_description, is_returning_camper,
                   returning_years, how_heard_about_camp, additional_comments
            FROM registrations 
            ORDER BY timestamp DESC
        ''')