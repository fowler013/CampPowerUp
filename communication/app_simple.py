#!/usr/bin/env python3
"""
Simple Communication Dashboard Test
"""

from flask import Flask, render_template

app = Flask(__name__)
app.secret_key = 'communication_test_2025'

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
    return render_template('send_message.html', campers=[])

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
