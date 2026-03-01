"""
Artifact: GUI.py
Description: Main entry point. Starts application. 
Authors: Cole Cooper
Date Created: 2/14/2026
Date Last Modified: 2/28/2026
Last Modified by: Ebraheem AlAamer
"""

import tkinter as tk
from tkinter import ttk
from database import DatabaseBackend


class BookHuntGUI:    
    def __init__(self, root):
        self.root = root
        self.root.title("BookHunt")
        self.root.geometry("900x600")
        
        # Initialize database
        self.db = DatabaseBackend()
        
        # Set up the GUI
        self.setup_ui()
        
        # Load example books
        self.load_books(self.db.get_all_books())

    def setup_ui(self):
        # Title
        title_frame = tk.Frame(self.root, bg="SlateBlue3", height=80)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame, 
            text="BookHunt", 
            font=("Arial", 24, "bold"),
            bg="SlateBlue3",
            fg="white"
        )
        title_label.pack(expand=True)

        # Add create book button field
        creation_frame = tk.Frame(self.root, bg="gray90")
        creation_frame.pack(fill=tk.X, ipady=20)
        create_book_button = tk.Button(creation_frame, text="Create a Book Entry", command=self.create_book)
        create_book_button.pack(side=tk.LEFT, padx=10, pady=10)

        # --- Book attribute input fields (used by Create a Book Entry) ---
        tk.Label(creation_frame, text="Title:", bg="gray90").pack(side=tk.LEFT, padx=(10, 2))
        self.title_entry = tk.Entry(creation_frame, width=18)
        self.title_entry.pack(side=tk.LEFT, padx=(0, 10))

        tk.Label(creation_frame, text="Author:", bg="gray90").pack(side=tk.LEFT, padx=(0, 2))
        self.author_entry = tk.Entry(creation_frame, width=18)
        self.author_entry.pack(side=tk.LEFT, padx=(0, 10))

        tk.Label(creation_frame, text="Genre:", bg="gray90").pack(side=tk.LEFT, padx=(0, 2))
        self.genre_entry = tk.Entry(creation_frame, width=14)
        self.genre_entry.pack(side=tk.LEFT, padx=(0, 10))

        tk.Label(creation_frame, text="Year:", bg="gray90").pack(side=tk.LEFT, padx=(0, 2))
        self.year_entry = tk.Entry(creation_frame, width=6)
        self.year_entry.pack(side=tk.LEFT, padx=(0, 10))

        tk.Label(creation_frame, text="Rating:", bg="gray90").pack(side=tk.LEFT, padx=(0, 2))
        self.rating_entry = tk.Entry(creation_frame, width=6)
        self.rating_entry.pack(side=tk.LEFT, padx=(0, 10))

        tk.Label(creation_frame, text="Status:", bg="gray90").pack(side=tk.LEFT, padx=(0, 2))
        self.create_status_dropdown = ttk.Combobox(
            creation_frame,
            values=["to-read", "completed", "currently reading"],
            width=16,
            state="readonly"
        )
        self.create_status_dropdown.set("to-read")
        self.create_status_dropdown.pack(side=tk.LEFT, padx=(0, 10))

        # Add delete book button field
        deletion_frame = tk.Frame(self.root, bg="gray90")
        deletion_frame.pack(fill=tk.X, ipady=20)
        delete_book_button = tk.Button(deletion_frame, text="Delete a Book Entry", command=self.delete_book)
        delete_book_button.pack(side=tk.LEFT, padx=10, pady=10)
        
        # Add filter by status drop down
        dropdown_options = ["All", "Completed", "To Read", "Currently Reading"]
        status_frame = tk.Frame(self.root, bg="gray90")
        status_frame.pack(fill=tk.X, ipady=20)
        status_dropdown = ttk.Combobox(status_frame, values=dropdown_options)
        status_dropdown.set("Filter by status")
        status_dropdown.pack(side=tk.RIGHT, padx=10, pady=10)

        # Add apply filter button field
        apply_filter_frame = tk.Frame(self.root, bg="gray90")
        apply_filter_frame.pack(fill=tk.X, ipady=1)
        apply_filter_button = tk.Button(apply_filter_frame, text="Apply Filter(s)", command=lambda: self.apply_filters(status_dropdown.get()))
        apply_filter_button.pack(side=tk.RIGHT, padx=10, pady=10)

        # Main content area
        content_frame = tk.Frame(self.root, bg="gray90")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Info label
        self.info_label = tk.Label(
            content_frame,
            text="Your Book Collection",
            font=("Arial", 14, "bold"),
            bg="gray90"
        )
        self.info_label.pack(pady=(0, 10))

        # Basic setup like scroll bar and book tree
        tree_frame = tk.Frame(content_frame, bg="gray90")
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        columns = ("Title", "Author", "Genre", "Year", "Rating", "Status")
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            yscrollcommand=scrollbar.set
        )
        scrollbar.config(command=self.tree.yview)
        
        # Configure columns
        self.tree.column("Title", width=200)
        self.tree.column("Author", width=150)
        self.tree.column("Genre", width=120)
        self.tree.column("Year", width=80)
        self.tree.column("Rating", width=80)
        self.tree.column("Status", width=120)
        
        # Configure headings
        for col in columns:
            self.tree.heading(col, text=col)
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Alternate the row colors
        self.tree.tag_configure('oddrow', background='white')
        self.tree.tag_configure('evenrow', background='gray95')

    def create_book(self) :
        """create book helper function

        Uses the text entry fields next to the Create button (title/author/etc.) as parameters
        to the database INSERT. If the fields don't exist for any reason, it falls back to
        the original behavior (hardcoded example insert).
        """
        # Backwards-compatible fallback
        if not hasattr(self, "title_entry") or not hasattr(self, "author_entry"):
            self.db.create_book()
            self.load_books(self.db.get_all_books())
            return

        title = self.title_entry.get().strip()
        author = self.author_entry.get().strip()
        genre = self.genre_entry.get().strip() if hasattr(self, "genre_entry") else ""

        # Validate required fields
        if title == "" or author == "":
            self.info_label.config(text="Title and Author are required to create a book.")
            return

        # Optional conversions
        year_raw = self.year_entry.get().strip() if hasattr(self, "year_entry") else ""
        year = None
        if year_raw != "":
            try:
                year = int(year_raw)
            except ValueError:
                self.info_label.config(text="Year must be an integer (e.g., 2024).")
                return

        rating_raw = self.rating_entry.get().strip() if hasattr(self, "rating_entry") else ""
        rating = None
        if rating_raw != "":
            try:
                rating = float(rating_raw)
            except ValueError:
                self.info_label.config(text="Rating must be a number (e.g., 4 or 4.5).")
                return

        status = self.create_status_dropdown.get().strip() if hasattr(self, "create_status_dropdown") else "to-read"
        if status == "":
            status = "to-read"

        # Create in DB using user-provided values
        self.db.create_book(title, author, genre, year, rating, status)

        # Clear inputs after successful insert
        self.title_entry.delete(0, tk.END)
        self.author_entry.delete(0, tk.END)
        if hasattr(self, "genre_entry"):
            self.genre_entry.delete(0, tk.END)
        if hasattr(self, "year_entry"):
            self.year_entry.delete(0, tk.END)
        if hasattr(self, "rating_entry"):
            self.rating_entry.delete(0, tk.END)
        if hasattr(self, "create_status_dropdown"):
            self.create_status_dropdown.set("to-read")

        self.load_books(self.db.get_all_books())

    def delete_book(self) :
        """delete book helper function"""
        self.db.delete_book()
        self.load_books(self.db.get_all_books())

    def apply_filters(self, selectedStatus):
        """apply filters helper function"""
        self.clear_treeview()
        self.load_books(self.db.get_books_by_status(selectedStatus))

    def load_books(self, books):
        # Prevent duplicate rows when reloading
        self.clear_treeview()
        # Update info label
        self.info_label.config(text=f"Your Book Collection ({len(books)} books)")
        
        # Insert books into table
        for idx, book in enumerate(books):
            tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
            
            # Format rating
            rating_str = f"{book['rating']}/5" if book['rating'] else "N/A"
            
            # Format status
            status = book['status'].replace('-', ' ').title()
            
            values = (
                book['title'],
                book['author'],
                book['genre'] or "N/A",
                book['year'] or "N/A",
                rating_str,
                status
            )
            
            self.tree.insert(
                "",
                tk.END,
                values=values,
                tags=(tag,)
            )
    
    def clear_treeview(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
    

def main():
    root = tk.Tk()
    app = BookHuntGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
