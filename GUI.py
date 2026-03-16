"""
Artifact: GUI.py
Description: Main entry point. Starts application. 
Authors: Cole Cooper
Date Created: 2/14/2026
Date Last Modified: 2/15/2026
Last Modified by: Carson Abbott
"""

import tkinter as tk
from tkinter import ttk
import webbrowser
from urllib.parse import quote
from database import DatabaseBackend


class BookHuntGUI:    
    def __init__(self, root):
        self.root = root
        self.root.title("BookHunt")
        self.root.geometry("900x600")
        
        # Initialize database
        self.db = DatabaseBackend()

        #Initializes tags for filtering
        self._tag_id_map = {}
        self._pending_tags = []
        
        # Set up the GUI
        self.setup_ui()

        # Populate filter dropdown from Database
        self.refresh_genre_dropdown()
        self.refresh_tag_dropdown()
        
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

        # Add delete book button field
        deletion_frame = tk.Frame(self.root, bg="gray90")
        deletion_frame.pack(fill=tk.X, ipady=20)
        delete_book_button = tk.Button(deletion_frame, text="Delete a Book Entry", command=self.delete_book)
        delete_book_button.pack(side=tk.LEFT, padx=10, pady=10)
        
        # Add filter by status drop down
        dropdown_options = ["All", "Completed", "To Read", "Currently Reading"]
        self.status_dropdown = ttk.Combobox(filter_frame, values=dropdown_options, width=16, state="readonly")
        self.status_dropdown.set("All")
        self.status_dropdown.pack(side=tk.LEFT, padx=(0,16), pady=8)

        # Genre Filter
        tk.Label(filter_frame, text="Genre:", bg="gray90").pack(side=tk.LEFT, padx=(0, 2), pady=8)
        self.genre_dropdown = ttk.Combobox(filter_frame, values=["All Genres"], width=18, state="readonly")
        self.genre_dropdown.set("All Genres")
        self.genre_dropdown.pack(side=tk.LEFT, padx=(0, 16), pady=8)

        # Tag Filter
        tk.Label(filter_frame, text="Tag:", bg="gray90").pack(side=tk.LEFT, padx=(0, 2), pady=8)
        self.tag_dropdown = ttk.Combobox(filter_frame, values=["All Tags"], width=18, state="readonly")
        self.tag_dropdown.set("All Tags")
        self.tag_dropdown.pack(side=tk.LEFT, padx=(0, 16), pady=8)
 
        # -- Apply / Clear buttons --
        apply_filter_button = tk.Button(filter_frame, text="Apply Filter(s)", command=self.apply_filters)
        apply_filter_button.pack(side=tk.LEFT, padx=(0, 6), pady=8)
        clear_filter_button = tk.Button(filter_frame, text="Clear Filters", command=self.clear_filters)
        clear_filter_button.pack(side=tk.LEFT, pady=8)

        # Sorting options frame
        sorting_frame = tk.Frame(self.root, bg="gray90")
        sorting_frame.pack(fill=tk.X, ipady=4)
        tk.Label(sorting_frame, text="Sort by:", bg="gray90").pack(side=tk.LEFT, padx=(10, 2), pady=8)
        self.sorting_dropdown = ttk.Combobox(sorting_frame, values=["id", "title", "author", "genre", "year", "status"], width=18, state="readonly")
        self.sorting_dropdown.set("id")
        self.sorting_dropdown.pack(side=tk.LEFT, padx=(0, 16), pady=8)

        sorting_button = tk.Button(sorting_frame, text="Apply Sorting", command=self.apply_sorting)
        sorting_button.pack(side=tk.LEFT, padx=(0, 6), pady=8)

        # Search area
        searching_frame = tk.Frame(self.root, bg="gray90")
        searching_frame.pack(fill=tk.X, ipady=4)
        self.search_field = tk.Entry(searching_frame)
        self.search_field.pack(anchor="w", fill=tk.X, ipadx=100)
        search_button = tk.Button(searching_frame, text="Search for Title", command=self.search_book)
        search_button.pack(side=tk.LEFT, padx=(0, 6), pady=8)


        # Nearby bookstores section
        maps_frame = tk.Frame(self.root, bg="gray90")
        maps_frame.pack(fill=tk.X, ipady=10)

        tk.Label(maps_frame, text="Location:", bg="gray90").pack(side=tk.LEFT, padx=(10, 2))
        self.location_entry = tk.Entry(maps_frame, width=30)
        self.location_entry.pack(side=tk.LEFT, padx=(0, 10))

        find_bookstores_button = tk.Button(
            maps_frame,
            text="Find Nearby Bookstores",
            command=self.find_nearby_bookstores
        )
        find_bookstores_button.pack(side=tk.LEFT, padx=10, pady=5)

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
        self.load_books(self.db.get_all_books())

    def delete_book(self) :
        """delete book helper function"""
        self.db.delete_book()
        self.load_books(self.db.get_all_books())


    def find_nearby_bookstores(self):
        """Open Google Maps and search for nearby bookstores based on the entered location."""
        location = self.location_entry.get().strip() if hasattr(self, "location_entry") else ""

        if location == "":
            self.info_label.config(text="Please enter a location to find nearby bookstores.")
            return

        query = quote(f"bookstores near {location}")
        url = f"https://www.google.com/maps/search/{query}"
        webbrowser.open(url)

        self.info_label.config(text=f"Opening nearby bookstores for: {location}")

    def apply_filters(self):
        #Collect status, genre, and tag selections then reload the book list
        status = self.status_dropdown.get()
        genre = self.genre_dropdown.get()
        tag = self.tag_dropdown.get()
        # Convert single selected tag label to a tag_id list
        tag_ids = []
        if tag and tag != "All Tags":
            all_tags = self.db.get_all_tags()
            tag_ids = [t["id"] for t in all_tags if t["label"] == tag]
        self.load_books(self.db.get_filtered_books(status=status, genre=genre, tag_ids=tag_ids))

    def clear_filters(self):
        # Reset all filter controls and reload all books
        self.status_dropdown.set("All")
        self.genre_dropdown.set("All Genres")
        self.tag_dropdown.set("All Tags")
        self.load_books(self.db.get_all_books(self.sorting_dropdown.get()))

    def apply_sorting(self) :
        """apply the sorting to the table"""
        sorting = self.sorting_dropdown.get()
        self.load_books((self.db.get_all_books(sorting)))

    def search_book(self):
        book_title = self.search_field.get()
        self.load_books(self.db.get_books_by_name(book_title, self.sorting_dropdown.get()))


    def refresh_genre_dropdown(self):
        # Repopulate genre dropdown and tag listbox from the current DB state
        genres = ["All Genres"] + self.db.get_distinct_genres()
        self.genre_dropdown["values"] = genres
        if self.genre_dropdown.get() not in genres:
            self.genre_dropdown.set("All Genres")

    def refresh_tag_dropdown(self):
        """Repopulate tag dropdown from DB."""
        tags = ["All Tags"] + [t["label"] for t in self.db.get_all_tags()]
        self.tag_dropdown["values"] = tags
        if self.tag_dropdown.get() not in tags:
            self.tag_dropdown.set("All Tags")
 
    def _add_pending_tag(self):
        """Stage a tag for the book currently being created."""
        label = self.pending_tag_entry.get().strip()
        if not label or label in self._pending_tags:
            self.pending_tag_entry.delete(0, tk.END)
            return
        self._pending_tags.append(label)
        self.pending_tag_entry.delete(0, tk.END)
        self.pending_tags_label.config(text="Tags: " + ", ".join(self._pending_tags), fg="black")

    def load_books(self, books):
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
