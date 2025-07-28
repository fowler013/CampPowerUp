#!/usr/bin/env python3

from flask import Flask, render_template
import os

app = Flask(__name__, template_folder='templates')

@app.route('/')
def test():
    print(f"Current directory: {os.getcwd()}")
    print(f"Template folder: {app.template_folder}")
    print(f"Root path: {app.root_path}")
    print(f"Templates dir exists: {os.path.exists('templates')}")
    print(f"registration_form.html exists: {os.path.exists('templates/registration_form.html')}")
    
    return render_template('registration_form.html', 
                         camp_title="TEST REGISTRATION FORM",
                         camp_subtitle="This should show the registration form",
                         pricing={"returning_text": "Test pricing"},
                         config={})

if __name__ == '__main__':
    app.run(debug=True, port=5003)
