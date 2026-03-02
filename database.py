"""
Artifact: database.py
Description: Uses SQLite to handle database operations
Authors: Cole Cooper
Date Created: 2/14/2026
Date Last Modified: 2/28/2026
Last Modified by: Ebraheem AlAamer
"""

# Import Libraries and Tools
import sqlite3
from typing import List, Dict, Optional
global_id_counter = 3 # Please increment if you add more samples at the bottom. Terrible solution ik, but it works for now :P - Carson
class DatabaseBackend:
    def __init__(self, db_path: str = "books.db"):
        # Initialize database connection and create tables
        self.db_path = db_path
        self.connection = sqlite3.connect(db_path)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()
        self._create_tables()
        
        # Initializes ID_counter based on what's already in the database
        self.ID_counter = global_id_counter
        print(f"Initialized id counter to: {self.ID_counter}")

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
                review_content TEXT DEFAULT '',
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
    def create_book(self, title=None, author=None, genre=None, year=None, rating=None, status="to-read") :
        """called on create book button press, create an entry in the book table with specified info

        Backwards-compatible:
        - If no user-defined info is provided, inserts the original hardcoded example row.
        - If fields are provided, uses them as parameters for the INSERT query.
        """
        # If nothing provided, keep the original example insert so existing behavior doesn't break.
        if title is None and author is None and genre is None and year is None and rating is None and status == "to-read":
            #TODO: CHANGE TO ACTUALLY ACCEPT USER DEFINED INFO
            self.cursor.execute('''
                        INSERT INTO books (title, author, genre, year, rating, review_content, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', ("The Analects", "Confucius's Disciples", "Philosophy", -221 , 4, "", "currently reading"))
            self.connection.commit()
            return

        # Normalize/clean values for DB insert
        title = (title or "").strip()
        author = (author or "").strip()
        genre = (genre or "").strip()

        # Allow empty strings to become NULL for optional fields
        genre_db = genre if genre != "" else None

        self.cursor.execute('''
                    INSERT INTO books (title, author, genre, year, rating, review_content, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (title, author, genre_db, year, rating, "", status))
        self.connection.commit()

    def delete_book(self, book_id) :
        """called on delete book button press, delete specific entry"""
        self.cursor.execute('DELETE FROM books WHERE id = ?', (book_id,))
        self.connection.commit()

    def update_book(self, new_attributes, book_id):
        """update book attributes of specific entity given by book_id"""
        query = f'UPDATE books SET title = ?, author = ?, genre = ?, year = ?, review_content = ?, status = ? WHERE id = ?'
        self.cursor.execute(query, (new_attributes[0], new_attributes[1], new_attributes[2], int(new_attributes[3]), new_attributes[4].lower(), book_id))
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
            self.cursor.execute('SELECT * FROM books ORDER BY id')
        else:
            formattedStatus = ""
            if (status == "To Read"):
                formattedStatus = "to-read"
            else:
                formattedStatus = status.lower()
            # Get all info about all books based on a certain status and order by id
            self.cursor.execute('SELECT * FROM books WHERE status = ? ORDER BY id', (formattedStatus,))
        
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
            INSERT INTO books (id, title, author, genre, year, rating, review_content, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (1, "1984", "George Orwell", "Dystopian Fiction", 1949, 4.5, "", "completed"))
        
        db.cursor.execute('''
            INSERT INTO books (id, title, author, genre, year, rating, review_content, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (2, "To Kill a Mockingbird", "Harper Lee", "Classic Fiction", 1960, 5.0, "", "completed"))
        
        db.cursor.execute('''
            INSERT INTO books (id, title, author, genre, year, rating, review_content, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (3, "The Great Gatsby", "F. Scott Fitzgerald", "Classic Fiction", 1925, 4.0, "", "to-read"))
        
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

    
