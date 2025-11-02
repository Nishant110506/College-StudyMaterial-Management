# ------------------------------------------------------------
# 📚 COLLEGE PYQ & NOTES PORTAL
# ------------------------------------------------------------
# This program is a Tkinter-based GUI application for managing
# college study materials such as Notes, PYQs, and Other files.
# Admins can upload or delete materials, and students can
# search, view, and download them easily.
# ------------------------------------------------------------

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sqlite3
import os
import datetime
import shutil
import uuid
import subprocess
import sys

# ------------------ DATABASE & FOLDER SETUP ------------------

DB_NAME = "college_materials.db"   # SQLite database name
UPLOAD_FOLDER = "uploads"          # Folder to store uploaded files

# Create the upload folder if it doesn’t exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# ------------------ DATABASE INITIALIZATION ------------------
def init_db():
    """Initializes database tables and inserts default data if not present."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Create table for courses
    c.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_name TEXT UNIQUE
        )
    """)

    # Create table for study materials
    c.execute("""
        CREATE TABLE IF NOT EXISTS materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER,
            semester TEXT,
            year TEXT,
            subject TEXT,
            type TEXT,
            file_path TEXT,
            uploaded_on TEXT,
            FOREIGN KEY(course_id) REFERENCES courses(id)
        )
    """)

    # Create table for admin credentials
    c.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            username TEXT PRIMARY KEY,
            password TEXT
        )
    """)

    # Default admin account
    c.execute("INSERT OR IGNORE INTO admins VALUES ('nishant', '45009Ni')")

    # Default courses
    c.execute("INSERT OR IGNORE INTO courses (course_name) VALUES ('BSc Physical Science with Computer Science')")
    c.execute("INSERT OR IGNORE INTO courses (course_name) VALUES ('BSc honours Chemistry')")
    c.execute("INSERT OR IGNORE INTO courses (course_name) VALUES ('BCom')")
    c.execute("INSERT OR IGNORE INTO courses (course_name) VALUES ('BA')")

    conn.commit()
    conn.close()


# ------------------ MAIN APPLICATION CLASS ------------------
class CollegeApp(tk.Tk):
    """Main window class for the College Materials Portal."""
    def __init__(self):
        super().__init__()
        self.title("📚 College PYQ & Notes Portal")
        self.geometry("1000x650")
        self.configure(bg="#88bdb4")

        self.selected_file_path = None     # Store selected file path temporarily
        self.admin_logged_in = False       # Track admin login state

        # Create Notebook (tab system)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, pady=10)

        # Initialize both tabs
        self.create_login_tab()
        self.create_student_tab()


    # ==========================================================++
    #                    ADMIN LOGIN TAB                        ++
    # ==========================================================++
    def create_login_tab(self):
        """Creates the login tab for admin authentication."""
        self.login_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.login_tab, text="🧑‍💻 Admin Login")

        # Frame for login widgets
        frame = ttk.LabelFrame(self.login_tab, text="Admin Login", padding=20)
        frame.pack(pady=30)

        # Username field
        ttk.Label(frame, text="Username:").grid(row=0, column=0, padx=10, pady=5)
        self.admin_user_entry = ttk.Entry(frame, width=25)
        self.admin_user_entry.grid(row=0, column=1, pady=5)

        # Password field
        ttk.Label(frame, text="Password:").grid(row=1, column=0, padx=10, pady=5)
        self.admin_pass_entry = ttk.Entry(frame, width=25, show="*")
        self.admin_pass_entry.grid(row=1, column=1, pady=5)

        # Login button
        ttk.Button(frame, text="Login", command=self.verify_admin).grid(row=2, column=0, columnspan=2, pady=15)


    def verify_admin(self):
        """Checks admin credentials from the database."""
        user = self.admin_user_entry.get().strip()
        pwd = self.admin_pass_entry.get().strip()

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT * FROM admins WHERE username=? AND password=?", (user, pwd))
        result = c.fetchone()
        conn.close()

        # If credentials match
        if result:
            messagebox.showinfo("Login Successful ✅", f"Welcome, {user}!")
            self.admin_logged_in = True
            self.create_admin_dashboard()   # Open dashboard
            self.notebook.hide(self.login_tab)  # Hide login tab
        else:
            messagebox.showerror("Invalid Credentials", "Incorrect username or password.")


    def logout_admin(self):
        """Logs out admin and returns to login screen."""
        self.remove_admin_dashboard()
        self.admin_logged_in = False
        self.notebook.add(self.login_tab, text="🧑‍💻 Admin Login")
        self.notebook.select(self.login_tab)
        self.admin_user_entry.delete(0, tk.END)
        self.admin_pass_entry.delete(0, tk.END)


    # ==========================================================
    #                    ADMIN DASHBOARD TAB
    # ==========================================================
    def create_admin_dashboard(self):
        """Creates the admin dashboard after successful login."""

        # If dashboard already exists, remove it (prevents duplication)
        if hasattr(self, 'admin_dashboard'):
            self.notebook.forget(self.admin_dashboard)

        # Create new dashboard tab
        self.admin_dashboard = ttk.Frame(self.notebook)
        self.notebook.add(self.admin_dashboard, text="🧑‍💻 Admin Dashboard")
        self.notebook.select(self.admin_dashboard)

        # Logout button (top-right)
        ttk.Button(self.admin_dashboard, text="Logout", command=self.logout_admin).pack(anchor="ne", pady=5, padx=10)

        # ---------- Upload Material Section ----------
        upload_frame = ttk.LabelFrame(self.admin_dashboard, text="Upload Material", padding=15)
        upload_frame.pack(padx=10, pady=10, fill="x")

        # Course dropdown
        ttk.Label(upload_frame, text="Course:").grid(row=0, column=0, padx=5, pady=5)
        self.upload_course_combo = ttk.Combobox(upload_frame, values=self.get_courses(), width=30)
        self.upload_course_combo.grid(row=0, column=1, padx=5)

        # Semester dropdown
        ttk.Label(upload_frame, text="Semester:").grid(row=0, column=2, padx=5)
        self.upload_sem_combo = ttk.Combobox(upload_frame, values=["1st","2nd","3rd","4th","5th","6th"], width=10)
        self.upload_sem_combo.grid(row=0, column=3, padx=5)

        # Year dropdown
        ttk.Label(upload_frame, text="Year:").grid(row=1, column=0, padx=5)
        self.upload_year_combo = ttk.Combobox(upload_frame, values=["2022","2023","2024","2025","2026"], width=15)
        self.upload_year_combo.grid(row=1, column=1, padx=5)

        # Subject entry
        ttk.Label(upload_frame, text="Subject:").grid(row=1, column=2, padx=5)
        self.upload_sub_entry = ttk.Entry(upload_frame, width=25)
        self.upload_sub_entry.grid(row=1, column=3, padx=5)

        # Type dropdown (Notes / PYQ / Other)
        ttk.Label(upload_frame, text="Type:").grid(row=2, column=0, padx=5)
        self.upload_type_combo = ttk.Combobox(upload_frame, values=["Notes","PYQ","Other"], width=15)
        self.upload_type_combo.grid(row=2, column=1, padx=5)

        # Buttons for file selection & upload
        btn_frame = ttk.Frame(upload_frame)
        btn_frame.grid(row=3, column=0, columnspan=4, pady=15)

        ttk.Button(btn_frame, text="📂 Select File", command=self.select_file).grid(row=0, column=0, padx=10)
        ttk.Button(btn_frame, text="⬆️ Upload File", command=self.upload_material).grid(row=0, column=1, padx=10)

        # Display selected file name
        self.file_label = ttk.Label(upload_frame, text="No file selected", foreground="gray")
        self.file_label.grid(row=4, column=0, columnspan=4)

        # ---------- Table Section for Uploaded Materials ----------
        materials_frame = ttk.LabelFrame(self.admin_dashboard, text="Uploaded Materials", padding=15)
        materials_frame.pack(padx=10, pady=10, fill="both", expand=True)

        columns = ("ID","Course","Subject","Type","Semester","Year","Uploaded On","File Path")
        self.admin_result_table = ttk.Treeview(materials_frame, columns=columns, show="headings")

        for col in columns:
            self.admin_result_table.heading(col, text=col)
            self.admin_result_table.column(col, width=120)

        self.admin_result_table.pack(fill="both", expand=True, pady=10)

        # Delete button for removing selected material
        ttk.Button(materials_frame, text="🗑️ Delete Selected", command=self.admin_delete_selected).pack(pady=5)

        # Load existing data into table
        self.load_admin_materials()


    def remove_admin_dashboard(self):
        """Removes the admin dashboard tab when logging out."""
        if hasattr(self, 'admin_dashboard'):
            self.notebook.forget(self.admin_dashboard)
            del self.admin_dashboard


    def select_file(self):
        """Opens file dialog to select a file for upload."""
        path = filedialog.askopenfilename(title="Select File")
        if path:
            self.selected_file_path = path
            self.file_label.config(text=f"Selected: {os.path.basename(path)}", foreground="green")


    def upload_material(self):
        """Uploads selected material to database and local storage."""
        if not self.selected_file_path:
            messagebox.showerror("Error", "Select a file first.")
            return

        # Get form inputs
        course = self.upload_course_combo.get().strip()
        sem = self.upload_sem_combo.get().strip()
        year = self.upload_year_combo.get().strip()
        subject = self.upload_sub_entry.get().strip()
        mtype = self.upload_type_combo.get().strip()

        # Check for missing fields
        if not all([course, sem, year, subject, mtype]):
            messagebox.showerror("Error", "Fill all fields.")
            return

        # Fetch or create course ID
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id FROM courses WHERE course_name=?", (course,))
        res = c.fetchone()
        if not res:
            c.execute("INSERT INTO courses (course_name) VALUES (?)", (course,))
            conn.commit()
            c.execute("SELECT id FROM courses WHERE course_name=?", (course,))
            res = c.fetchone()
        cid = res[0]

        # Copy file to uploads folder with unique name
        ext = os.path.splitext(self.selected_file_path)[1]
        dest = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}{ext}")
        shutil.copy2(self.selected_file_path, dest)

        # Insert into materials table
        uploaded_on = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("""
            INSERT INTO materials (course_id, semester, year, subject, type, file_path, uploaded_on)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (cid, sem, year, subject, mtype, dest, uploaded_on))
        conn.commit()
        conn.close()

        # Refresh UI
        messagebox.showinfo("✅ Success", "Material uploaded.")
        self.selected_file_path = None
        self.file_label.config(text="No file selected", foreground="gray")
        self.load_admin_materials()
        self.search_materials()  # Update student view too


    def admin_delete_selected(self):
        """Deletes the selected material from both database and local folder."""
        sel = self.admin_result_table.selection()
        if not sel:
            messagebox.showerror("Error", "Select a row to delete.")
            return
        mid = self.admin_result_table.item(sel[0])["values"][0]
        file_path = self.admin_result_table.item(sel[0])["values"][7]

        # Delete the file
        if os.path.exists(file_path):
            os.remove(file_path)

        # Remove from database
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("DELETE FROM materials WHERE id=?", (mid,))
        conn.commit()
        conn.close()

        # Remove from table
        self.admin_result_table.delete(sel[0])
        messagebox.showinfo("Deleted", "Material removed.")
        self.search_materials()


    def load_admin_materials(self):
        """Loads all uploaded materials into the admin table."""
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("""
            SELECT m.id, c.course_name, m.subject, m.type, m.semester, m.year, m.uploaded_on, m.file_path
            FROM materials m JOIN courses c ON m.course_id=c.id ORDER BY m.uploaded_on DESC
        """)
        rows = c.fetchall()
        conn.close()

        # Clear previous data
        for i in self.admin_result_table.get_children():
            self.admin_result_table.delete(i)

        # Insert new data
        for r in rows:
            self.admin_result_table.insert("", tk.END, values=r)


    def get_courses(self):
        """Fetch all courses from database."""
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT course_name FROM courses")
        courses = [r[0] for r in c.fetchall()]
        conn.close()
        return courses


    # ==========================================================
    #                    STUDENT TAB
    # ==========================================================
    def create_student_tab(self):
        """Creates the student/visitor interface for searching materials."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🎓Students")

        ttk.Label(tab, text="📖 Search Materials", font=("Arial", 14, "bold")).pack(pady=10)

        # --- Filter Frame ---
        filters = ttk.Frame(tab)
        filters.pack(pady=5)

        # Search filters
        ttk.Label(filters, text="Course:").grid(row=0, column=0, padx=5)
        self.search_course_combo = ttk.Combobox(filters, values=self.get_courses(), width=25, state="readonly")
        self.search_course_combo.grid(row=0, column=1)

        ttk.Label(filters, text="Semester:").grid(row=0, column=2, padx=5)
        self.search_sem_combo = ttk.Combobox(filters, values=["1st","2nd","3rd","4th","5th","6th"], width=10, state="readonly")
        self.search_sem_combo.grid(row=0, column=3)

        ttk.Label(filters, text="Year:").grid(row=0, column=4, padx=5)
        self.search_year_combo = ttk.Combobox(filters, values=["2022","2023","2024","2025","2026"], width=15, state="readonly")
        self.search_year_combo.grid(row=0, column=5)

        ttk.Label(filters, text="Type:").grid(row=0, column=6, padx=5)
        self.filter_type_combo = ttk.Combobox(filters, values=["All","Notes","PYQ","Other"], width=10, state="readonly")
        self.filter_type_combo.current(0)
        self.filter_type_combo.grid(row=0, column=7)

        # Subject filter
        ttk.Label(filters, text="Subject:").grid(row=1, column=0, padx=5, pady=5)
        self.subject_search_combo = ttk.Combobox(filters, width=30, state="readonly")
        self.subject_search_combo.grid(row=1, column=1, columnspan=3, padx=5)

        # Search button
        ttk.Button(filters, text="🔍 Search", command=self.search_materials).grid(row=1, column=4, padx=5)

        # Update subject list dynamically when course, sem, or year changes
        self.search_course_combo.bind("<<ComboboxSelected>>", self.update_student_subjects)
        self.search_sem_combo.bind("<<ComboboxSelected>>", self.update_student_subjects)
        self.search_year_combo.bind("<<ComboboxSelected>>", self.update_student_subjects)

        # --- Results Table ---
        table_frame = ttk.Frame(tab)
        table_frame.pack(fill="both", expand=True, pady=10)

        columns = ("Subject","Type","Semester","Year","Uploaded On","👁️ View","⬇️ Download")
        self.result_table = ttk.Treeview(table_frame, columns=columns, show="headings")

        for col in columns:
            self.result_table.heading(col, text=col)
            self.result_table.column(col, width=120)

        self.result_table.pack(fill="both", expand=True)

        # Handle button clicks (View/Download)
        self.result_table.bind("<Button-1>", self.on_student_table_click)

        # Load all materials initially
        self.search_materials()


    # ------------------ STUDENT HANDLERS ------------------

    def on_student_table_click(self, event):
        """Handles clicks on 'View' or 'Download' columns."""
        region = self.result_table.identify("region", event.x, event.y)
        if region != "cell":
            return
        row_id = self.result_table.identify_row(event.y)
        col_id = self.result_table.identify_column(event.x)
        if not row_id:
            return
        col_text = self.result_table.heading(col_id, "text")
        values = self.result_table.item(row_id, "values")
        tags = self.result_table.item(row_id, "tags")
        if not tags:
            return
        file_path = tags[0]
        if col_text == "👁️ View":
            self._view_file(file_path)
        elif col_text == "⬇️ Download":
            self._download_file(file_path)


    def _view_file(self, path):
        """Opens the selected file using the system default viewer."""
        if not os.path.exists(path):
            messagebox.showerror("Error", "File not found.")
            return
        try:
            if sys.platform.startswith('darwin'):
                subprocess.call(('open', path))
            elif os.name == 'nt':
                os.startfile(path)
            elif os.name == 'posix':
                subprocess.call(('xdg-open', path))
        except Exception as e:
            messagebox.showerror("Error", f"Cannot open:\n{e}")


    def _download_file(self, path):
        """Allows students to download a copy of a material."""
        if not os.path.exists(path):
            messagebox.showerror("Error", "File not found.")
            return
        dest = filedialog.asksaveasfilename(initialfile=os.path.basename(path), title="Save File As")
        if dest:
            try:
                shutil.copy2(path, dest)
                messagebox.showinfo("Downloaded", f"File saved to:\n{dest}")
            except Exception as e:
                messagebox.showerror("Error", f"Download failed:\n{e}")


    def search_materials(self):
        """Filters and displays materials based on selected criteria."""
        course = self.search_course_combo.get().strip()
        sem = self.search_sem_combo.get().strip()
        year = self.search_year_combo.get().strip()
        mat_type = self.filter_type_combo.get().strip()
        subject = self.subject_search_combo.get().strip()

        query = """
            SELECT m.subject, m.type, m.semester, m.year, m.uploaded_on, m.file_path
            FROM materials m
            JOIN courses c ON m.course_id=c.id
            WHERE 1=1
        """
        params = []
        if course:
            query += " AND c.course_name=?"
            params.append(course)
        if sem:
            query += " AND m.semester=?"
            params.append(sem)
        if year:
            query += " AND m.year=?"
            params.append(year)
        if mat_type != "All":
            query += " AND m.type=?"
            params.append(mat_type)
        if subject:
            query += " AND m.subject LIKE ?"
            params.append(f"%{subject}%")

        # Execute query
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute(query, params)
        rows = c.fetchall()
        conn.close()

        # Clear table before inserting new rows
        for i in self.result_table.get_children():
            self.result_table.delete(i)

        # Insert new rows
        for subj, mtype, sem, yr, uploaded_on, path in rows:
            self.result_table.insert("", tk.END,
                                     values=(subj, mtype, sem, yr, uploaded_on, "👁️ View", "⬇️ Download"),
                                     tags=(path,))


    def update_student_subjects(self, event=None):
        """Updates subject dropdown based on selected course, semester, and year."""
        course = self.search_course_combo.get().strip()
        sem = self.search_sem_combo.get().strip()
        year = self.search_year_combo.get().strip()
        if not all([course, sem, year]):
            self.subject_search_combo["values"] = []
            return

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("""
            SELECT DISTINCT subject FROM materials m
            JOIN courses c ON m.course_id=c.id
            WHERE c.course_name=? AND m.semester=? AND m.year=?
        """, (course, sem, year))
        subjects = [r[0] for r in c.fetchall()]
        conn.close()
        self.subject_search_combo["values"] = subjects


# ------------------ PROGRAM ENTRY POINT ------------------
if __name__ == "__main__":
    init_db()      # Initialize database before launching UI
    app = CollegeApp()
    app.mainloop()  # Start Tkinter main loop
