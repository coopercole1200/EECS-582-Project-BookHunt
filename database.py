"""
Artifact: database.py
Description: Uses SQLite to handle database operations
Authors: Cole Cooper
Date Created: 2/14/2026
Date Last Modified: 3/13/2026
Last Modified by: Cole Cooper
"""

# Import Libraries and Tools
import sqlite3
from typing import List, Dict, Optional
from datetime import date

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

        # enable foreign key enforcing
        self.cursor.execute("PRAGMA foreign_keys = ON;")

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                genre TEXT,
                year INTEGER,
                rating REAL CHECK(rating >=0 AND rating <=5),
                review_content TEXT DEFAULT NULL,
                status TEXT DEFAULT 'to-read'
            )
        ''')
        # reviews
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                review_id INTEGER PRIMARY KEY,
                book_id INTEGER,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                review TEXT,
                date_created TEXT NOT NULL,
                last_updated TEXT NOT NULL,
                FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE
            )
        ''')
        # Tags table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY,
                label TEXT NOT NULL UNIQUE
            )
        ''')
        # Junction table: links books to tags
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS book_tags (
                book_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                PRIMARY KEY (book_id, tag_id),
                FOREIGN KEY (book_id) REFERENCES books(id),
                FOREIGN KEY (tag_id) REFERENCES tags(id)
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
                        INSERT INTO books (title, author, genre, year, rating, status)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', ("The Analects", "Confucius's Disciples", "Philosophy", -221 , 4, "currently reading"))
            self.connection.commit()
            return

        # Normalize/clean values for DB insert
        title = (title or "").strip()
        author = (author or "").strip()
        genre = (genre or "").strip()

        # Allow empty strings to become NULL for optional fields
        genre_db = genre if genre != "" else None

        self.cursor.execute('''
                    INSERT INTO books (title, author, genre, year, rating, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (title, author, genre_db, year, rating, status))
        self.connection.commit()

    def delete_book(self, book_id) :
        """called on delete book button press, delete specific entry"""
        self.cursor.execute('DELETE FROM books WHERE id = ?', (book_id,))
        self.connection.commit()

    def update_book(self, new_attributes, book_id, isRatingBeingUpdated):
        """update book attributes of specific entity given by book_id"""
        if not isRatingBeingUpdated:
            query = f'UPDATE books SET title = ?, author = ?, genre = ?, year = ?, status = ? WHERE id = ?'
            self.cursor.execute(query, (new_attributes[0], new_attributes[1], new_attributes[2], int(new_attributes[3]), new_attributes[4].lower(), book_id))
        else:
            query = f'UPDATE books SET rating = ? WHERE id = ?'
            self.cursor.execute(query, (new_attributes[0], book_id))
        self.connection.commit()
    
    # review helper methods
    def create_review(self, book_id, title: str, review: str):
        """create a new review on a book"""
        today = date.today().isoformat() # the day the create_review() method is run, in format YYYY-MM-DD
        author = "TODO" # get author from user table

        self.cursor.execute("""
            INSERT INTO reviews (book_id, title, author, review, date_created, last_updated)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (str(book_id), title, author, review, today, today))
        self.connection.commit()
    
    def update_review(self, review_id, new_title: str, new_review: str):
        """update an existing review on a book"""
        today = date.today().isoformat()

        self.cursor.execute("""
            UPDATE reviews SET title = ?, review = ?, last_updated = ? WHERE id = ?
        """, (new_title, new_review, today, str(review_id)))
        self.connection.commit()

    def delete_review(self, review_id):
        """delete an existing review on a book"""
        self.cursor.execute('DELETE FROM reviews WHERE id = ?', (str(review_id)))
        self.connection.commit()

    def get_reviews(self, book_id):
        """get all reviews of a certain book"""
        self.cursor.execute("""SELECT * FROM reviews WHERE book_id = ?
        """, str(book_id))
        rows = self.cursor.fetchall()

        return [dict(row) for row in rows]

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

    def get_books_by_name(self, title, sort_by):
        if not (title == "") :
            self.cursor.execute(f'SELECT * FROM books WHERE title = \'{title}\' ORDER BY {sort_by}')
        else :
            self.cursor.execute(f'SELECT * FROM books ORDER BY {sort_by}')
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]
    
    # Genre helper function
    def get_distinct_genres(self) -> List[str]:
        #Return a sorted list of every genre in the DB
        self.cursor.execute(
            "SELECT DISTINCT genre FROM books WHERE genre IS NOT NULL ORDER BY genre"
        )
        return [row[0] for row in self.cursor.fetchall()]
    
    # Tag helper function
    def get_all_tags(self) -> List[Dict]:
        #Return all tags as a list
        self.cursor.execute("SELECT id, label FROM tags ORDER BY label")
        return [dict(row) for row in self.cursor.fetchall()]
 
    def create_tag(self, label: str) -> int:
        #Insert a new tag and return its id
        label = label.strip()
        self.cursor.execute(
            "INSERT OR IGNORE INTO tags (label) VALUES (?)", (label,)
        )
        self.connection.commit()
        self.cursor.execute("SELECT id FROM tags WHERE label = ?", (label,))
        return self.cursor.fetchone()[0]
 
    def add_tag_to_book(self, book_id: int, tag_label: str):
        #Add a tag to a book
        tag_id = self.create_tag(tag_label)
        self.cursor.execute(
            "INSERT OR IGNORE INTO book_tags (book_id, tag_id) VALUES (?, ?)",
            (book_id, tag_id),
        )
        self.connection.commit()
 
    def remove_tag_from_book(self, book_id: int, tag_id: int):
        #REmove a tag from a book
        self.cursor.execute(
            "DELETE FROM book_tags WHERE book_id = ? AND tag_id = ?",
            (book_id, tag_id),
        )
        self.connection.commit()
 
    def get_tags_for_book(self, book_id: int) -> List[Dict]:
        #Return all tags attached to specified book
        self.cursor.execute(
            """SELECT t.id, t.label FROM tags t
               JOIN book_tags bt ON t.id = bt.tag_id
               WHERE bt.book_id = ?
               ORDER BY t.label""",
            (book_id,),
        )
        return [dict(row) for row in self.cursor.fetchall()]
    
    # Combined filter
    def get_filtered_books(
        self,
        status: Optional[str] = None,
        genre: Optional[str] = None,
        tag_ids: Optional[List[int]] = None,
        sort_by: str = "id",
    ) -> List[Dict]:
        #Return books matching ALL supplied filters.
        conditions: List[str] = []
        params: List = []
 
        # Status filter
        if status and status not in ("All", "Filter by status"):
            status_map = {
                "To Read": "to-read",
                "Completed": "completed",
                "Currently Reading": "currently reading",
            }
            db_status = status_map.get(status, status.lower())
            conditions.append("b.status = ?")
            params.append(db_status)
 
        # Genre filter
        if genre and genre not in ("All Genres", "Filter by genre"):
            conditions.append("b.genre = ?")
            params.append(genre)
 
        # Tag filter: book must have ALL selected tags
        if tag_ids:
            for tid in tag_ids:
                conditions.append(
                    "EXISTS (SELECT 1 FROM book_tags bt WHERE bt.book_id = b.id AND bt.tag_id = ?)"
                )
                params.append(tid)
 
        where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        query = f"SELECT b.* FROM books b {where_clause} ORDER BY b.{sort_by}"
        self.cursor.execute(query, params)
        return [dict(row) for row in self.cursor.fetchall()]
    
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
            INSERT INTO books (id, title, author, genre, year, rating, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (1, "1984", "George Orwell", "Dystopian Fiction", 1949, 4.5, "completed"))
        
        db.cursor.execute('''
            INSERT INTO books (id, title, author, genre, year, rating, review_content, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (2, "To Kill a Mockingbird", "Harper Lee", "Classic Fiction", 1960, 5.0, "the book was good", "completed"))
        
        db.cursor.execute('''
            INSERT INTO books (id, title, author, genre, year, rating, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (3, "The Great Gatsby", "F. Scott Fitzgerald", "Classic Fiction", 1925, 4.0, "to-read"))
        
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

    
