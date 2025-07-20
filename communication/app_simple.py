#!/usr/bin/env python3
"""
Simple Communication Dashboard Test
"""

from flask import Flask, render_template
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'communication_test_2025'

# Database path - points to main camp database
DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'camp_power_up.db')

def get_campers_from_db():
    """Get camper data from the database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        
        cursor = conn.execute("""
            SELECT childs_first_name, childs_last_name, email_address, age 
            FROM registrations 
            WHERE childs_first_name IS NOT NULL 
            AND email_address IS NOT NULL
            ORDER BY childs_first_name, childs_last_name
        """)
        
        campers = []
        for row in cursor.fetchall():
            campers.append({
                'name': f"{row['childs_first_name']} {row['childs_last_name']}",
                'parent_email': row['email_address'],
                'age': row['age']
            })
        
        conn.close()
        return campers
    except Exception as e:
        print(f"Database error: {e}")
        return []

@app.route('/')
def communication_dashboard():
    """Main communication dashboard"""
    return render_template('communication_dashboard.html')

@app.route('/portal')
def parent_portal():
    """Parent portal"""
    return render_template('parent_portal.html')

@app.route('/send_message')
def send_message():
    """Send message page"""
    campers = get_campers_from_db()
    return render_template('send_message.html', campers=campers)

@app.route('/test')
def test():
    """Test route to verify this is the communication system"""
    return '''
    <h1 style="color: green;">✅ Communication System Working!</h1>
    <p>This is the <strong>COMMUNICATION DASHBOARD</strong>, not the main camp dashboard.</p>
    <ul>
        <li><a href="/">Communication Dashboard</a></li>
        <li><a href="/portal">Parent Portal</a></li>
        <li><a href="/send_message">Send Message</a></li>
    </ul>
    '''

if __name__ == '__main__':
    print("🏕️ Camp Power-Up Communication System")
    print("=====================================")
    print("🌐 Communication Dashboard: http://127.0.0.1:5004")
    print("🔧 Test page: http://127.0.0.1:5004/test")
    app.run(debug=False, port=5004)
