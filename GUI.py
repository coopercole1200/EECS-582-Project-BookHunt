"""
Artifact: GUI.py
Description: Main entry point. Starts application. 
Authors: Cole Cooper
Date Created: 2/14/2026
Date Last Modified: 3/29/2026
Last Modified by: Ebraheem AlAamer
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import webbrowser
#from tkinter import ttk
from urllib.parse import quote
from openai import OpenAI
import os
from dotenv import load_dotenv

from database import DatabaseBackend
# ─────────────────────────────────────────────────────────────────────────────
# Colour constants (keep consistent with the rest of the app)
# ─────────────────────────────────────────────────────────────────────────────
ACCENT      = "SlateBlue3"
ACCENT_DARK = "SlateBlue4"
BG          = "gray90"


# ═════════════════════════════════════════════════════════════════════════════
# 2.2 – Sign-in / Register screen
# ═════════════════════════════════════════════════════════════════════════════

class SignInScreen:
    """
    Shown at launch.  The user must sign in (or register) before the main
    BookHuntGUI is displayed.  Uses the same root window to avoid a second
    Toplevel.
    """

    def __init__(self, root: tk.Tk, db: DatabaseBackend, on_success):
        self.root       = root
        self.db         = db
        self.on_success = on_success   # callback(username) called after login

        self.root.title("BookHunt – Sign In")
        self.root.geometry("420x480")
        self.root.resizable(False, False)

        self._build()

    # ------------------------------------------------------------------
    # Build the sign-in UI
    # ------------------------------------------------------------------

    def _build(self):
        self.frame = tk.Frame(self.root, bg=BG)
        self.frame.pack(fill=tk.BOTH, expand=True)

        # ── Header banner ──────────────────────────────────────────────
        banner = tk.Frame(self.frame, bg=ACCENT, height=90)
        banner.pack(fill=tk.X)
        banner.pack_propagate(False)

        tk.Label(
            banner,
            text="📚  BookHunt  📚",
            font=("Arial", 28, "bold"),
            bg=ACCENT,
            fg="white",
        ).pack(expand=True)

        # ── Card frame (centred) ───────────────────────────────────────
        card = tk.Frame(self.frame, bg="white", relief="flat", bd=0)
        card.place(relx=0.5, rely=0.52, anchor="center", width=340)

        # Mode label ("Sign In" / "Create Account")
        self._mode_var = tk.StringVar(value="Sign In")
        self._mode_label = tk.Label(
            card,
            textvariable=self._mode_var,
            font=("Arial", 17, "bold"),
            bg="white",
            fg=ACCENT_DARK,
        )
        self._mode_label.grid(row=0, column=0, columnspan=2,
                              pady=(22, 14), padx=24, sticky="w")

        # Username
        tk.Label(card, text="Username", font=("Arial", 10),
                 bg="white", fg="#444").grid(
            row=1, column=0, columnspan=2, sticky="w", padx=24)

        self._username_var = tk.StringVar()
        username_entry = tk.Entry(
            card, textvariable=self._username_var,
            font=("Arial", 12), relief="solid", bd=1, width=28,
        )
        username_entry.grid(row=2, column=0, columnspan=2,
                            padx=24, pady=(2, 10), ipady=5)
        username_entry.bind("<Return>", lambda e: self._password_entry.focus())

        # Password
        tk.Label(card, text="Password", font=("Arial", 10),
                 bg="white", fg="#444").grid(
            row=3, column=0, columnspan=2, sticky="w", padx=24)

        self._password_var = tk.StringVar()
        self._password_entry = tk.Entry(
            card, textvariable=self._password_var,
            font=("Arial", 12), relief="solid", bd=1, width=28,
            show="•",
        )
        self._password_entry.grid(row=4, column=0, columnspan=2,
                                   padx=24, pady=(2, 4), ipady=5)
        self._password_entry.bind("<Return>", lambda e: self._submit())

        # Error / info message
        self._msg_var = tk.StringVar()
        self._msg_label = tk.Label(
            card, textvariable=self._msg_var,
            font=("Arial", 9), bg="white", fg="red",
            wraplength=290, justify="left",
        )
        self._msg_label.grid(row=5, column=0, columnspan=2,
                              padx=24, pady=(0, 6), sticky="w")

        # Primary action button
        self._btn_text = tk.StringVar(value="Sign In")
        self._action_btn = tk.Button(
            card,
            textvariable=self._btn_text,
            font=("Arial", 12, "bold"),
            bg=ACCENT, fg="white", activebackground=ACCENT_DARK,
            activeforeground="white", relief="flat", cursor="hand2",
            command=self._submit,
        )
        self._action_btn.grid(row=6, column=0, columnspan=2,
                              padx=24, pady=(4, 10), sticky="ew", ipady=7)

        # Toggle link
        toggle_frame = tk.Frame(card, bg="white")
        toggle_frame.grid(row=7, column=0, columnspan=2, pady=(0, 22))

        self._toggle_prompt = tk.StringVar(value="Don't have an account?")
        tk.Label(toggle_frame, textvariable=self._toggle_prompt,
                 font=("Arial", 9), bg="white", fg="#555").pack(side=tk.LEFT)

        self._toggle_link_text = tk.StringVar(value=" Register")
        toggle_link = tk.Label(
            toggle_frame, textvariable=self._toggle_link_text,
            font=("Arial", 9, "underline"), bg="white",
            fg=ACCENT_DARK, cursor="hand2",
        )
        toggle_link.pack(side=tk.LEFT)
        toggle_link.bind("<Button-1>", lambda e: self._toggle_mode())

        # Track which mode we're in
        self._is_register = False

        # Focus username field
        username_entry.focus()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _toggle_mode(self):
        self._is_register = not self._is_register
        self._msg_var.set("")

        if self._is_register:
            self._mode_var.set("Create Account")
            self._btn_text.set("Register")
            self._toggle_prompt.set("Already have an account?")
            self._toggle_link_text.set(" Sign In")
        else:
            self._mode_var.set("Sign In")
            self._btn_text.set("Sign In")
            self._toggle_prompt.set("Don't have an account?")
            self._toggle_link_text.set(" Register")

    def _submit(self):
        username = self._username_var.get().strip()
        password = self._password_var.get()

        if not username or not password:
            self._msg_var.set("Please fill in both fields.")
            return

        if self._is_register:
            ok, msg = self.db.register_user(username, password)
            if ok:
                # Auto-login after successful registration
                self.db.login_user(username, password)
                self._proceed()
            else:
                self._msg_var.set(msg)
        else:
            ok, msg = self.db.login_user(username, password)
            if ok:
                self._proceed()
            else:
                self._msg_var.set(msg)

    def _proceed(self):
        """Tear down this screen and launch the main application."""
        self.frame.destroy()
        self.on_success(self.db.current_username)

class BookHuntGUI:    
    def __init__(self, root, db):
        self.root = root
        self.root.title("BookHunt")
        self.root.geometry("900x800")
        
        # Initialize database
        self.db = db

        #Initializes tags for filtering
        self._tag_id_map = {}
        self._pending_tags = []
        
        # Set up the GUI
        self.setup_ui()

        # Populate filter dropdown from Database
        self.refresh_genre_dropdown()
        self.refresh_tag_dropdown()

        # Boolean to track user allowing recommendation agent to access the book entries
        self.agent_optin = False
        
        # Load example books
        self.load_books(self.db.get_all_books("id"))

    def setup_ui(self):
        ### Title ###
        title_frame = ttk.Frame(self.root, bootstyle='primary', height=120)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        title_label = ttk.Label(
            title_frame, 
            text="📚  BookHunt  📚", 
            font=("Arial", 36, "bold"),
            bootstyle='inverse-primary'
        )
        title_label.pack(expand=True)

        right_header = ttk.Frame(title_frame, bootstyle='primary')
        right_header.pack(side=tk.RIGHT, padx=16)

        ttk.Label(
            right_header,
            text=f"👤  {self.db.current_username}",
            font=("Arial", 11),
            bootstyle='inverse-primary'
        ).pack(anchor="e")

        ttk.Button(
            right_header,
            text="Log Out",
            cursor='hand2',
            bootstyle='danger',
            command=self._logout,
        ).pack(anchor="e", padx=5, pady=(2, 4))

        ### Frame Structure ###
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        notebook = ttk.Notebook(main_frame, bootstyle="light")
        notebook.pack(fill=tk.BOTH, expand=True)

        ## TAB 1 ##
        tab1 = tk.Frame(notebook, bg="gray90")
        notebook.add(tab1, text="Search")

        # Search area #
        searching_frame = tk.Frame(tab1, bg="gray90")
        searching_frame.pack(fill=tk.X, pady=5)
        self.search_field = tk.Entry(searching_frame)
        self.search_field.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        search_button = ttk.Button(searching_frame, text="Search for Title", cursor="hand2", bootstyle='primary', command=self.search_book)
        search_button.pack(side=tk.LEFT, padx=(0, 6), pady=8)

        options_outer = ttk.Labelframe(tab1, text=" Advanced Search Options ", bootstyle='primary')
        options_outer.pack(fill=tk.X, padx=10, pady=(6, 2))
        
        # Filters #
        filter_frame = tk.Frame(options_outer, bg="gray90")
        filter_frame.pack(fill=tk.X)

        # Status Filter #
        tk.Label(filter_frame, text="Status:", bg="gray90").pack(side=tk.LEFT, padx=5)
        dropdown_options = ["All", "Completed", "To Read", "Currently Reading"]
        self.status_dropdown = ttk.Combobox(filter_frame, values=dropdown_options, width=15, state="readonly")
        self.status_dropdown.set("All")
        self.status_dropdown.pack(side=tk.LEFT, padx=5)

        # Genre Filter #
        tk.Label(filter_frame, text="Genre:", bg="gray90").pack(side=tk.LEFT, padx=5)
        self.genre_dropdown = ttk.Combobox(filter_frame, values=["All Genres"], width=15, state="readonly")
        self.genre_dropdown.set("All Genres")
        self.genre_dropdown.pack(side=tk.LEFT, padx=5)

        # Tag Filter #
        tk.Label(filter_frame, text="Tag:", bg="gray90").pack(side=tk.LEFT, padx=5)
        self.tag_dropdown = ttk.Combobox(filter_frame, values=["All Tags"], width=15, state="readonly")
        self.tag_dropdown.set("All Tags")
        self.tag_dropdown.pack(side=tk.LEFT, padx=5)
 
        # Apply / Clear buttons #
        apply_filter_button = ttk.Button(filter_frame, text="Apply Filter(s)", cursor='hand2', bootstyle='dark-outline', command=self.apply_filters)
        apply_filter_button.pack(side=tk.LEFT, padx=10)
        clear_filter_button = ttk.Button(filter_frame, text="Clear Filters", cursor='hand2', bootstyle='warning-outline', command=self.clear_filters)
        clear_filter_button.pack(side=tk.LEFT)

        # Sorting options frame #
        sorting_frame = tk.Frame(options_outer, bg="gray90")
        sorting_frame.pack(fill=tk.X, pady=5)
        tk.Label(sorting_frame, text="Sort by:", bg="gray90").pack(side=tk.LEFT, padx=5)
        self.sorting_dropdown = ttk.Combobox(sorting_frame, values=["id", "title", "author", "genre", "year", "status"], width=15, state="readonly")
        self.sorting_dropdown.set("id")
        self.sorting_dropdown.pack(side=tk.LEFT, padx=5)

        sorting_button = ttk.Button(sorting_frame, text="Apply Sorting", cursor='hand2', bootstyle='dark-outline', command=self.apply_sorting)
        sorting_button.pack(side=tk.LEFT, padx=10)

        ## Tab 2 ##
        tab2 = tk.Frame(notebook, bg="gray90")
        notebook.add(tab2, text="Add")

        creation_outer = ttk.Labelframe(tab2, text=" Add to Book Collection ", bootstyle='primary')
        creation_outer.pack(fill=tk.X, padx=10, pady=(6, 2))

        # Add create book button field #
        creation_frame = tk.Frame(creation_outer, bg="gray90")
        creation_frame.pack(fill=tk.X, pady=5)

        row1 = ttk.Frame(creation_frame)
        row1.pack(fill=tk.X)

        row2 = ttk.Frame(creation_frame)
        row2.pack(fill=tk.X, pady=(5, 0))
        
        row3 = ttk.Frame(creation_frame)
        row3.pack(fill=tk.X, pady=(5, 0))

        # --- Book attribute input fields (used by Create a Book Entry) --- #
        tk.Label(row1, text="Title:", bg="gray90").pack(side=tk.LEFT, padx=(10, 2))
        self.title_entry = tk.Entry(row1, width=15)
        self.title_entry.pack(side=tk.LEFT, padx=5)

        tk.Label(row1, text="Author:", bg="gray90").pack(side=tk.LEFT, padx=(0, 2))
        self.author_entry = tk.Entry(row1, width=15)
        self.author_entry.pack(side=tk.LEFT, padx=5)

        tk.Label(row1, text="Genre:", bg="gray90").pack(side=tk.LEFT, padx=(0, 2))
        self.genre_entry = tk.Entry(row1, width=12)
        self.genre_entry.pack(side=tk.LEFT, padx=5)

        tk.Label(row1, text="Year:", bg="gray90").pack(side=tk.LEFT, padx=(0, 2))
        self.year_entry = tk.Entry(row1, width=6)
        self.year_entry.pack(side=tk.LEFT, padx=5)

        tk.Label(row2, text="Rating:", bg="gray90").pack(side=tk.LEFT, padx=(10, 2))
        self.rating_entry = tk.Entry(row2, width=6)
        self.rating_entry.pack(side=tk.LEFT, padx=5)

        tk.Label(row2, text="Status:", bg="gray90").pack(side=tk.LEFT, padx=(0, 2))
        self.create_status_dropdown = ttk.Combobox(
            row2,
            values=["to read", "completed", "currently reading"],
            width=15,
            state="readonly"
        )
        self.create_status_dropdown.set("to read")
        self.create_status_dropdown.pack(side=tk.LEFT, padx=5)

        create_book_button = ttk.Button(creation_frame, text="Create a Book Entry", bootstyle='primary', command=self.create_book)
        create_book_button.pack(side=tk.LEFT, pady=10, padx=10)

        # Tag entry row #
        tag_entry_frame = tk.Frame(tab2, bg="gray90")
        tag_entry_frame.pack(fill=tk.X)
        tk.Label(row3, text="Tags:", bg="gray90").pack(side=tk.LEFT, padx=(10, 2))
        self.pending_tag_entry = tk.Entry(row3, width=20)
        self.pending_tag_entry.pack(side=tk.LEFT, padx=5)
        self.pending_tag_entry.bind("<Return>", lambda e: self._add_pending_tag())
        ttk.Button(row3, text="Add Tag", bootstyle='dark-outline', command=self._add_pending_tag).pack(side=tk.LEFT)
        self.pending_tags_label = tk.Label(row3, text="No tags added yet.", bg="gray90", fg="gray50")
        self.pending_tags_label.pack(side=tk.LEFT, padx=10)

        ## Tab 3 ##
        tab3 = tk.Frame(notebook, bg="gray90")
        notebook.add(tab3, text="Review")

        review_outer = ttk.Labelframe(tab3, text=" Current Review of Selected Book ", bootstyle='primary')
        review_outer.pack(fill=tk.X, padx=10, pady=(6, 2))

        # setup review frame; actual review display is setup further down after treeview setup #
        self.review_frame = tk.Frame(review_outer)
        self.review_frame.pack(fill=tk.X, pady=10)
        #tk.Label(self.review_frame, text="Current Review", font=("Arial", 16, "underline")).pack(side=tk.TOP)
        self.review_content = tk.Label(
            self.review_frame,
            text="Double click on your book in the view below to see all your reviews!",
            font=("Arial", 14),
            bg="SlateBlue2",
            fg="white"
        )
        self.review_content.pack()


        # adds/edits to reviews made through this Entry #
        selectedStarValue = tk.IntVar(value=0)

        ttk.Label(
            self.review_frame,
            text="Enter Review: ",
            bootstyle='default'
        ).pack(side=tk.LEFT, padx=(10, 5))
        self.review_entry = tk.Entry(self.review_frame)
        self.review_stars = tk.Frame(self.review_frame)
        update_review_button = ttk.Button(self.review_frame, text="Add Review", cursor='hand2', bootstyle='primary', command=lambda: self.create_review(selectedStarValue))
        delete_review_button = ttk.Button(self.review_frame, text="Delete Review", cursor='hand2', bootstyle='warning-outline', command=lambda: self.delete_review())

        self.review_entry.pack(side=tk.LEFT)
        ttk.Label(
            self.review_frame,
            text="Enter Rating (out of 5): ",
            bootstyle='default'
        ).pack(side=tk.LEFT, padx=(10, 5))
        self.review_stars.pack(side=tk.LEFT, padx=(5, 0))
        starButtons = [("0", 0), ("1", 1), ("2", 2), ("3", 3), ("4", 4), ("5", 5)]
        for i, (text, val) in enumerate(starButtons):
            ttk.Radiobutton(self.review_stars, text=text, variable=selectedStarValue, value=val).grid(row=0, column=i, padx=5)

        update_review_button.pack(side=tk.LEFT, padx=(10, 0))
        delete_review_button.pack(side=tk.LEFT, padx=(10, 0))

        ## TAB 4 ##
        tab4 = tk.Frame(notebook, bg="gray90")
        notebook.add(tab4, text="Hunt!")

        # Ask for agent recommendation button
        agent_outer = ttk.Labelframe(tab4, text=" Get Book Recomendations ", bootstyle='primary')
        agent_outer.pack(fill=tk.X, padx=10, pady=(6, 2))
        agent_access_frame = tk.Frame(agent_outer, bg="gray90")
        agent_access_frame.pack(fill=tk.X, ipady=5)
        agent_access_button = ttk.Button(agent_access_frame, text="Hunt!", cursor='hand2', bootstyle='primary', command=self.recommendation_agent_toplevel)
        agent_access_button.pack(side=tk.LEFT, padx=10, pady=5)

        # ── Requirement 34: Check Book Availability at a Bookstore ─────────────
        avail_outer = ttk.Labelframe(tab4, text=" Check Book Availability at a Bookstore ", bootstyle='primary')
        avail_outer.pack(fill=tk.X, padx=10, pady=(6, 2))

        # Row 1 – "Specify book" entry (sub-requirement iii)
        book_specify_row = tk.Frame(avail_outer, bg="gray90")
        book_specify_row.pack(fill=tk.X, padx=8, pady=(6, 2))

        tk.Label(
            book_specify_row,
            text="Specify book:",
            bg="gray90",
            font=("Arial", 9, "bold"),
        ).pack(side=tk.LEFT, padx=(0, 4))

        self.avail_book_entry = tk.Entry(book_specify_row, width=36)
        self.avail_book_entry.pack(side=tk.LEFT, padx=(0, 6))

        # Button: auto-fill from selected tree row
        ttk.Button(
            book_specify_row,
            text="Use Selected Book",
            cursor='hand2',
            bootstyle='dark-outline',
            command=self._autofill_availability_book,
        ).pack(side=tk.LEFT, padx=(0, 4))

        # Row 2 – Location + Google Maps (sub-requirements i & ii)
        maps_row = tk.Frame(avail_outer, bg="gray90")
        maps_row.pack(fill=tk.X, padx=8, pady=(2, 6))

        tk.Label(maps_row, text="Location:", bg="gray90").pack(side=tk.LEFT, padx=(0, 4))
        self.location_entry = tk.Entry(maps_row, width=28)
        self.location_entry.pack(side=tk.LEFT, padx=(0, 8))

        # i. Get bookstores from Google Maps
        find_bookstores_button = ttk.Button(
            maps_row,
            text="🗺  Find Nearby Bookstores (Google Maps)",
            cursor='hand2',
            bootstyle='primary',
            command=self.find_nearby_bookstores,
        )
        find_bookstores_button.pack(side=tk.LEFT, padx=(0, 10))

        # ii. Search sites for book
        search_sites_button = ttk.Button(
            maps_row,
            text="🔍  Search Sites for This Book",
            cursor='hand2',
            bootstyle='primary',
            command=self.search_book_availability_sites,
        )
        search_sites_button.pack(side=tk.LEFT)
        # ── End Requirement 34 ───────────────────────────────────────────────

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

        # Right click menu for tree view
        self.tree_menu = tk.Menu(self.root, tearoff=0)
        self.tree_menu.add_command(label="Delete Book", command=self.delete_book)
        self.tree_menu.add_command(label="Edit Book", command=self.edit_book_toplevel)
        self.tree_menu.add_command(label="Add Review", command=self.add_review)

        # the mainloop will run self.on_tree_select() when an item is selected in the TreeView
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        # bind double-left-click to the TreeView to show book's reviews
        self.tree.bind("<Double-1>", self.display_review_window)

        # Bind right click event to the tree to access edit (and eventually delete) book functionality
        self.tree.bind("<Button-3>", self.tree_right_click)

    def create_book(self) :
        """create book helper function using the text entry fields next to the Create button as parameters to the INSERT query"""

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

        status = self.create_status_dropdown.get().strip() if hasattr(self, "create_status_dropdown") else "to read"
        if status == "":
            status = "to read"

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
            self.create_status_dropdown.set("to read")

        self.refresh_genre_dropdown()
        self.refresh_tag_dropdown()
        self.load_books(self.db.get_all_books(self.sorting_dropdown.get()))

    def delete_book(self) :
        """delete book helper function"""
        self.db.delete_book(self.sel_book_id)
        self.clear_treeview()
        self.load_books(self.db.get_all_books(self.sorting_dropdown.get()))


    # THESE METHODS ARE UNSTABLE AND IM SCARED
    def create_review(self, star_value):
        """user creates a new review"""
        new_title = self.db.current_username
        print(star_value)
        new_review = self.review_entry.get() # our Entry widget

        selected = self.tree.selection()[0]
        if not selected:
            return
    
        self.sel_book_id = int(self.tree.item(selected, "values")[0])
        self.db.create_review(self.sel_book_id, new_title, new_review)

    def update_review(self):
        """user updates a review"""
        new_title = "TODO"
        new_review = self.review_entry.get()

        # for now it just will take the first book selected, im not sure how selecting
        # a lot of books will affect the UI yet
        selected = self.tree.selection()[0]

        # there may be a case where all books are unselected? im not sure and i dont
        # really care
        if not selected:
            return

        self.sel_book_id = self.tree.item(selected, "values")[0]
        print(self.sel_book_id)
        self.db.update_review(self.sel_book_id, new_title, new_review)
        

    def delete_review(self):
        review_id = self.review_entry.get() # our Entry widget
        self.db.delete_review(review_id)

    def add_review(self):
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

        #create the entry fields
        title_field = tk.Entry(entry_frame)
        author_field = tk.Entry(entry_frame)
        genre_field = tk.Entry(entry_frame)
        year_field = tk.Entry(entry_frame)

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
        submit_button = tk.Button(button_frame, text="Apply Edit", command=lambda: self.apply_review_edit(text_field_references, edit_window)) #Apply edit, destroy window afterward
        button_frame.pack(side=tk.BOTTOM, fill=tk.X)
        cancel_button.pack(side=tk.LEFT, padx=10, pady=10)
        submit_button.pack(side=tk.RIGHT, padx=10, pady=10)

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
        edit_window.geometry("500x350")
        edit_window.attributes('-topmost', True)
        edit_window.focus_force()
        edit_window.grab_set()

        #create the frame where the entry fields will be
        entry_frame = tk.Frame(edit_window)
        entry_frame.pack(fill=tk.BOTH, expand=True)

        entry_outer = ttk.Labelframe(entry_frame, text=" Enter New Attributes for Book ", bootstyle='primary')
        entry_outer.pack(fill=tk.X, padx=10, pady=(6, 2))
        #create a label giving user interaction instructions
        #tk.Label(entry_frame, text="Enter New Attributes for Book", font=("Arial", 20, "bold")).pack(side=tk.TOP)

        #create the entry fields
        title_field = tk.Entry(entry_outer)
        author_field = tk.Entry(entry_outer)
        genre_field = tk.Entry(entry_outer)
        year_field = tk.Entry(entry_outer)
        status_field = ttk.Combobox(entry_outer, values=["To Read", "Currently Reading", "Completed"])

        #give the entry fields labels and actually pack them
        tk.Label(entry_outer, text="Enter Book Title:").pack(anchor="w")
        title_field.pack(anchor="w", fill=tk.X, ipadx=100)
        title_field.insert(0, old_attributes["title"])
        tk.Label(entry_outer, text="Enter Author Name:").pack(anchor="w")
        author_field.pack(anchor="w", fill=tk.X, ipadx=100)
        author_field.insert(0, old_attributes["author"])
        tk.Label(entry_outer, text="Enter Book Genre:").pack(anchor="w")
        genre_field.pack(anchor="w", fill=tk.X, ipadx=100)
        if (old_attributes["genre"] is not None):
            genre_field.insert(0, old_attributes["genre"])
        else:
            genre_field.insert(0, "")
        tk.Label(entry_outer, text="Enter Year Published:").pack(anchor="w")
        year_field.pack(anchor="w", fill=tk.X, ipadx=100)
        if (old_attributes["year"] is not None) :
            year_field.insert(0, old_attributes["year"])
        else :
            year_field.insert(0, "")
        tk.Label(entry_outer, text="Enter Reading Status:").pack(anchor="w")
        status_field.pack(anchor="w")
        status_field.set(old_attributes["status"])

        #warning frame to handle error messaging
        warning_frame = tk.Frame(edit_window)
        warning_frame.pack(fill=tk.X)

        # create a list to hold the references to the text boxes to be passed to apply_edit function
        text_field_references = [title_field, author_field, genre_field, year_field, status_field]

        #create the frame where the buttons show up, create the buttons, and then finally pack the frame and buttons
        button_frame = tk.Frame(edit_window, bg="gray90")
        cancel_button = ttk.Button(button_frame, text="Cancel Edit", cursor='hand2', bootstyle='warning', command=edit_window.destroy) #If not applying edit, simply destroy the window, no change
        submit_button = ttk.Button(button_frame, text="Apply Edit", cursor='hand2', bootstyle='primary', command=lambda: self.apply_edit(text_field_references, edit_window, warning_frame)) #Apply edit, destroy window afterward
        button_frame.pack(side=tk.BOTTOM, fill=tk.X)
        cancel_button.pack(side=tk.LEFT, padx=10, pady=10)
        submit_button.pack(side=tk.RIGHT, padx=10, pady=10)

    def display_review_window(self, event):
        """create pop-up window to view book's review entries"""
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return

        # setup data from treeview for use in code below
        # this will have to be updated if any fields are added/updated/removed
        book_data = self.tree.item(item_id, "values")
        book_id, title, author, genre, date_published, rating, is_completed = book_data
        print(book_data)

        #create the pop-up window, force focus onto it, and prevent user from interacting with main window while pop-up is up
        review_window = ttk.Toplevel(self.root)
        review_window.title(f"{title} Reviews")
        review_window.geometry("500x800")
        review_window.attributes('-topmost', True)
        review_window.focus_set()
        review_window.grab_set()

        ### Title ###
        title_frame = ttk.Frame(review_window, bootstyle='primary', height=120)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        right_header = ttk.Frame(title_frame, bootstyle='primary')
        right_header.pack(side=tk.RIGHT, padx=16)
        ttk.Label(
            right_header,
            text=f"👤  {self.db.current_username}",
            font=("Arial", 11),
            bootstyle='inverse-primary'
        ).pack(anchor="e")

        label_text = f"{title}, {author}"
        emoji = ""

        ttk.Label(
            title_frame,
            text=f"{emoji}  {label_text}  {emoji}",
            font=("Arial", 24, "bold"),
            bootstyle="inverse-primary",
        ).pack(expand=True)

        reviews_frame = tk.Frame(review_window, bg="gray90")
        reviews_frame.pack(fill=tk.X, pady=5)

        # scroll wheel :p
        # Container
        container = ttk.Frame(review_window)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Canvas (this is what actually scrolls)
        canvas = tk.Canvas(container, highlightthickness=0)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        canvas.configure(yscrollcommand=scrollbar.set)

        # Frame inside the canvas (this holds your reviews)
        scrollable_frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        def on_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        scrollable_frame.bind("<Configure>", on_configure)
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        # returns a dictionary of each review with key as primary key and values
        reviews = self.db.reviews(book_id)

        print(reviews)
        # for every review, we will pack a new label
        for review in reviews:
            review_title = f"review no. {review['review_id']}"
            review_author = review['author']
            review_content = review['review']
            date_created = review['date_created']
            last_updated = review['last_updated']

            review_frame = ttk.Labelframe(scrollable_frame, text=review_title, bootstyle='primary')
            review_frame.pack()

            ttk.Label(
                review_frame,
                text=f"By {review_author} | Created: {date_created} | Updated: {last_updated}",
                font=("Arial", 10),
                bootstyle="secondary"
            ).pack(anchor="w", padx=10, pady=(0, 5))

            ttk.Label(
                review_frame,
                text=review_content,
                font=("Arial", 16),
                wraplength=800,
                justify="left"
            ).pack(anchor="w", padx=10, pady=5)


    def apply_edit(self, text_fields, window, frame) :
        """get the new attributes from the given entry field references, apply the edit"""

        #clear frame, just in case
        for widget in frame.winfo_children():
            widget.destroy()
        #create list to hold the text to be used for constructing query
        new_attributes = []

        #loop through text references to get the input text
        for field in text_fields :
            new_attributes.append(field.get())

        #validate that the user has at least entered a title and author
        if new_attributes[0] == "" or new_attributes[1] == "":
            tk.Label(frame, text="Must have a title and an author!").pack()
            return

        # validate that the user has a valid book status
        if not (new_attributes[4].lower() == "to read" or new_attributes[4].lower() == "currently reading" or new_attributes[4].lower() == "completed"):
            tk.Label(frame, text="Must have a valid status!").pack()
            return

        if not (new_attributes[3].isdigit()) and not (new_attributes[3] == "") :
            tk.Label(frame, text="Year must be a number or left empty").pack()
            return

        if new_attributes[2] == "" :
            new_attributes[2] = None
        if new_attributes[3] == "" :
            new_attributes[3] = None


        #call database function to edit the entry with these new attributes
        self.db.update_book(new_attributes, self.sel_book_id, False)

        #after applying the update, destroy the window
        window.destroy()

        #update the list display to reflect new edited book
        self.clear_treeview()
        self.load_books(self.db.get_all_books(self.sorting_dropdown.get()))

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
        # Prevent duplicating rows when reloading
        self.clear_treeview()
        # Update info label
        num_books = self.db.get_book_count()
        self.info_label.config(text=f"Your Book Collection ({num_books} books)")

        # Insert books into table
        for idx, book in enumerate(books):
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

    # ── Requirement 34 methods ───────────────────────────────────────────────

    def _get_availability_book_title(self) -> str:
        """Return the book title from the availability entry field.

        If the field is empty, fall back to the currently selected tree row.
        Returns an empty string when nothing is available.
        """
        title = self.avail_book_entry.get().strip()
        if title:
            return title
        # fallback: try selected tree row
        selection = self.tree.selection()
        if selection:
            values = self.tree.item(selection[0], "values")
            # values tuple: (ID, Title, Author, Genre, Year, Rating, Status)
            if len(values) >= 2:
                return values[1]
        return ""

    def _autofill_availability_book(self):
        """Populate the 'Specify book' entry from the currently selected tree row."""
        selection = self.tree.selection()
        if not selection:
            self.info_label.config(text="Select a book in the list first.")
            return
        values = self.tree.item(selection[0], "values")
        if len(values) >= 2:
            self.avail_book_entry.delete(0, tk.END)
            self.avail_book_entry.insert(0, values[1])  # title is index 1
            self.info_label.config(text=f"Book set to: {values[1]}")

    def find_nearby_bookstores(self):
        """Sub-requirement i – Get bookstores from Google Maps.

        Opens Google Maps in the browser, searching for bookstores near the
        user-supplied location.  The 'Specify book' title is appended to the
        map query so the user can see both pieces of information at once.
        """
        location = self.location_entry.get().strip()
        book_title = self._get_availability_book_title()

        if not location:
            self.info_label.config(
                text="Please enter a location to find nearby bookstores."
            )
            return

        # Build a Maps query that surfaces bookstores near the given location.
        # Including the book title gives the user a useful search context.
        if book_title:
            maps_query = f'bookstores near {location}'
        else:
            maps_query = f"bookstores near {location}"

        url = f"https://www.google.com/maps/search/{quote(maps_query)}"
        webbrowser.open(url)

        status_msg = f"Opened Google Maps: bookstores near '{location}'"
        if book_title:
            status_msg += f" — looking for '{book_title}'"
        self.info_label.config(text=status_msg)

    def search_book_availability_sites(self):
        """Sub-requirement ii – Search sites for the specified book.

        Opens three retailer / availability sites in the default browser so
        the user can check stock: Google Books, WorldCat (library finder),
        and AbeBooks (new & used inventory).
        """
        book_title = self._get_availability_book_title()

        if not book_title:
            self.info_label.config(
                text="Please enter or select a book title before searching sites."
            )
            return

        encoded = quote(book_title)

        sites = [
            (
                "Google Books",
                f"https://www.google.com/search?q={encoded}+book+buy",
            ),
            (
                "WorldCat (libraries)",
                f"https://www.worldcat.org/search?q={encoded}",
            ),
            (
                "AbeBooks",
                f"https://www.abebooks.com/servlet/SearchResults?kn={encoded}",
            ),
        ]

        for _name, url in sites:
            webbrowser.open(url)

        site_names = ", ".join(name for name, _ in sites)
        self.info_label.config(
            text=f"Opened availability search for '{book_title}' on: {site_names}"
        )

    # ── End Requirement 34 methods ───────────────────────────────────────────

    def toggle_agent(self, btn):
        # Toggles between the button being unclickable or not based on checkbox
        if (self.check_var.get()):
            btn['state'] = 'normal'
        else:
            btn['state'] = 'disabled'
            
    def recommendation_agent_toplevel(self) :
        """Open the window for interacting with the recommendation agent, interactions done by helpers called in this function"""

        #create the pop-up window, force focus onto it, and prevent user from interacting with main window while pop-up is up
        agent_window = tk.Toplevel(self.root)
        agent_window.title("Book Recommendation Agent")
        agent_window.geometry("600x640")
        agent_window.attributes('-topmost', True)
        agent_window.focus_force()
        agent_window.grab_set()

        #Select type of recommendation
        based_outer = ttk.Labelframe(agent_window, text=" Initial Screening ", bootstyle='primary')
        based_outer.pack(fill=tk.X, padx=10, pady=(6, 2))
        tk.Label(based_outer, text="What would you like your recommendation based off of?").pack(side="top")
        type_frame = tk.Frame(based_outer)
        type_frame.pack(fill=tk.X)
        type_selection = tk.IntVar(value=5)
        typeButtons = [("Book(s)", 0), ("Genre(s)", 1), ("Tag(s)", 2)]
        for i, (text, val) in enumerate(typeButtons):
            ttk.Radiobutton(type_frame, text=text, variable=type_selection, value=val, bootstyle='primary').grid(row=i, column=0, sticky="W")

        #Frame for the button to enter initial selection of recommendation type
        button_frame = tk.Frame(based_outer)
        button_frame.pack(fill=tk.X)

        #Frame for opting in to AI agent interaction
        opt_in_frame = tk.Frame(based_outer)
        opt_in_frame.pack(fill=tk.X, pady=5)

        #After selecting type of recommendation, further specification between "all" or "specific entry" appears in this frame
        #this will be done in the specify_recommendation function
        label_frame = tk.Frame(agent_window)
        label_frame.pack(fill=tk.X)
        dynamic_frame = tk.Frame(agent_window)
        dynamic_frame.pack(fill=tk.X, pady=5)

        #Button for moving to second stage of recommendation specification
        get_recommendation_button = ttk.Button(button_frame, text="Next", cursor='hand2', bootstyle='primary-outline', command = lambda : self.specify_recommendation(type_selection, dynamic_frame, label_frame))
        get_recommendation_button['state'] = 'disabled'
        get_recommendation_button.pack()
        self.check_var = tk.BooleanVar()
        self.check_var.set(0)
        opt_in_button = ttk.Checkbutton(opt_in_frame, text="Opt-in to sharing your stored book data with an AI Agent?", bootstyle='primary', variable=self.check_var, command=lambda: self.toggle_agent(get_recommendation_button))
        opt_in_button.pack()

        #This is where the recommendation agent text will appear
        self.agent_frame = tk.Frame(agent_window, height=120, bg="SlateBlue3")
        self.agent_frame.pack(ipady=120, fill=tk.X, side="bottom")
        tk.Label(self.agent_frame, text="Recommendation Agent:", bg="SlateBlue3").pack(side="top")
        self.agent_text = tk.Text(self.agent_frame, height=110, width=500)
        self.agent_text.pack()
        self.agent_text.tag_configure("center", justify='center')

    def specify_recommendation(self, type_selection, frame, label_frame) :
        """Based on selected option, get info from database, and then pass to agent"""

        #Do nothing if no selection made
        num = type_selection.get()
        if num > 2 or num < 0 :
            return

        #Clear frames so that the user can change recommendation types
        for widget in label_frame.winfo_children():
            widget.destroy()
        for widget in frame.winfo_children():
            widget.destroy()

        #Create a tree inside the dynamic_frame
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        #Get recommendation from specific book(s)
        if num == 0 :
            # create tree and button to select book(s) from database
            tk.Label(label_frame, text="Select Books", font=("Arial", 14, "bold"), bg="gray90", width=500).pack()
            columns = ("ID #", "Title", "Author", "Rating")
            tree = ttk.Treeview(frame, columns=columns, show="headings", yscrollcommand=scrollbar.set)
            tree.column("ID #", width=20)
            tree.column("Title", width=300)
            tree.column("Author", width=150)
            tree.column("Rating", width=80)
            # Configure headings
            for col in columns:
                tree.heading(col, text=col)
            tree.pack(fill=tk.BOTH, expand=True)

            # Alternate the row colors
            self.tree.tag_configure('oddrow', background='white')
            self.tree.tag_configure('evenrow', background='gray95')
            scrollbar.config(command=self.tree.yview)

            books = self.db.get_all_books()

            # Insert books into table
            for idx, book in enumerate(books):

                tag = 'evenrow' if idx % 2 == 0 else 'oddrow'

                rating_str = f"{book['rating']}/5" if book['rating'] else "N/A"

                values = (book['id'], book['title'], book['author'], rating_str)

                tree.insert("", tk.END, values=values, tags=(tag,))

            query_button = tk.Button(frame, text="Get Recommendation from Selection", command=lambda : self.model_query_books(tree))
            query_button.pack()
            return

        # Get recommendation from specific genre(s)
        if num == 1 :
            # create tree and button to select genre(s) from database
            tk.Label(label_frame, text="Select Genres", font=("Arial", 14, "bold"), bg="gray90", width=500).pack()
            columns = ("Genre","# of Books w/ Genre", "Avg. Rating")
            tree = ttk.Treeview(frame, columns=columns, show="headings", yscrollcommand=scrollbar.set)
            tree.column("Genre", width=350)
            tree.column("# of Books w/ Genre", width=125)
            tree.column("Avg. Rating", width=75)
            # Configure headings
            for col in columns:
                tree.heading(col, text=col)
            tree.pack(fill=tk.BOTH, expand=True)

            # Alternate the row colors
            self.tree.tag_configure('oddrow', background='white')
            self.tree.tag_configure('evenrow', background='gray95')
            scrollbar.config(command=self.tree.yview)

            genres = self.db.get_genres_with_stats()
            # Insert genres and stats into table
            for idx, genre in enumerate(genres):
                if genre['genre'] is None :
                    continue

                tag = 'evenrow' if idx % 2 == 0 else 'oddrow'

                values = (genre['genre'], genre['count'], genre['avg'],)

                tree.insert("", tk.END, values=values, tags=(tag,))

            query_button = ttk.Button(frame, text="Get Recommendation from Selection", cursor='hand2', bootstyle='primary', command=lambda : self.model_query_genres(tree))
            query_button.pack(pady=5)
            return

        # Get recommendation from specific tag(s)
        if num == 2 :
            # create tree and button to select tag(s) from database
            tk.Label(label_frame, text="Select Tags", font=("Arial", 14, "bold"), bg="gray90", width=500).pack(fill=tk.X)
            columns = ("Tag","# of Books w/ Tag", "Avg. Rating")
            tree = ttk.Treeview(frame, columns=columns, show="headings", yscrollcommand=scrollbar.set)
            tree.column("Tag", width=350)
            tree.column("# of Books w/ Tag", width=125)
            tree.column("Avg. Rating", width=75)
            # Configure headings
            for col in columns:
                tree.heading(col, text=col)
            tree.pack(fill=tk.BOTH, expand=True)

            # Alternate the row colors
            self.tree.tag_configure('oddrow', background='white')
            self.tree.tag_configure('evenrow', background='gray95')
            scrollbar.config(command=self.tree.yview)

            tags = self.db.get_tags_with_stats()
            # Insert books into table
            for idx, tag_i in enumerate(tags):
                if tag_i['tag'] is None:
                    continue

                tag = 'evenrow' if idx % 2 == 0 else 'oddrow'

                values = (tag_i['tag'], tag_i['count'], tag_i['avg'],)

                tree.insert("", tk.END, values=values, tags=(tag,))

            query_button = tk.Button(frame, text="Get Recommendation from Selection", command=lambda : self.model_query_tags(tree))
            query_button.pack()
            return

    def model_query_books(self, tree) :
        self.agent_text.delete("1.0", "end")
        selected_books = tree.selection()
        titles = []
        authors = []
        ratings = []
        for selection in selected_books :
            titles.append(tree.item(selection, "values")[1])
            authors.append(tree.item(selection, "values")[2])
            ratings.append(tree.item(selection, "values")[3])


        if not(len(titles) < 1) :
            load_dotenv()
            client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=os.getenv('API_KEY'))

            completion = client.chat.completions.create(
                model="openai/gpt-oss-120b:free",  # Check OpenRouter for current free model IDs
                messages=[{"role": "user", "content": f'give me 3 book recommendation if I have read this/these book(s): {titles} by {authors} and rated them {ratings} respectively on a scale of 0-5. Only list the title, author, and a short single-sentence description. do not put it in a list format'}]
            )
            self.agent_text.insert("1.0", completion.choices[0].message.content, "center")
            client.close()

    def model_query_genres(self, tree) :
        self.agent_text.delete("1.0", "end")
        selected_genres = tree.selection()
        genres = []
        counts = []
        averages = []
        for selection in selected_genres:
            genres.append(tree.item(selection, "values")[0])
            counts.append(tree.item(selection, "values")[1])
            averages.append(tree.item(selection, "values")[2])

        if not(len(genres) < 1) :
            load_dotenv()
            client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=os.getenv('API_KEY'))

            completion = client.chat.completions.create(
                model="openai/gpt-oss-120b:free",  # Check OpenRouter for current free model IDs
                messages=[{"role": "user", "content": f'give me 3 book recommendation if I have read books in this/these genres(s): {genres}, {counts} times respectively and, on average, rated them {averages} respectively on a scale of 0-5. Only list the title, author, and a short single-sentence description. do not put it in a list format'}]
            )
            self.agent_text.insert("1.0", completion.choices[0].message.content, "center")
            client.close()

    def model_query_tags(self,tree) :
        self.agent_text.delete("1.0", "end")
        selected_tags = tree.selection()
        tags = []
        counts = []
        averages = []
        for selection in selected_tags:
            tags.append(tree.item(selection, "values")[0])
            counts.append(tree.item(selection, "values")[1])
            averages.append(tree.item(selection, "values")[2])

        if not(len(tags) < 1) :
            load_dotenv()
            client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=os.getenv('API_KEY'))

            completion = client.chat.completions.create(
                model="openai/gpt-oss-120b:free",  # Check OpenRouter for current free model IDs
                messages=[{"role": "user", "content": f'give me 3 book recommendation if I have read books with this/these content tag(s): {tags}, {counts} times respectively and, on average, rated them {averages} respectively on a scale of 0-5. Only list the title, author, and a short single-sentence description. do not put it in a list format'}]
            )
            self.agent_text.insert("1.0", completion.choices[0].message.content, "center")
            client.close()

    def _logout(self):
        """Log out and return to the sign-in screen."""
        self.db.logout_user()
        for widget in self.root.winfo_children():
            widget.destroy()
        self.root.geometry("420x480")
        # Pass a closure so the callback captures root/db without globals
        _show_signin(self.root, self.db)

def _show_signin(root: tk.Tk, db: DatabaseBackend):
    """Display the sign-in screen and wire it to launch the main app."""
    def on_success(username: str):
        root.geometry("900x900")
        BookHuntGUI(root, db)

    SignInScreen(root, db, on_success)


def main():
    root = tk.Tk()
    style = ttk.Style(theme='pulse')
    db   = DatabaseBackend()
    _show_signin(root, db)
    root.mainloop()

if __name__ == "__main__":
    main()
