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
class DatabaseBackend:
    def __init__(self, db_path: str = "books.db"):
        # Initialize database connection and create tables
        self.db_path = db_path
        self.connection = sqlite3.connect(db_path)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()
        self._create_tables()

        self.current_user_id: Optional[int] = None
        self.current_username: Optional[str] = None

###################################################################################TABLE CREATION FUNCTION##################################################################
    def _create_tables(self):

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT    NOT NULL UNIQUE,
                password TEXT    NOT NULL
            )
        ''')
        self.connection.commit()
        print("Database initialized successfully")

    def _books_table(self, user_id: int) -> str:
        return f"books_user_{user_id}"

    def _tags_table(self, user_id: int) -> str:
        # Fix 1: tags are now per-user, not global
        return f"tags_user_{user_id}"

    def _book_tags_table(self, user_id: int) -> str:
        return f"book_tags_user_{user_id}"

    def _create_user_tables(self, user_id):
        # Create initial tables
        # Basic book info, we can change/add features later
        #Creates columns for each in table
        bt  = self._books_table(user_id)
        tt  = self._tags_table(user_id)
        btt = self._book_tags_table(user_id)

        # Books table
        self.cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {bt} (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                title          TEXT    NOT NULL,
                author         TEXT    NOT NULL,
                genre          TEXT,
                year           INT,
                rating         REAL    CHECK(rating >= 0 AND rating <= 5),
                review_content TEXT    DEFAULT NULL,
                status         TEXT    DEFAULT "to read"
            )
        ''')

        # Tags table
        self.cursor.execute(f'''
             CREATE TABLE IF NOT EXISTS {tt} (
                 id    INTEGER PRIMARY KEY AUTOINCREMENT,
                 label TEXT    NOT NULL UNIQUE
             )
         ''')

        # Junction table: links books to tags
        self.cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {btt} (
                book_id INTEGER NOT NULL,
                tag_id  INTEGER NOT NULL,
                PRIMARY KEY (book_id, tag_id),
                FOREIGN KEY (book_id) REFERENCES {bt}(id),
                FOREIGN KEY (tag_id)  REFERENCES {tt}(id)
            )
        ''')

        self.connection.commit()
        # Debug message
        print("User Tables initialized successfully")

###############################################################################USER SIGN-IN RELATED FUNCTIONS###############################################################
    def register_user(self, username, password) :
        username = username.strip()
        if not username or not password:
            return False, "Username and password cannot be empty."
        try:
            self.cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password))
            self.connection.commit()
            self.cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            user_id = self.cursor.fetchone()["id"]
            self._create_user_tables(user_id)
            return True, "ok"

        except sqlite3.IntegrityError:
            return False, f"Username '{username}' is already taken."

    def login_user(self, username, password) :
        username = username.strip()
        self.cursor.execute(
            "SELECT id, username FROM users WHERE username = ? AND password = ?",
            (username, password),
        )
        row = self.cursor.fetchone()
        if row is None:
            return False, "Invalid username or password."
        self.current_user_id = row["id"]
        self.current_username = row["username"]
        self._create_user_tables(self.current_user_id)  # idempotent safety
        return True, "ok"

    def logout_user(self):
        self.current_user_id = None
        self.current_username = None

    def _require_login(self):
        if self.current_user_id is None:
            raise RuntimeError("No user is logged in.")


###############################################################################BOOK RELATED FUNCTIONS#######################################################################
    # Create a book item in the book table
    def create_book(self, title=None, author=None, genre=None, year=None, rating=None, status="to read") :
        """called on create book button press, create an entry in the book table with specified info"""

        self._require_login()
        bt = self._books_table(self.current_user_id)

        # Normalize/clean values for DB insert
        title = (title or "").strip()
        author = (author or "").strip()
        genre = (genre or "").strip()

        # Allow empty strings to become NULL for optional fields
        genre_db = genre if genre != "" else None

        self.cursor.execute(
            f"INSERT INTO {bt} (title, author, genre, year, rating, status) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (title, author, genre_db, year, rating, status),
        )
        self.connection.commit()

    # Delete a book item in the table
    def delete_book(self, book_id) :
        """called on delete book button press, delete specific entry"""
        self._require_login()
        bt = self._books_table(self.current_user_id)
        self.cursor.execute(f"DELETE FROM {bt} WHERE id = ?", (book_id,))
        self.connection.commit()

    # Update a book item in the table
    def update_book(self, new_attributes, book_id, isRatingBeingUpdated):
        """update book attributes of specific entity given by book_id"""
        self._require_login()
        bt = self._books_table(self.current_user_id)

        if not isRatingBeingUpdated :
            query = f"UPDATE {bt} SET title=?, author=?, genre=?, year=?, status=? WHERE id=?"
            self.cursor.execute(query, (new_attributes[0], new_attributes[1], new_attributes[2], new_attributes[3], new_attributes[4].lower(), book_id))

        else:
            query = f"UPDATE {bt} SET rating=? WHERE id=?"
            self.cursor.execute(query, (new_attributes[0], book_id))
        self.connection.commit()

    # Count the number of entries in the book table
    def get_book_count(self) :
        self._require_login()
        bt = self._books_table(self.current_user_id)
        self.cursor.execute(f"SELECT COUNT(*) FROM {bt}")
        return self.cursor.fetchall()[0][0]

    # Get all info of a specific, single book entry from the table
    def get_specific_book(self, book_id):
        """get book entry based on book id"""
        self._require_login()
        bt = self._books_table(self.current_user_id)
        self.cursor.execute(f"SELECT * FROM {bt} WHERE id = ?", (book_id,))
        book = self.cursor.fetchone()
        return book

    # Get all info of book entries with a specific, exact book name
    def get_books_by_name(self, title, sort_by):

        self._require_login()
        bt = self._books_table(self.current_user_id)

        if not (title == "") :
            self.cursor.execute(f'SELECT * FROM {bt} WHERE title = \'{title}\' ORDER BY {sort_by}')
        else :
            self.cursor.execute(f'SELECT * FROM {bt} ORDER BY {sort_by}')

        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]

    # Get book entries based on a specific, custom filter
    def get_filtered_books(self, status: Optional[str] = None, genre: Optional[str] = None, tag_ids: Optional[List[int]] = None, sort_by: str = "id", ) -> List[Dict]:
        self._require_login()
        bt = self._books_table(self.current_user_id)
        btt = self._book_tags_table(self.current_user_id)

        # Return books matching ALL supplied filters.
        conditions: List[str] = []
        params: List = []

        # Status filter
        if status and status not in ("All", "Filter by status"):
            status_map = {
                "To Read": "to read",
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
                    f"EXISTS (SELECT 1 FROM {btt} bt WHERE bt.book_id = b.id AND bt.tag_id = ?)"
                )
                params.append(tid)

        where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        query = f"SELECT b.* FROM {bt} b {where_clause} ORDER BY b.{sort_by}"
        self.cursor.execute(query, params)
        return [dict(row) for row in self.cursor.fetchall()]

    # Returns a list of dictionaries that is all books
    def get_all_books(self, sort_by='id') -> List[Dict]:

        self._require_login()
        bt = self._books_table(self.current_user_id)

        # Get all info about all books and order by id
        self.cursor.execute(f'SELECT * FROM {bt} ORDER BY {sort_by}')
        # Stores all data from SQL query into rows
        rows = self.cursor.fetchall()
        # Makes a list out of all returned books
        return [dict(row) for row in rows]

###############################################################################GENRE RELATED FUNCTIONS######################################################################
    # Genre helper function
    def get_distinct_genres(self) -> List[str]:

        self._require_login()
        bt = self._books_table(self.current_user_id)

        #Return a sorted list of every genre in the DB
        self.cursor.execute(
            f"SELECT DISTINCT genre FROM {bt} WHERE genre IS NOT NULL ORDER BY genre"
        )
        return [row[0] for row in self.cursor.fetchall()]

    def get_genres_with_stats(self) :

        self._require_login()
        bt = self._books_table(self.current_user_id)

        self.cursor.execute(
            f"SELECT DISTINCT genre, COUNT(genre) AS count, AVG(rating) AS avg FROM {bt} GROUP BY genre"
        )
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]

###############################################################################REVIEW RELATED FUNCTIONS#####################################################################
    def update_review(self, book_id, new):

        self._require_login()
        bt = self._books_table(self.current_user_id)

        query = f"UPDATE {bt} SET review_content = '{new}' WHERE id = {book_id}"
        self.cursor.execute(query)
        self.connection.commit()

    def delete_review(self, book_id):

        self._require_login()
        bt = self._books_table(self.current_user_id)

        query = f"UPDATE {bt} SET review_content = NULL WHERE id = {book_id}"
        self.cursor.execute(query)
        self.connection.commit()

###############################################################################TAG RELATED FUNCTIONS########################################################################
    def create_tag(self, label: str) -> int:

        self._require_login()
        tt = self._tags_table(self.current_user_id)

        #Insert a new tag and return its id
        label = label.strip()
        self.cursor.execute(
            f"INSERT OR IGNORE INTO {tt} (label) VALUES (?)", (label,)
        )
        self.connection.commit()
        self.cursor.execute(f"SELECT id FROM {tt} WHERE label = ?", (label,))
        return self.cursor.fetchone()[0]
 
    def add_tag_to_book(self, book_id: int, tag_label: str):
        #Add a tag to a book
        self._require_login()
        btt = self._book_tags_table(self.current_user_id)

        tag_id = self.create_tag(tag_label)
        self.cursor.execute(
            f"INSERT OR IGNORE INTO {btt} (book_id, tag_id) VALUES (?, ?)",
            (book_id, tag_id),
        )
        self.connection.commit()
 
    def remove_tag_from_book(self, book_id: int, tag_id: int):
        #REmove a tag from a book
        self._require_login()
        btt = self._book_tags_table(self.current_user_id)

        self.cursor.execute(
            f"DELETE FROM {btt} WHERE book_id = ? AND tag_id = ?",
            (book_id, tag_id),
        )
        self.connection.commit()
 
    def get_tags_for_book(self, book_id: int) -> List[Dict]:
        #Return all tags attached to specified book
        self._require_login()
        tt = self._tags_table(self.current_user_id)
        btt = self._book_tags_table(self.current_user_id)

        self.cursor.execute(
            f"""SELECT t.id, t.label FROM {tt} t
               JOIN {btt} bt ON t.id = bt.tag_id
               WHERE bt.book_id = ?
               ORDER BY t.label""",
            (book_id,),
        )
        return [dict(row) for row in self.cursor.fetchall()]

    # Tag helper function
    def get_all_tags(self) -> List[Dict]:
        #Return all tags as a list
        self._require_login()
        tt = self._tags_table(self.current_user_id)
        self.cursor.execute(f"SELECT id, label FROM {tt} ORDER BY label")
        return [dict(row) for row in self.cursor.fetchall()]

    def get_tags_with_stats(self) :

        self._require_login()
        tt = self._tags_table(self.current_user_id)
        btt = self._book_tags_table(self.current_user_id)
        bt = self._books_table(self.current_user_id)

        self.cursor.execute(
            f"SELECT label AS tag, COUNT(label) AS count, AVG(rating) AS avg FROM (SELECT {tt}.label, {bt}.rating FROM {tt}, {btt}, {bt} WHERE {tt}.id = {btt}.tag_id AND {btt}.book_id = {bt}.id) GROUP BY tag"
        )
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]

###############################################################################CLOSE CONNECTION FUNCTION####################################################################
    def close(self):
        # Closes database connection
        if self.connection:
            self.connection.close()
            print("Database connection closed")


#Test to display books
if __name__ == "__main__":
    db = DatabaseBackend("books.db")
    
    # Display all books
    books = db.get_all_books()
    print(f"\nAll books in database:")
    for book in books:
        print(f"  - {book['title']} by {book['author']}")
    
    db.close()

    
