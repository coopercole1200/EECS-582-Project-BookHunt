"""
Artifact: database.py
Description: Uses SQLite to handle database operations
Authors: Cole Cooper
Date Created: 2/14/2026
Date Last Modified: 4/12/2026
Last Modified by: Fixed tags-per-user, sort_by whitelist, selection crash guard
"""

import sqlite3
import hashlib
from typing import List, Dict, Optional


def _hash_password(password: str) -> str:
    """Hash a password with SHA-256 for secure storage."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# Fix 3: whitelist of safe sort columns to prevent SQL injection / errors
_VALID_SORT_COLUMNS = {"id", "title", "author", "genre", "year", "rating", "status"}


class DatabaseBackend:
    def __init__(self, db_path: str = "books.db"):
        self.db_path = db_path
        self.connection = sqlite3.connect(db_path)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()
        self._create_tables()

        self.current_user_id: Optional[int] = None
        self.current_username: Optional[str] = None

    # ------------------------------------------------------------------
    # Global schema – only users table; everything else is per-user (2.1)
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Per-user table name helpers
    # ------------------------------------------------------------------

    def _books_table(self, user_id: int) -> str:
        return f"books_user_{user_id}"

    def _tags_table(self, user_id: int) -> str:
        # Fix 1: tags are now per-user, not global
        return f"tags_user_{user_id}"

    def _book_tags_table(self, user_id: int) -> str:
        return f"book_tags_user_{user_id}"

    def _safe_sort(self, sort_by: str) -> str:
        # Fix 3: reject invalid sort columns to prevent SQL errors
        return sort_by if sort_by in _VALID_SORT_COLUMNS else "id"

    def _create_user_tables(self, user_id: int):
        """Create books, tags, and book_tags tables scoped to this user."""
        bt  = self._books_table(user_id)
        tt  = self._tags_table(user_id)
        btt = self._book_tags_table(user_id)

        self.cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {bt} (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                title          TEXT    NOT NULL,
                author         TEXT    NOT NULL,
                genre          TEXT,
                year           INTEGER,
                rating         REAL    CHECK(rating >= 0 AND rating <= 5),
                review_content TEXT    DEFAULT NULL,
                status         TEXT    DEFAULT "to-read"
            )
        ''')

        # Fix 1: per-user tags table (was global `tags`, now `tags_user_<id>`)
        self.cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {tt} (
                id    INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT    NOT NULL UNIQUE
            )
        ''')

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

    # ------------------------------------------------------------------
    # Authentication (2.2)
    # ------------------------------------------------------------------

    def register_user(self, username: str, password: str):
        username = username.strip()
        if not username or not password:
            return False, "Username and password cannot be empty."
        try:
            hashed = _hash_password(password)
            self.cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, hashed),
            )
            self.connection.commit()
            self.cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            user_id = self.cursor.fetchone()["id"]
            self._create_user_tables(user_id)
            return True, "ok"
        except sqlite3.IntegrityError:
            return False, f"Username '{username}' is already taken."

    def login_user(self, username: str, password: str):
        username = username.strip()
        hashed = _hash_password(password)
        self.cursor.execute(
            "SELECT id, username FROM users WHERE username = ? AND password = ?",
            (username, hashed),
        )
        row = self.cursor.fetchone()
        if row is None:
            return False, "Invalid username or password."
        self.current_user_id  = row["id"]
        self.current_username = row["username"]
        self._create_user_tables(self.current_user_id)  # idempotent safety
        return True, "ok"

    def logout_user(self):
        self.current_user_id  = None
        self.current_username = None

    def _require_login(self):
        if self.current_user_id is None:
            raise RuntimeError("No user is logged in.")

    # ------------------------------------------------------------------
    # Book CRUD (scoped to current user)
    # ------------------------------------------------------------------

    def get_specific_book(self, book_id):
        self._require_login()
        bt = self._books_table(self.current_user_id)
        self.cursor.execute(f"SELECT * FROM {bt} WHERE id = ?", (book_id,))
        return self.cursor.fetchone()

    def create_book(self, title=None, author=None, genre=None,
                    year=None, rating=None, status="to-read"):
        self._require_login()
        bt = self._books_table(self.current_user_id)
        if (title is None and author is None and genre is None
                and year is None and rating is None and status == "to-read"):
            self.cursor.execute(
                f"INSERT INTO {bt} (title, author, genre, year, rating, status) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                ("The Analects", "Confucius's Disciples", "Philosophy", -221, 4, "currently reading"),
            )
            self.connection.commit()
            return
        title  = (title  or "").strip()
        author = (author or "").strip()
        genre  = ((genre or "").strip()) or None
        self.cursor.execute(
            f"INSERT INTO {bt} (title, author, genre, year, rating, status) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (title, author, genre, year, rating, status),
        )
        self.connection.commit()

    def delete_book(self, book_id):
        self._require_login()
        bt = self._books_table(self.current_user_id)
        self.cursor.execute(f"DELETE FROM {bt} WHERE id = ?", (book_id,))
        self.connection.commit()

    def update_book(self, new_attributes, book_id, isRatingBeingUpdated):
        self._require_login()
        bt = self._books_table(self.current_user_id)
        if not isRatingBeingUpdated:
            self.cursor.execute(
                f"UPDATE {bt} SET title=?, author=?, genre=?, year=?, status=? WHERE id=?",
                (new_attributes[0], new_attributes[1], new_attributes[2],
                 int(new_attributes[3]), new_attributes[4].lower(), book_id),
            )
        else:
            self.cursor.execute(
                f"UPDATE {bt} SET rating=? WHERE id=?",
                (new_attributes[0], book_id),
            )
        self.connection.commit()

    def update_review(self, book_id, new):
        self._require_login()
        bt = self._books_table(self.current_user_id)
        self.cursor.execute(
            f"UPDATE {bt} SET review_content = ? WHERE id = ?", (new, book_id)
        )
        self.connection.commit()

    def delete_review(self, book_id):
        self._require_login()
        bt = self._books_table(self.current_user_id)
        self.cursor.execute(
            f"UPDATE {bt} SET review_content = NULL WHERE id = ?", (book_id,)
        )
        self.connection.commit()

    def get_book_count(self):
        self._require_login()
        bt = self._books_table(self.current_user_id)
        self.cursor.execute(f"SELECT COUNT(*) FROM {bt}")
        return self.cursor.fetchall()[0][0]

    def get_all_books(self, sort_by="id") -> List[Dict]:
        self._require_login()
        bt = self._books_table(self.current_user_id)
        col = self._safe_sort(sort_by)  # Fix 3
        self.cursor.execute(f"SELECT * FROM {bt} ORDER BY {col}")
        return [dict(row) for row in self.cursor.fetchall()]

    def get_books_by_status(self, status) -> List[Dict]:
        self._require_login()
        bt = self._books_table(self.current_user_id)
        if status == "All":
            self.cursor.execute(f"SELECT * FROM {bt} ORDER BY id")
        else:
            status_map = {"To Read": "to-read"}
            db_status = status_map.get(status, status.lower())
            self.cursor.execute(
                f"SELECT * FROM {bt} WHERE status = ? ORDER BY id", (db_status,)
            )
        return [dict(row) for row in self.cursor.fetchall()]

    def get_books_by_name(self, title, sort_by) -> List[Dict]:
        self._require_login()
        bt  = self._books_table(self.current_user_id)
        col = self._safe_sort(sort_by)  # Fix 3
        if title:
            self.cursor.execute(
                f"SELECT * FROM {bt} WHERE title = ? ORDER BY {col}", (title,)
            )
        else:
            self.cursor.execute(f"SELECT * FROM {bt} ORDER BY {col}")
        return [dict(row) for row in self.cursor.fetchall()]

    # ------------------------------------------------------------------
    # Genre helpers
    # ------------------------------------------------------------------

    def get_distinct_genres(self) -> List[str]:
        self._require_login()
        bt = self._books_table(self.current_user_id)
        self.cursor.execute(
            f"SELECT DISTINCT genre FROM {bt} WHERE genre IS NOT NULL ORDER BY genre"
        )
        return [row[0] for row in self.cursor.fetchall()]

    # ------------------------------------------------------------------
    # Tag helpers (Fix 1: now fully per-user)
    # ------------------------------------------------------------------

    def get_all_tags(self) -> List[Dict]:
        self._require_login()
        tt = self._tags_table(self.current_user_id)
        self.cursor.execute(f"SELECT id, label FROM {tt} ORDER BY label")
        return [dict(row) for row in self.cursor.fetchall()]

    def create_tag(self, label: str) -> int:
        self._require_login()
        tt = self._tags_table(self.current_user_id)
        label = label.strip()
        self.cursor.execute(f"INSERT OR IGNORE INTO {tt} (label) VALUES (?)", (label,))
        self.connection.commit()
        self.cursor.execute(f"SELECT id FROM {tt} WHERE label = ?", (label,))
        return self.cursor.fetchone()[0]

    def add_tag_to_book(self, book_id: int, tag_label: str):
        self._require_login()
        tag_id = self.create_tag(tag_label)
        btt = self._book_tags_table(self.current_user_id)
        self.cursor.execute(
            f"INSERT OR IGNORE INTO {btt} (book_id, tag_id) VALUES (?, ?)",
            (book_id, tag_id),
        )
        self.connection.commit()

    def remove_tag_from_book(self, book_id: int, tag_id: int):
        self._require_login()
        btt = self._book_tags_table(self.current_user_id)
        self.cursor.execute(
            f"DELETE FROM {btt} WHERE book_id = ? AND tag_id = ?",
            (book_id, tag_id),
        )
        self.connection.commit()

    def get_tags_for_book(self, book_id: int) -> List[Dict]:
        self._require_login()
        tt  = self._tags_table(self.current_user_id)
        btt = self._book_tags_table(self.current_user_id)
        self.cursor.execute(
            f"""SELECT t.id, t.label FROM {tt} t
                JOIN {btt} bt ON t.id = bt.tag_id
                WHERE bt.book_id = ?
                ORDER BY t.label""",
            (book_id,),
        )
        return [dict(row) for row in self.cursor.fetchall()]

    # ------------------------------------------------------------------
    # Combined filter
    # ------------------------------------------------------------------

    def get_filtered_books(
        self,
        status: Optional[str] = None,
        genre: Optional[str] = None,
        tag_ids: Optional[List[int]] = None,
        sort_by: str = "id",
    ) -> List[Dict]:
        self._require_login()
        bt  = self._books_table(self.current_user_id)
        btt = self._book_tags_table(self.current_user_id)
        col = self._safe_sort(sort_by)  # Fix 3

        conditions: List[str] = []
        params: List = []

        if status and status not in ("All", "Filter by status"):
            status_map = {
                "To Read": "to-read",
                "Completed": "completed",
                "Currently Reading": "currently reading",
            }
            conditions.append("b.status = ?")
            params.append(status_map.get(status, status.lower()))

        if genre and genre not in ("All Genres", "Filter by genre"):
            conditions.append("b.genre = ?")
            params.append(genre)

        if tag_ids:
            for tid in tag_ids:
                conditions.append(
                    f"EXISTS (SELECT 1 FROM {btt} bt "
                    f"WHERE bt.book_id = b.id AND bt.tag_id = ?)"
                )
                params.append(tid)

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        self.cursor.execute(
            f"SELECT b.* FROM {bt} b {where} ORDER BY b.{col}", params
        )
        return [dict(row) for row in self.cursor.fetchall()]

    # ------------------------------------------------------------------

    def close(self):
        if self.connection:
            self.connection.close()
            print("Database connection closed")


# ---------------------------------------------------------------------------
# Smoke-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import os
    test_db = "test_users.db"
    if os.path.exists(test_db): os.remove(test_db)

    db = DatabaseBackend(test_db)

    ok, msg = db.register_user("alice", "secret123")
    print(f"Register alice: {ok} – {msg}")

    ok, msg = db.login_user("alice", "secret123")
    print(f"Login alice: {ok} – {msg}")

    db.create_book("1984", "George Orwell", "Dystopian", 1949, 4.5, "completed")
    db.create_book("Dune", "Frank Herbert", "Sci-Fi", 1965, 5.0, "completed")
    print(f"Alice's books: {[b['title'] for b in db.get_all_books()]}")

    db.add_tag_to_book(1, "classic")
    print(f"Tags for book 1: {db.get_tags_for_book(1)}")

    db.register_user("bob", "pass456")
    db.logout_user()
    db.login_user("bob", "pass456")
    print(f"Bob's books (should be []): {db.get_all_books()}")
    print(f"Bob's tags (should be []): {db.get_all_tags()}")

    db.close()
    os.remove(test_db)
    print("All tests passed!")
