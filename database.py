"""
Artifact: database.py
Description: Uses SQLite to handle database operations
Authors: Cole Cooper
Date Created: 2/14/2026
Date Last Modified: 2/15/2026
Last Modified by: Carson Abbott
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

    def get_specific_book(self, book_id):
        """get book entry based on book id"""
        self.cursor.execute(f'SELECT * FROM books WHERE id = {book_id}')
        book = self.cursor.fetchone()
        return book

    #create a book item in the book table
    def create_book(self) :
        """called on create book button press, create an entry in the book table with specified info"""
        #TODO: CHANGE TO ACTUALLY ACCEPT USER DEFINED INFO
        self.cursor.execute('''
                    INSERT INTO books (id, title, author, genre, year, rating, status)
                    VALUES (NULL, ?, ?, ?, ?, ?, ?)
                ''', ("The Analects", "Confucius's Disciples", "Philosophy", -221 , 4, "currently reading"))
        self.connection.commit()

    def delete_book(self) :
        """called on delete book button press, delete specific entry"""
        #TODO: CHANGE TO ACTUALLY ACCEPT USER DEFINED INFO
        self.cursor.execute('DELETE FROM books WHERE id = ?', (4,))
        self.connection.commit()

    def update_book(self, new_attributes, book_id):
        """update book attributes of specific entity given by book_id"""
        query = f'UPDATE books SET title = ?, author = ?, genre = ?, year = ?, status = ? WHERE id = ?'
        self.cursor.execute(query, (new_attributes[0], new_attributes[1], new_attributes[2], int(new_attributes[3]), new_attributes[4], book_id))
        self.connection.commit()

    def get_book_count(self) :
        self.cursor.execute('SELECT COUNT(*) FROM books')
        count = self.cursor.fetchall()[0][0]
        return count

    # Returns a list of dictionaries that is all books
    def get_all_books(self, sort_by='id') -> List[Dict]:
        # Get all info about all books and order by id
        self.cursor.execute(f'SELECT * FROM books ORDER BY {sort_by}')
        # Stores all data from SQL query into rows
        rows = self.cursor.fetchall()
        # Makes a list out of all returned books
        return [dict(row) for row in rows]

    # Returns a list of dictionaries that is all books based on a certain status
    def get_books_by_status(self, status) -> List[Dict]:
        if (status == "All"):
            self.cursor.execute('SELECT * FROM books ORDER BY title')
        else:
            formattedStatus = ""
            if (status == "To Read"):
                formattedStatus = "to-read"
            else:
                formattedStatus = status.lower()
            # Get all info about all books based on a certain status and order by title
            self.cursor.execute('SELECT * FROM books WHERE status = ? ORDER BY title', (formattedStatus,))
        
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

    """if len(books) == 0:
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
        print(f"Database already has {len(books)} books")"""
    
    # Display all books
    books = db.get_all_books()
    print(f"\nAll books in database:")
    for book in books:
        print(f"  - {book['title']} by {book['author']}")
    
    db.close()

    
