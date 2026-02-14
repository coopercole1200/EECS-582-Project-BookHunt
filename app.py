"""
Artifact: app.py
Description: Main entry point. Starts application. 
Authors: Cole Cooper
Date Created: 2/14/2026
Date Last Modified: 2/14/2026
Last Modified by: Cole Cooper
"""

# Imports
from flask import Flask, render_template
from database import DatabaseBackend

# Creates Flask and gives it templates
app = Flask(__name__)


@app.route('/')
def index():
    #Initialize database
    db = DatabaseBackend()
    # Basic call to get all books, just a test to see if it works
    books = db.get_all_books()
    db.close()
    # Gives html template files to Flask
    return render_template('index.html', books=books)
    

if __name__ == '__main__':
    # Run the app and enable debug mode
    app.run(debug=True, port=5000)
