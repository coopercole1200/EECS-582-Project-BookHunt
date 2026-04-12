"""
Artifact: GUI.py
Description: Main entry point. Starts application.
Authors: Cole Cooper
Date Created: 2/14/2026
Date Last Modified: 4/12/2026
Last Modified by: Updated for sign-in screen (Task 2.2)
"""

import tkinter as tk
from tkinter import ttk
from database import DatabaseBackend
import webbrowser
from urllib.parse import quote

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
            text="📚  BookHunt",
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


# ═════════════════════════════════════════════════════════════════════════════
# Main application (unchanged except for logout button + welcome label)
# ═════════════════════════════════════════════════════════════════════════════

class BookHuntGUI:
    def __init__(self, root: tk.Tk, db: DatabaseBackend):
        self.root = root
        self.db   = db

        self.root.title("BookHunt")
        self.root.geometry("900x900")

        # Initialise tag state
        self._tag_id_map   = {}
        self._pending_tags = []

        # Build UI then load data
        self.setup_ui()
        self.refresh_genre_dropdown()
        self.refresh_tag_dropdown()
        self.load_books(self.db.get_all_books("id"))

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def setup_ui(self):
        # ── Header ────────────────────────────────────────────────────
        title_frame = tk.Frame(self.root, bg=ACCENT, height=80)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)

        tk.Label(
            title_frame,
            text="BookHunt",
            font=("Arial", 24, "bold"),
            bg=ACCENT, fg="white",
        ).pack(side=tk.LEFT, padx=20, expand=True)

        # Welcome label + logout button (right side of header)
        right_header = tk.Frame(title_frame, bg=ACCENT)
        right_header.pack(side=tk.RIGHT, padx=16)

        tk.Label(
            right_header,
            text=f"👤  {self.db.current_username}",
            font=("Arial", 11),
            bg=ACCENT, fg="white",
        ).pack(anchor="e")

        tk.Button(
            right_header,
            text="Log Out",
            font=("Arial", 9),
            bg="white", fg=ACCENT_DARK,
            relief="flat", cursor="hand2",
            command=self._logout,
        ).pack(anchor="e", pady=(2, 0))

        # ── Review frame ──────────────────────────────────────────────
        self.review_frame = tk.Frame(self.root, bg=ACCENT, height=80)
        self.review_frame.pack(fill=tk.X)
        self.review_content = tk.Label(
            self.review_frame,
            text="no reviews",
            font=("Arial", 16),
            bg="SlateBlue2",
            fg="white",
        )
        self.review_content.pack()

        selectedStarValue = tk.IntVar(value=0)
        self.review_entry = tk.Entry(self.review_frame)
        self.review_stars = tk.Frame(self.review_frame)
        update_review_button = tk.Button(
            self.review_frame, text="Add/Update Review",
            command=lambda: self.update_review(selectedStarValue),
        )
        delete_review_button = tk.Button(
            self.review_frame, text="Delete Review",
            command=self.delete_review,
        )

        update_review_button.pack(side=tk.LEFT, padx=(0, 20))
        self.review_entry.pack(side=tk.LEFT)
        self.review_stars.pack(side=tk.LEFT, padx=(5, 0))
        for text, val in [("0", 0), ("1", 1), ("2", 2), ("3", 3), ("4", 4), ("5", 5)]:
            tk.Radiobutton(
                self.review_stars, text=text,
                variable=selectedStarValue, value=val,
            ).grid(row=0, column=val, padx=5)
        delete_review_button.pack(side=tk.LEFT, padx=(20, 0))

        # ── Right-click menu ──────────────────────────────────────────
        self.tree_menu = tk.Menu(self.root, tearoff=0)
        self.tree_menu.add_command(label="Delete Book",  command=self.delete_book)
        self.tree_menu.add_command(label="Edit Book",    command=self.edit_book_toplevel)

        # ── Create book row ───────────────────────────────────────────
        creation_frame = tk.Frame(self.root, bg=BG)
        creation_frame.pack(fill=tk.X, ipady=20)

        tk.Button(creation_frame, text="Create a Book Entry",
                  command=self.create_book).pack(side=tk.LEFT, padx=10, pady=10)

        for label, attr, width in [
            ("Title:",  "title_entry",  18),
            ("Author:", "author_entry", 18),
            ("Genre:",  "genre_entry",  14),
            ("Year:",   "year_entry",    6),
            ("Rating:", "rating_entry",  6),
        ]:
            tk.Label(creation_frame, text=label, bg=BG).pack(side=tk.LEFT, padx=(10, 2))
            entry = tk.Entry(creation_frame, width=width)
            entry.pack(side=tk.LEFT, padx=(0, 10))
            setattr(self, attr, entry)

        tk.Label(creation_frame, text="Status:", bg=BG).pack(side=tk.LEFT, padx=(0, 2))
        self.create_status_dropdown = ttk.Combobox(
            creation_frame,
            values=["to-read", "completed", "currently reading"],
            width=16, state="readonly",
        )
        self.create_status_dropdown.set("to-read")
        self.create_status_dropdown.pack(side=tk.LEFT, padx=(0, 10))

        # ── Tag entry row ─────────────────────────────────────────────
        tag_frame = tk.Frame(self.root, bg=BG)
        tag_frame.pack(fill=tk.X, ipady=4)
        tk.Label(tag_frame, text="Tags:", bg=BG).pack(side=tk.LEFT, padx=(10, 2))
        self.pending_tag_entry = tk.Entry(tag_frame, width=18)
        self.pending_tag_entry.pack(side=tk.LEFT, padx=(0, 4))
        self.pending_tag_entry.bind("<Return>", lambda e: self._add_pending_tag())
        tk.Button(tag_frame, text="Add Tag",
                  command=self._add_pending_tag).pack(side=tk.LEFT, padx=(0, 10))
        self.pending_tags_label = tk.Label(
            tag_frame, text="No tags added yet.", bg=BG, fg="gray50")
        self.pending_tags_label.pack(side=tk.LEFT)

        # ── Filters ───────────────────────────────────────────────────
        filter_frame = tk.Frame(self.root, bg=BG)
        filter_frame.pack(fill=tk.X, ipady=4)

        tk.Label(filter_frame, text="Status:", bg=BG).pack(
            side=tk.LEFT, padx=(10, 2), pady=8)
        self.status_dropdown = ttk.Combobox(
            filter_frame,
            values=["All", "Completed", "To Read", "Currently Reading"],
            width=16, state="readonly",
        )
        self.status_dropdown.set("All")
        self.status_dropdown.pack(side=tk.LEFT, padx=(0, 16), pady=8)

        tk.Label(filter_frame, text="Genre:", bg=BG).pack(
            side=tk.LEFT, padx=(0, 2), pady=8)
        self.genre_dropdown = ttk.Combobox(
            filter_frame, values=["All Genres"], width=18, state="readonly")
        self.genre_dropdown.set("All Genres")
        self.genre_dropdown.pack(side=tk.LEFT, padx=(0, 16), pady=8)

        tk.Label(filter_frame, text="Tag:", bg=BG).pack(
            side=tk.LEFT, padx=(0, 2), pady=8)
        self.tag_dropdown = ttk.Combobox(
            filter_frame, values=["All Tags"], width=18, state="readonly")
        self.tag_dropdown.set("All Tags")
        self.tag_dropdown.pack(side=tk.LEFT, padx=(0, 16), pady=8)

        tk.Button(filter_frame, text="Apply Filter(s)",
                  command=self.apply_filters).pack(side=tk.LEFT, padx=(0, 6), pady=8)
        tk.Button(filter_frame, text="Clear Filters",
                  command=self.clear_filters).pack(side=tk.LEFT, pady=8)

        # ── Sorting ───────────────────────────────────────────────────
        sorting_frame = tk.Frame(self.root, bg=BG)
        sorting_frame.pack(fill=tk.X, ipady=4)
        tk.Label(sorting_frame, text="Sort by:", bg=BG).pack(
            side=tk.LEFT, padx=(10, 2), pady=8)
        self.sorting_dropdown = ttk.Combobox(
            sorting_frame,
            values=["id", "title", "author", "genre", "year", "status"],
            width=18, state="readonly",
        )
        self.sorting_dropdown.set("id")
        self.sorting_dropdown.pack(side=tk.LEFT, padx=(0, 16), pady=8)
        tk.Button(sorting_frame, text="Apply Sorting",
                  command=self.apply_sorting).pack(side=tk.LEFT, padx=(0, 6), pady=8)

        # ── Search ────────────────────────────────────────────────────
        searching_frame = tk.Frame(self.root, bg=BG)
        searching_frame.pack(fill=tk.X, ipady=4)
        self.search_field = tk.Entry(searching_frame)
        self.search_field.pack(anchor="w", fill=tk.X, ipadx=100)
        tk.Button(searching_frame, text="Search for Title",
                  command=self.search_book).pack(side=tk.LEFT, padx=(0, 6), pady=8)

        # ── Nearby bookstores ─────────────────────────────────────────
        maps_frame = tk.Frame(self.root, bg=BG)
        maps_frame.pack(fill=tk.X, ipady=10)
        tk.Label(maps_frame, text="Location:", bg=BG).pack(side=tk.LEFT, padx=(10, 2))
        self.location_entry = tk.Entry(maps_frame, width=30)
        self.location_entry.pack(side=tk.LEFT, padx=(0, 10))
        tk.Button(maps_frame, text="Find Nearby Bookstores",
                  command=self.find_nearby_bookstores).pack(
            side=tk.LEFT, padx=10, pady=5)

        # ── Book collection treeview ──────────────────────────────────
        content_frame = tk.Frame(self.root, bg=BG)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        self.info_label = tk.Label(
            content_frame,
            text="Your Book Collection",
            font=("Arial", 14, "bold"),
            bg=BG,
        )
        self.info_label.pack(pady=(0, 10))

        tree_frame = tk.Frame(content_frame, bg=BG)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        columns = ("ID #", "Title", "Author", "Genre", "Year", "Rating", "Status")
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            yscrollcommand=scrollbar.set,
        )
        scrollbar.config(command=self.tree.yview)

        widths = {"ID #": 25, "Title": 200, "Author": 150,
                  "Genre": 120, "Year": 80, "Rating": 80, "Status": 120}
        for col in columns:
            self.tree.column(col, width=widths[col])
            self.tree.heading(col, text=col)

        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.tag_configure("oddrow",  background="white")
        self.tree.tag_configure("evenrow", background="gray95")

        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree.bind("<Button-3>",         self.tree_right_click)

    # ------------------------------------------------------------------
    # Logout
    # ------------------------------------------------------------------

    def _logout(self):
        """Log out and return to the sign-in screen."""
        self.db.logout_user()
        for widget in self.root.winfo_children():
            widget.destroy()
        self.root.geometry("420x480")
        # Pass a closure so the callback captures root/db without globals
        _show_signin(self.root, self.db)

    # ------------------------------------------------------------------
    # Book operations (unchanged from original)
    # ------------------------------------------------------------------

    def create_book(self):
        if not hasattr(self, "title_entry") or not hasattr(self, "author_entry"):
            self.db.create_book()
            self.load_books(self.db.get_all_books())
            return

        title  = self.title_entry.get().strip()
        author = self.author_entry.get().strip()
        genre  = self.genre_entry.get().strip() if hasattr(self, "genre_entry") else ""

        if not title or not author:
            self.info_label.config(text="Title and Author are required.")
            return

        year_raw = self.year_entry.get().strip() if hasattr(self, "year_entry") else ""
        year = None
        if year_raw:
            try:
                year = int(year_raw)
            except ValueError:
                self.info_label.config(text="Year must be an integer (e.g., 2024).")
                return

        rating_raw = self.rating_entry.get().strip() if hasattr(self, "rating_entry") else ""
        rating = None
        if rating_raw:
            try:
                rating = float(rating_raw)
            except ValueError:
                self.info_label.config(text="Rating must be a number (e.g., 4 or 4.5).")
                return

        status = self.create_status_dropdown.get().strip() if hasattr(self, "create_status_dropdown") else "to-read"
        if not status:
            status = "to-read"

        self.db.create_book(title, author, genre, year, rating, status)

        if self._pending_tags:
            new_book_id = self.db.get_all_books("id")[-1]["id"]
            for tag_label in self._pending_tags:
                self.db.add_tag_to_book(new_book_id, tag_label)
            self._pending_tags = []
            self.pending_tags_label.config(text="No tags added yet.", fg="gray50")

        for attr in ("title_entry", "author_entry", "genre_entry",
                     "year_entry", "rating_entry"):
            if hasattr(self, attr):
                getattr(self, attr).delete(0, tk.END)
        if hasattr(self, "create_status_dropdown"):
            self.create_status_dropdown.set("to-read")

        self.refresh_genre_dropdown()
        self.refresh_tag_dropdown()
        self.load_books(self.db.get_all_books(self.sorting_dropdown.get()))

    def delete_book(self):
        self.db.delete_book(self.sel_book_id)
        self.clear_treeview()
        self.load_books(self.db.get_all_books(self.sorting_dropdown.get()))

    def update_review(self, rating):
        new = self.review_entry.get()
        updatedRating = str(rating.get())
        selection = self.tree.selection()  # Fix 2: check before indexing
        if not selection:
            return
        selected = selection[0]
        self.sel_book_id = self.tree.item(selected, "values")[0]
        self.db.update_review(self.sel_book_id, new)
        self.db.update_book([updatedRating], self.sel_book_id, True)
        book_review = self.db.get_specific_book(self.sel_book_id)[6]
        self.review_content.config(
            text=book_review if book_review else "No review yet.")

    def delete_review(self):
        selection = self.tree.selection()  # Fix 2: check before indexing
        if not selection:
            return
        selected = selection[0]
        self.sel_book_id = self.tree.item(selected, "values")[0]
        self.db.delete_review(self.sel_book_id)
        book_review = self.db.get_specific_book(self.sel_book_id)[6]
        self.review_content.config(
            text=book_review if book_review else "No review yet.")

    def edit_book_toplevel(self):
        old_book_info = self.db.get_specific_book(self.sel_book_id)
        self.display_edit_window(old_book_info)

    def display_edit_window(self, old_attributes):
        edit_window = tk.Toplevel(self.root)
        edit_window.title("Edit Book Entity")
        edit_window.geometry("500x450")
        edit_window.attributes("-topmost", True)
        edit_window.focus_force()
        edit_window.grab_set()

        entry_frame = tk.Frame(edit_window)
        entry_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(entry_frame, text="Enter New Attributes for Book",
                 font=("Arial", 20, "bold")).pack(side=tk.TOP)

        title_field  = tk.Entry(entry_frame)
        author_field = tk.Entry(entry_frame)
        genre_field  = tk.Entry(entry_frame)
        year_field   = tk.Entry(entry_frame)
        status_field = ttk.Combobox(
            entry_frame,
            values=["To Read", "Currently Reading", "Completed"],
        )

        for label, widget in [
            ("Enter Book Title:",     title_field),
            ("Enter Author Name:",    author_field),
            ("Enter Book Genre:",     genre_field),
            ("Enter Year Published:", year_field),
            ("Enter Reading Status:", status_field),
        ]:
            tk.Label(entry_frame, text=label).pack(anchor="w")
            widget.pack(anchor="w", fill=tk.X, ipadx=100)

        text_field_references = [
            title_field, author_field, genre_field, year_field, status_field]

        button_frame = tk.Frame(edit_window, bg=BG)
        tk.Button(button_frame, text="Cancel Edit",
                  command=edit_window.destroy).pack(side=tk.LEFT, padx=10, pady=10)
        tk.Button(button_frame, text="Apply Edit",
                  command=lambda: self.apply_edit(
                      text_field_references, edit_window)).pack(
            side=tk.RIGHT, padx=10, pady=10)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X)

    def apply_edit(self, text_fields, window):
        new_attributes = [f.get() for f in text_fields]
        self.db.update_book(new_attributes, self.sel_book_id, False)
        window.destroy()
        self.clear_treeview()
        self.load_books(self.db.get_all_books(self.sorting_dropdown.get()))

    def on_tree_select(self, event):
        selection = self.tree.selection()  # Fix 2: check before indexing
        if not selection:
            return
        selected = selection[0]
        self.sel_book_id = self.tree.item(selected, "values")[0]
        book_review = self.db.get_specific_book(self.sel_book_id)[6]
        self.review_content.config(
            text=book_review if book_review else "No review yet.")

    def tree_right_click(self, event):
        tree_item_id = self.tree.identify_row(event.y)
        if not tree_item_id:
            return
        self.tree.selection_set(tree_item_id)
        self.sel_book_id = self.tree.item(tree_item_id, "values")[0]
        self.tree_menu.post(event.x_root, event.y_root)
        self.tree_menu.grab_release()

    def apply_filters(self):
        status = self.status_dropdown.get()
        genre  = self.genre_dropdown.get()
        tag    = self.tag_dropdown.get()
        tag_ids = []
        if tag and tag != "All Tags":
            all_tags = self.db.get_all_tags()
            tag_ids  = [t["id"] for t in all_tags if t["label"] == tag]
        self.load_books(
            self.db.get_filtered_books(status=status, genre=genre, tag_ids=tag_ids))

    def clear_filters(self):
        self.status_dropdown.set("All")
        self.genre_dropdown.set("All Genres")
        self.tag_dropdown.set("All Tags")
        self.load_books(self.db.get_all_books(self.sorting_dropdown.get()))

    def apply_sorting(self):
        self.load_books(self.db.get_all_books(self.sorting_dropdown.get()))

    def search_book(self):
        self.load_books(
            self.db.get_books_by_name(
                self.search_field.get(), self.sorting_dropdown.get()))

    def refresh_genre_dropdown(self):
        genres = ["All Genres"] + self.db.get_distinct_genres()
        self.genre_dropdown["values"] = genres
        if self.genre_dropdown.get() not in genres:
            self.genre_dropdown.set("All Genres")

    def refresh_tag_dropdown(self):
        tags = ["All Tags"] + [t["label"] for t in self.db.get_all_tags()]
        self.tag_dropdown["values"] = tags
        if self.tag_dropdown.get() not in tags:
            self.tag_dropdown.set("All Tags")

    def _add_pending_tag(self):
        label = self.pending_tag_entry.get().strip()
        if not label or label in self._pending_tags:
            self.pending_tag_entry.delete(0, tk.END)
            return
        self._pending_tags.append(label)
        self.pending_tag_entry.delete(0, tk.END)
        self.pending_tags_label.config(
            text="Tags: " + ", ".join(self._pending_tags), fg="black")

    def load_books(self, books):
        self.clear_treeview()
        num_books = self.db.get_book_count()
        self.info_label.config(
            text=f"{self.db.current_username}'s Book Collection ({num_books} books)")
        self.book_mapping = {}
        for idx, book in enumerate(books):
            self.book_mapping[idx] = book
            tag       = "evenrow" if idx % 2 == 0 else "oddrow"
            rating_str = f"{book['rating']}/5" if book["rating"] else "N/A"
            status     = book["status"].replace("-", " ").title()
            self.tree.insert(
                "", tk.END,
                values=(book["id"], book["title"], book["author"],
                        book["genre"] or "N/A", book["year"] or "N/A",
                        rating_str, status),
                tags=(tag,),
            )

    def clear_treeview(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def find_nearby_bookstores(self):
        location = self.location_entry.get().strip()
        if not location:
            self.info_label.config(
                text="Please enter a location to find nearby bookstores.")
            return
        query = quote(f"bookstores near {location}")
        webbrowser.open(f"https://www.google.com/maps/search/{query}")
        self.info_label.config(
            text=f"Opening nearby bookstores for: {location}")


# ─────────────────────────────────────────────────────────────────────────────
# Wiring – closure-based so no module-level globals are needed
# ─────────────────────────────────────────────────────────────────────────────

def _show_signin(root: tk.Tk, db: DatabaseBackend):
    """Display the sign-in screen and wire it to launch the main app."""
    def on_success(username: str):
        root.geometry("900x900")
        BookHuntGUI(root, db)

    SignInScreen(root, db, on_success)


def main():
    root = tk.Tk()
    db   = DatabaseBackend()
    _show_signin(root, db)
    root.mainloop()


if __name__ == "__main__":
    main()
