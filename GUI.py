"""
Artifact: GUI.py
Description: Main entry point. Starts application. 
Authors: Cole Cooper
Date Created: 2/14/2026
Date Last Modified: 3/13/2026
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

        #Initializes tags for filtering
        self._tag_id_map = {}
        self._pending_tags = []
        
        # Set up the GUI
        self.setup_ui()

        # Populate filter dropdown from Database
        self.refresh_genre_dropdown()
        self.refresh_tag_dropdown()
        
        # Load example books
        self.load_books(self.db.get_all_books("id"))

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

        # setup review frame; actual review display is setup further down after treeview setup
        self.review_frame = tk.Frame(self.root, bg="SlateBlue3", height=80)
        self.review_frame.pack(fill=tk.X)
        self.review_content = tk.Label(
            self.review_frame,
            text="no reviews",
            font=("Arial", 16),
            bg="SlateBlue2",
            fg="white"
        )
        self.review_content.pack()


        # adds/edits to reviews made through this Entry
        self.review_entry = tk.Entry(self.review_frame)
        update_review_button = tk.Button(self.review_frame, text="Add/Update Review", command=lambda: self.update_review())
        delete_review_button = tk.Button(self.review_frame, text="Delete Review", command=lambda: self.delete_review())

        update_review_button.pack(side=tk.LEFT)
        self.review_entry.pack(side=tk.LEFT)
        delete_review_button.pack(side=tk.LEFT, padx=(20, 0))

        # Right click menu for tree view
        self.tree_menu = tk.Menu(self.root, tearoff=0)
        self.tree_menu.add_command(label="Delete Book", command=self.delete_book)
        self.tree_menu.add_command(label="Edit Book", command=self.edit_book_toplevel)

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

        # Tag entry row
        tag_entry_frame = tk.Frame(self.root, bg="gray90")
        tag_entry_frame.pack(fill=tk.X, ipady=4)
        tk.Label(tag_entry_frame, text="Tags:", bg="gray90").pack(side=tk.LEFT, padx=(10, 2))
        self.pending_tag_entry = tk.Entry(tag_entry_frame, width=18)
        self.pending_tag_entry.pack(side=tk.LEFT, padx=(0, 4))
        self.pending_tag_entry.bind("<Return>", lambda e: self._add_pending_tag())
        tk.Button(tag_entry_frame, text="Add Tag", command=self._add_pending_tag).pack(side=tk.LEFT, padx=(0, 10))
        self.pending_tags_label = tk.Label(tag_entry_frame, text="No tags added yet.", bg="gray90", fg="gray50")
        self.pending_tags_label.pack(side=tk.LEFT)

        # Filters
        filter_frame = tk.Frame(self.root, bg="gray90")
        filter_frame.pack(fill=tk.X, ipady=4)

        # Status Filter
        tk.Label(filter_frame, text="Status:", bg="gray90").pack(side=tk.LEFT, padx=(10, 2), pady=8)
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
        
        columns = ("ID #", "Title", "Author", "Genre", "Year", "Rating", "Status")
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            yscrollcommand=scrollbar.set
        )
        scrollbar.config(command=self.tree.yview)
        
        # Configure columns
        self.tree.column("ID #", width=25)
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

        # the mainloop will run self.on_tree_select() when an item is selected in the TreeView
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        # Bind right click event to the tree to access edit (and eventually delete) book functionality
        self.tree.bind("<Button-3>", self.tree_right_click)

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

        # Attach any pending tags to the new book
        if self._pending_tags:
            new_book_id = self.db.get_all_books("id")[-1]["id"]
            for tag_label in self._pending_tags:
                self.db.add_tag_to_book(new_book_id, tag_label)
            self._pending_tags = []
            self.pending_tags_label.config(text="No tags added yet.", fg="gray50")

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

        self.refresh_genre_dropdown()
        self.refresh_tag_dropdown()
        self.load_books(self.db.get_all_books())

    def delete_book(self) :
        """delete book helper function"""
        self.db.delete_book(self.sel_book_id)
        self.clear_treeview()
        self.load_books(self.db.get_all_books())

    def update_review(self):
        new = self.review_entry.get()

        # for now it just will take the first book selected, im not sure how selecting
        # a lot of books will affect the UI yet
        selected = self.tree.selection()[0]

        # there may be a case where all books are unselected? im not sure and i dont
        # really care to test it right now
        if not selected:
            return

        self.sel_book_id = self.tree.item(selected, "values")[0]
        self.db.update_review(self.sel_book_id, new)

        book_review = self.db.get_specific_book(self.sel_book_id)[6]

        if not book_review:
            book_review = "No review yet."

        self.review_content.config(text=book_review)

    def delete_review(self):
        # for now it just will take the first book selected, im not sure how selecting
        # a lot of books will affect the UI yet
        selected = self.tree.selection()[0]

        # there may be a case where all books are unselected? im not sure and i dont
        # really care to test it right now
        if not selected:
            return

        self.sel_book_id = self.tree.item(selected, "values")[0]
        self.db.delete_review(self.sel_book_id)

        book_review = self.db.get_specific_book(self.sel_book_id)[6]

        if not book_review:
            book_review = "No review yet."

        self.review_content.config(text=book_review)

    def edit_book_toplevel(self):
        """use old attributes to get book item, display window for new attributes, make change"""

        #get all the attributes of the book entity
        old_book_info = self.db.get_specific_book(self.sel_book_id)

        #create a pop-up window for the user to specify new attributes and then apply the edit
        self.display_edit_window(old_book_info)



    def display_edit_window(self, old_attributes):
        """create pop-up window, get user input, apply user input data to updating the book entry"""

        #create the pop-up window, force focus onto it, and prevent user from interacting with main window while pop-up is up
        edit_window = tk.Toplevel(self.root)
        edit_window.title("Edit Book Entity")
        edit_window.geometry("500x450")
        edit_window.attributes('-topmost', True)
        edit_window.focus_force()
        edit_window.grab_set()

        #create the frame where the entry fields will be
        entry_frame = tk.Frame(edit_window)
        entry_frame.pack(fill=tk.BOTH, expand=True)

        #create a label giving user interaction instructions
        tk.Label(entry_frame, text="Enter New Attributes for Book", font=("Arial", 20, "bold")).pack(side=tk.TOP)

        #create the entry fields
        title_field = tk.Entry(entry_frame)
        author_field = tk.Entry(entry_frame)
        genre_field = tk.Entry(entry_frame)
        year_field = tk.Entry(entry_frame)
        status_field = ttk.Combobox(entry_frame, values=["To Read", "Currently Reading", "Completed"])

        #give the entry fields labels and actually pack them
        tk.Label(entry_frame, text="Enter Book Title:").pack(anchor="w")
        title_field.pack(anchor="w", fill=tk.X, ipadx=100)
        tk.Label(entry_frame, text="Enter Author Name:").pack(anchor="w")
        author_field.pack(anchor="w", fill=tk.X, ipadx=100)
        tk.Label(entry_frame, text="Enter Book Genre:").pack(anchor="w")
        genre_field.pack(anchor="w", fill=tk.X, ipadx=100)
        tk.Label(entry_frame, text="Enter Year Published:").pack(anchor="w")
        year_field.pack(anchor="w", fill=tk.X, ipadx=100)
        tk.Label(entry_frame, text="Enter Reading Status:").pack(anchor="w")
        status_field.pack(anchor="w")

        # create a list to hold the references to the text boxes to be passed to apply_edit function
        text_field_references = [title_field, author_field, genre_field, year_field, status_field]

        #create the frame where the buttons show up, create the buttons, and then finally pack the frame and buttons
        button_frame = tk.Frame(edit_window, bg="gray90")
        cancel_button = tk.Button(button_frame, text="Cancel Edit", command=edit_window.destroy) #If not applying edit, simply destroy the window, no change
        submit_button = tk.Button(button_frame, text="Apply Edit", command=lambda: self.apply_edit(text_field_references, edit_window)) #Apply edit, destroy window afterward
        button_frame.pack(side=tk.BOTTOM, fill=tk.X)
        cancel_button.pack(side=tk.LEFT, padx=10, pady=10)
        submit_button.pack(side=tk.RIGHT, padx=10, pady=10)

    def apply_edit(self, text_fields, window) :
        """get the new attributes from the given entry field references, apply the edit"""

        #create list to hold the text to be used for constructing query
        new_attributes = []

        #loop through text references to get the input text
        for field in text_fields :
            new_attributes.append(field.get())

        #call database function to edit the entry with these new attributes
        self.db.update_book(new_attributes, self.sel_book_id)

        #after applying the update, destroy the window
        window.destroy()

        #update the list display to reflect new edited book
        self.clear_treeview()
        self.load_books(self.db.get_all_books("id"))

    def on_tree_select(self, event):
        # for now it just will take the first book selected, im not sure how selecting
        # a lot of books will affect the UI yet
        selected = self.tree.selection()[0]

        # there may be a case where all books are unselected? im not sure and i dont
        # really care to test it right now
        if not selected:
            return

        self.sel_book_id = self.tree.item(selected, "values")[0]
        book_review = self.db.get_specific_book(self.sel_book_id)[6]

        if not book_review:
            book_review = "No review yet."

        self.review_content.config(text=book_review)


    def tree_right_click(self, event):
        """grab info of hovered book, display options to interact with it"""

        #if the click occurred on top of a book item in the tree, get the tree item id
        tree_item_id = self.tree.identify_row(event.y)

        #if we are not selecting a book item, there is no action to take
        if not tree_item_id :
            return

        #visually select the item we are supposed to be hovering over
        self.tree.selection_set(tree_item_id)

        #get the id of the book entity we are hovering over
        self.sel_book_id = self.tree.item(tree_item_id, "values")[0]

        #display the pop-up menu to delete or edit the book item
        self.tree_menu.post(event.x_root, event.y_root)
        self.tree_menu.grab_release()


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
        self.load_books(self.db.get_all_books("id"))

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
        # Prevent duplicate rows when reloading
        self.clear_treeview()
        # Update info label
        num_books = self.db.get_book_count()
        self.info_label.config(text=f"Your Book Collection ({num_books} books)")
        
        # Reset the book mapping
        self.book_mapping = {}

        # Insert books into table
        for idx, book in enumerate(books):
            self.book_mapping[idx] = book
            tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
            
            # Format rating
            rating_str = f"{book['rating']}/5" if book['rating'] else "N/A"
            
            # Format status
            status = book['status'].replace('-', ' ').title()
            
            values = (
                book['id'],
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
