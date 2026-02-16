"""
Artifact: database.py
Description: Uses SQLite to handle database operations
Authors: Cole Cooper
Date Created: 2/14/2026
Date Last Modified: 2/14/2026
Last Modified by: Cole Cooper
"""

# Import Libraries and Tools
import sqlite3
from typing import List, Dict, Optional

class DatabaseBackend:
    def __init__(self, db_path: str = "books.db"):
        # Initialize database connection and create tables
        self.db_path = db_path
        self.connection = sqlite3.connect(db_path)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()
        self._create_tables()

    def _create_tables(self):
        # Create initial tables
        # Basic book info, we can change/add features later
        #Creates columns for each in table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                genre TEXT,
                year INTEGER,
                rating REAL CHECK(rating >=0 AND rating <=5),
                status TEXT DEFAULT 'to-read'
            )
        ''')
        self.connection.commit()
        # Debug message
        print("Database initialized successfully")

    #create a book item in the book table
    def create_book(self) :
        """called on create book button press, create an entry in the book table with specified info"""
        #TODO: CHANGE TO ACTUALLY ACCEPT USER DEFINED INFO
        self.cursor.execute('''
                    INSERT INTO books (title, author, genre, year, rating, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', ("The Analects", "Confucius's Disciples", "Philosophy", -221 , 4, "currently reading"))
        self.connection.commit()

    def delete_book(self) :
        """called on delete book button press, delete specific entry"""
        #TODO: CHANGE TO ACTUALLY ACCEPT USER DEFINED INFO
        self.cursor.execute('DELETE FROM books WHERE id = ?', (4,))
        self.connection.commit()

    # Returns a list of dictionaries that is all books
    def get_all_books(self) -> List[Dict]:
        # Get all info about all books and order by title
        self.cursor.execute('SELECT * FROM books ORDER BY title')
        # Stores all data from SQL query into rows
        rows = self.cursor.fetchall()
        # Makes a list out of all returned books
        return [dict(row) for row in rows]

    def close(self):
        # Closes database connection
        if self.connection:
            self.connection.close()
            print("Database connection closed")


#Test to display books
if __name__ == "__main__":
    db = DatabaseBackend("books.db")
    
    # Check if database is empty
    books = db.get_all_books()

    if len(books) == 0:
        print("Adding sample books...")
        # Add some sample books directly for testing
        db.cursor.execute('''
            INSERT INTO books (title, author, genre, year, rating, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ("1984", "George Orwell", "Dystopian Fiction", 1949, 4.5, "completed"))
        
        db.cursor.execute('''
            INSERT INTO books (title, author, genre, year, rating, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ("To Kill a Mockingbird", "Harper Lee", "Classic Fiction", 1960, 5.0, "completed"))
        
        db.cursor.execute('''
            INSERT INTO books (title, author, genre, year, rating, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ("The Great Gatsby", "F. Scott Fitzgerald", "Classic Fiction", 1925, 4.0, "to-read"))
        
        db.connection.commit()
        print("Sample books added!")
    else:
        print(f"Database already has {len(books)} books")
    
    # Display all books
    books = db.get_all_books()
    print(f"\nAll books in database:")
    for book in books:
        print(f"  - {book['title']} by {book['author']}")
    
    db.close()

    
