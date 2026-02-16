"""
Artifact: GUI.py
Description: Main entry point. Starts application. 
Authors: Cole Cooper
Date Created: 2/14/2026
Date Last Modified: 2/15/2026
Last Modified by: Cole Cooper
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
        self.load_books()

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

        # Add delete book button field
        deletion_frame = tk.Frame(self.root, bg="gray90")
        deletion_frame.pack(fill=tk.X, ipady=20)
        delete_book_button = tk.Button(deletion_frame, text="Delete a Book Entry", command=self.delete_book)
        delete_book_button.pack(side=tk.LEFT, padx=10, pady=10)

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
        """create book helper function"""
        self.db.create_book()
        self.load_books()

    def delete_book(self) :
        """delete book helper function"""
        self.db.delete_book()
        self.load_books()

    def load_books(self):
        # Get books from database
        books = self.db.get_all_books()
        
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


def main():
    root = tk.Tk()
    app = BookHuntGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
