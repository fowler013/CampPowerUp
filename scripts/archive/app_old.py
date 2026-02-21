import pandas as pd
import sqlite3
import re
from flask import Flask, jsonify, render_template
import os

app = Flask(__name__)

# Configuration
CSV_FILE_PATH = 'data/Camp_Power_Up_past_forms - Sheet1.csv'
DB_FILE = 'camp_power_up.db'


# --- Database Functions ---
def setup_database():
    """Creates the database and campers table."""
    print("📊 Setting up database...")
    conn = sqlite3.connect(DATABASE_FILE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS campers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT, last_name TEXT, age INTEGER, grade TEXT,
            returning_camper TEXT, email TEXT, allergies TEXT,
            allergy_details TEXT, sensory_issues TEXT, sensory_description TEXT,
            favorite_games TEXT, bringing_switch TEXT
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ Database is ready.")

def import_data_from_csv():
    """Imports data from the CSV file into the database."""
    if not os.path.exists(CSV_FILE_PATH):
        print(f"❌ CSV file not found at: {CSV_FILE_PATH}")
        print("   Please make sure your CSV file is in the 'data' folder.")
        return 0

    print(f"📁 Importing data from {CSV_FILE_PATH}...")
    conn = sqlite3.connect(DATABASE_FILE_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM campers") # Clear old data

    imported_count = 0
    with open(CSV_FILE_PATH, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        header = next(reader) # Skip header

        for row in reader:
            if len(row) < 16: continue # Skip incomplete rows
            try:
                cursor.execute('''
                    INSERT INTO campers (first_name, last_name, age, grade, returning_camper, email,
                                         allergies, allergy_details, sensory_issues, sensory_description,
                                         favorite_games, bringing_switch)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row[2], row[3], int(row[5]) if row[5].isdigit() else 0, row[6],
                    row[4], row[1], row[13], row[14], row[11], row[12], row[15], row[9]
                ))
                imported_count += 1
            except Exception as e:
                print(f"⚠️  Skipping row due to error: {e}")

    conn.commit()
    conn.close()
    print(f"✅ Successfully imported {imported_count} campers.")
    return imported_count

def clean_col_names(df):
    """Cleans all column names in a pandas DataFrame."""
    cols = df.columns
    new_cols = []
    for col in cols:
        # Convert to lowercase
        new_col = col.lower()
        # Remove special characters, replace spaces with underscores
        new_col = re.sub(r'[^a-z0-9]+', '_', new_col).strip('_')
        new_cols.append(new_col)
    df.columns = new_cols
    print("--- Cleaned Column Names ---")
    print(df.columns.to_list())
    print("----------------------------")
    return df

def load_data():
    """Loads, cleans, and stores data from the CSV file."""
    if not os.path.exists(CSV_FILE_PATH_HISTORICAL):
        print(f"Error: The file was not found at {CSV_FILE_PATH_HISTORICAL}")
        return

    print(f"Reading data from {CSV_FILE_PATH_HISTORICAL}...")
    df = pd.read_csv(CSV_FILE_PATH_HISTORICAL)
    
    # Automatically clean all column names
    df = clean_col_names(df)

    # Convert age column to numeric, coercing errors
    if 'age' in df.columns:
        df['age'] = pd.to_numeric(df['age'], errors='coerce')
    else:
        print("Warning: Could not find a cleaned 'age' column.")

    # Load data into SQLite database
    conn = sqlite3.connect('camp_power_up.db')
    df.to_sql('registrations', conn, if_exists='replace', index=False)
    conn.close()
    print(f"Successfully loaded data into {DB_FILE}")


# --- Web Dashboard HTML ---
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Camp Power-Up 2025</title>
    <style>
        body { font-family: system-ui, sans-serif; margin: 20px; background: #f4f7f9; color: #333; }
        .container { max-width: 1000px; margin: auto; }
        header { text-align: center; margin-bottom: 30px; }
        h1 { color: #2c3e50; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 20px; }
        .stat-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center; }
        .stat-number { font-size: 2.5em; font-weight: bold; color: #3498db; }
        .stat-label { color: #7f8c8d; margin-top: 5px; }
        .section { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-top: 30px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
        th { background-color: #f8f9fa; }
        .error { color: #e74c3c; background: #fbebeb; padding: 15px; border-radius: 8px; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🏕️ Camp Power-Up 2025 Dashboard</h1>
        </header>
        <div id="stats-grid" class="stats-grid"></div>
        <div id="special-needs" class="section"><h2>⚠️ Special Needs</h2><div id="special-needs-content"></div></div>
        <div id="roster" class="section"><h2>👥 Camper Roster</h2><div id="roster-content"></div></div>
    </div>
    <script>
        const API_URL = 'http://localhost:5000';

        async function fetchData(endpoint) {
            try {
                const response = await fetch(`${API_URL}${endpoint}`);
                if (!response.ok) throw new Error(`Network response was not ok: ${response.statusText}`);
                return await response.json();
            } catch (error) {
                console.error(`Failed to fetch ${endpoint}:`, error);
                return null;
            }
        }

        async function renderDashboard() {
            const stats = await fetchData('/api/stats');
            if (stats) {
                const statsGrid = document.getElementById('stats-grid');
                statsGrid.innerHTML = `
                    <div class="stat-card"><div class="stat-number">${stats.total_campers}</div><div class="stat-label">Total Campers</div></div>
                    <div class="stat-card"><div class="stat-number">${stats.returning_campers}</div><div class="stat-label">Returning</div></div>
                    <div class="stat-card"><div class="stat-number">${stats.with_allergies}</div><div class="stat-label">With Allergies</div></div>
                    <div class="stat-card"><div class="stat-number">${stats.with_sensory_needs}</div><div class="stat-label">With Sensory Needs</div></div>
                `;
            }

            const specialNeeds = await fetchData('/api/special_needs');
            if (specialNeeds) {
                const content = document.getElementById('special-needs-content');
                let html = '<table><tr><th>Name</th><th>Type</th><th>Details</th></tr>';
                specialNeeds.forEach(c => {
                    html += `<tr><td>${c.first_name} ${c.last_name}</td><td>${c.type}</td><td>${c.details}</td></tr>`;
                });
                content.innerHTML = html + '</table>';
            }

            const campers = await fetchData('/api/campers');
            if (campers) {
                const content = document.getElementById('roster-content');
                let html = '<table><tr><th>Name</th><th>Age</th><th>Grade</th><th>Returning?</th></tr>';
                campers.forEach(c => {
                    html += `<tr><td>${c.first_name} ${c.last_name}</td><td>${c.age}</td><td>${c.grade}</td><td>${c.returning_camper}</td></tr>`;
                });
                content.innerHTML = html + '</table>';
            }
        }

        window.onload = renderDashboard;
    </script>
</body>
</html>
"""

# --- API Endpoints ---
@app.route('/')
def dashboard():
    """Serves the main HTML dashboard."""
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/stats')
def get_stats():
    """Provides key statistics about the camp."""
    conn = sqlite3.connect(DATABASE_FILE_PATH)
    cursor = conn.cursor()
    stats = {
        'total_campers': cursor.execute('SELECT COUNT(*) FROM campers').fetchone()[0],
        'returning_campers': cursor.execute('SELECT COUNT(*) FROM campers WHERE returning_camper = "Yes"').fetchone()[0],
        'with_allergies': cursor.execute('SELECT COUNT(*) FROM campers WHERE allergies = "Yes"').fetchone()[0],
        'with_sensory_needs': cursor.execute('SELECT COUNT(*) FROM campers WHERE sensory_issues = "Yes"').fetchone()[0],
    }
    conn.close()
    return jsonify(stats)

@app.route('/api/campers')
def get_campers():
    """Returns the full camper roster."""
    conn = sqlite3.connect(DATABASE_FILE_PATH)
    conn.row_factory = sqlite3.Row
    campers = conn.execute('SELECT first_name, last_name, age, grade, returning_camper FROM campers ORDER BY first_name').fetchall()
    conn.close()
    return jsonify([dict(row) for row in campers])

@app.route('/api/special_needs')
def get_special_needs():
    """Returns a list of campers with special needs."""
    conn = sqlite3.connect(DATABASE_FILE_PATH)
    conn.row_factory = sqlite3.Row
    allergies = conn.execute('SELECT first_name, last_name, allergy_details FROM campers WHERE allergies = "Yes"').fetchall()
    sensory = conn.execute('SELECT first_name, last_name, sensory_description FROM campers WHERE sensory_issues = "Yes"').fetchall()
    conn.close()
    
    needs = []
    for row in allergies:
        needs.append({'first_name': row['first_name'], 'last_name': row['last_name'], 'type': 'Allergy', 'details': row['allergy_details']})
    for row in sensory:
        needs.append({'first_name': row['first_name'], 'last_name': row['last_name'], 'type': 'Sensory', 'details': row['sensory_description']})
        
    return jsonify(sorted(needs, key=lambda x: x['first_name']))

@app.route('/api/data/<query>')
def get_data(query):
    """API endpoint to fetch processed data for charts."""
    conn = sqlite3.connect('camp_power_up.db')
    cursor = conn.cursor()

    # Note: We use the cleaned column names here (e.g., 'age', 'gender')
    if query == 'age_distribution':
        cursor.execute("SELECT age, COUNT(*) FROM registrations WHERE age IS NOT NULL GROUP BY age ORDER BY age")
    elif query == 'gender_distribution':
        cursor.execute("SELECT gender, COUNT(*) FROM registrations WHERE gender IS NOT NULL GROUP BY gender")
    elif query == 'grade_distribution':
        cursor.execute("SELECT grade, COUNT(*) FROM registrations WHERE grade IS NOT NULL GROUP BY grade")
    else:
        conn.close()
        return jsonify({"error": "Invalid query"}), 400

    data = cursor.fetchall()
    conn.close()
    return jsonify(data)

# --- Main Execution ---
if __name__ == '__main__':
    print("--- Camp Power-Up Management System ---")
    setup_database()
    import_data_from_csv()
    load_data()
    print("\n🚀 Starting Flask server...")
    print("   View your dashboard at: http://localhost:5000")
    app.run(debug=True, port=5000, host='0.0.0.0')
