# -------------------------------------------------------------
# 📚 College PYQ & Notes Portal
# -------------------------------------------------------------
# This Tkinter-based desktop application allows:
#   • Admins to upload and manage study materials (Notes, PYQs, etc.)
#   • Students to search, view, and download materials
#   • Students to submit suggestions or feedback to the admin
#
# Features:
#   - SQLite database for storage
#   - Admin login authentication
#   - File upload & download functionality
#   - Course, semester, and subject filtering
#   - Suggestion Box for user feedback
# -------------------------------------------------------------

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sqlite3
import os
import datetime
import shutil
import uuid
import subprocess
import sys

# ------------------ GLOBAL CONSTANTS ------------------
DB_NAME = "college_materials.db"     # SQLite database file name
UPLOAD_FOLDER = "uploads"            # Folder to store uploaded files

# Create uploads folder if not present
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# ------------------ DATABASE INITIALIZATION ------------------
def init_db():
    """Initialize the SQLite database with required tables."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Table for storing course names
    c.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_name TEXT UNIQUE
        )
    """)

    # Table for storing uploaded materials
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

    # Table for storing admin login credentials
    c.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            username TEXT PRIMARY KEY,
            password TEXT
        )
    """)

    # Table for storing user suggestions
    c.execute("""
        CREATE TABLE IF NOT EXISTS suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            message TEXT,
            submitted_on TEXT
        )
    """)

    # Insert default admin credentials and some courses
    c.execute("INSERT OR IGNORE INTO admins VALUES ('nishant', '45009Ni')")
    c.execute("INSERT OR IGNORE INTO courses (course_name) VALUES ('BSc Physical Science with Computer Science')")
    c.execute("INSERT OR IGNORE INTO courses (course_name) VALUES ('BSc honours Chemistry')")
    c.execute("INSERT OR IGNORE INTO courses (course_name) VALUES ('BCom')")
    c.execute("INSERT OR IGNORE INTO courses (course_name) VALUES ('BA')")

    conn.commit()
    conn.close()


# ------------------ MAIN APPLICATION CLASS ------------------
class CollegeApp(tk.Tk):
    """Main window of the College Materials Portal."""

    def __init__(self):
        super().__init__()
        self.title("📚 College PYQ & Notes Portal")
        self.geometry("1000x700")
        self.configure(bg="#f8f9fa")

        # Variables
        self.selected_file_path = None
        self.admin_logged_in = False

        # Create a tabbed interface (Notebook)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, pady=10)

        # Initialize two tabs: Login and Student view
        self.create_login_tab()
        self.create_student_tab()

    # ---------------------------------------------------------
    # 🧑‍💻 ADMIN LOGIN TAB
    # ---------------------------------------------------------
    def create_login_tab(self):
        """Create the Admin Login tab."""
        self.login_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.login_tab, text="🧑‍💻 Admin Login")

        frame = ttk.LabelFrame(self.login_tab, text="Admin Login", padding=20)
        frame.pack(pady=50)

        ttk.Label(frame, text="Username:").grid(row=0, column=0, padx=10, pady=5)
        self.admin_user_entry = ttk.Entry(frame, width=25)
        self.admin_user_entry.grid(row=0, column=1, pady=5)

        ttk.Label(frame, text="Password:").grid(row=1, column=0, padx=10, pady=5)
        self.admin_pass_entry = ttk.Entry(frame, width=25, show="*")
        self.admin_pass_entry.grid(row=1, column=1, pady=5)

        ttk.Button(frame, text="Login", command=self.verify_admin).grid(row=2, column=0, columnspan=2, pady=15)

    def verify_admin(self):
        """Check admin credentials and open dashboard if valid."""
        user = self.admin_user_entry.get().strip()
        pwd = self.admin_pass_entry.get().strip()

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT * FROM admins WHERE username=? AND password=?", (user, pwd))
        result = c.fetchone()
        conn.close()

        if result:
            messagebox.showinfo("Login Successful ✅", f"Welcome, {user}!")
            self.admin_logged_in = True
            self.create_admin_dashboard()
            self.notebook.hide(self.login_tab)
        else:
            messagebox.showerror("Invalid Credentials", "Incorrect username or password.")

    def logout_admin(self):
        """Log out the admin and return to login tab."""
        self.remove_admin_dashboard()
        self.admin_logged_in = False
        self.notebook.add(self.login_tab, text="🧑‍💻 Admin Login")
        self.notebook.select(self.login_tab)
        self.admin_user_entry.delete(0, tk.END)
        self.admin_pass_entry.delete(0, tk.END)

    # ---------------------------------------------------------
    # 🧰 ADMIN DASHBOARD (MAIN MANAGEMENT AREA)
    # ---------------------------------------------------------
    def create_admin_dashboard(self):
        """Create the Admin Dashboard tab after successful login."""
        if hasattr(self, 'admin_dashboard'):
            self.notebook.forget(self.admin_dashboard)

        self.admin_dashboard = ttk.Frame(self.notebook)
        self.notebook.add(self.admin_dashboard, text="🧑‍💻 Admin Dashboard")
        self.notebook.select(self.admin_dashboard)

        # Logout button
        ttk.Button(self.admin_dashboard, text="Logout", command=self.logout_admin).pack(anchor="ne", pady=5, padx=10)

        # -------------------- Upload Section --------------------
        upload_frame = ttk.LabelFrame(self.admin_dashboard, text="Upload Material", padding=15)
        upload_frame.pack(padx=10, pady=10, fill="x")

        # Upload input fields
        ttk.Label(upload_frame, text="Course:").grid(row=0, column=0, padx=5, pady=5)
        self.upload_course_combo = ttk.Combobox(upload_frame, values=self.get_courses(), width=30)
        self.upload_course_combo.grid(row=0, column=1, padx=5)

        ttk.Label(upload_frame, text="Semester:").grid(row=0, column=2, padx=5)
        self.upload_sem_combo = ttk.Combobox(upload_frame, values=["1st","2nd","3rd","4th","5th","6th"], width=10)
        self.upload_sem_combo.grid(row=0, column=3, padx=5)

        ttk.Label(upload_frame, text="Year:").grid(row=1, column=0, padx=5)
        self.upload_year_combo = ttk.Combobox(upload_frame, values=["2022","2023","2024","2025","2026"], width=15)
        self.upload_year_combo.grid(row=1, column=1, padx=5)

        ttk.Label(upload_frame, text="Subject:").grid(row=1, column=2, padx=5)
        self.upload_sub_entry = ttk.Entry(upload_frame, width=25)
        self.upload_sub_entry.grid(row=1, column=3, padx=5)

        ttk.Label(upload_frame, text="Type:").grid(row=2, column=0, padx=5)
        self.upload_type_combo = ttk.Combobox(upload_frame, values=["Notes","PYQ","Other"], width=15)
        self.upload_type_combo.grid(row=2, column=1, padx=5)

        # Buttons for file selection & upload
        btn_frame = ttk.Frame(upload_frame)
        btn_frame.grid(row=3, column=0, columnspan=4, pady=15)
        ttk.Button(btn_frame, text="📂 Select File", command=self.select_file).grid(row=0, column=0, padx=10)
        ttk.Button(btn_frame, text="⬆️ Upload File", command=self.upload_material).grid(row=0, column=1, padx=10)

        # Label to show selected file name
        self.file_label = ttk.Label(upload_frame, text="No file selected", foreground="gray")
        self.file_label.grid(row=4, column=0, columnspan=4)

        # -------------------- Uploaded Files Table --------------------
        materials_frame = ttk.LabelFrame(self.admin_dashboard, text="Uploaded Materials", padding=15)
        materials_frame.pack(padx=10, pady=10, fill="both", expand=True)

        columns = ("ID","Course","Subject","Type","Semester","Year","Uploaded On","File Path")
        self.admin_result_table = ttk.Treeview(materials_frame, columns=columns, show="headings")
        for col in columns:
            self.admin_result_table.heading(col, text=col)
            self.admin_result_table.column(col, width=120)
        self.admin_result_table.pack(fill="both", expand=True, pady=10)

        ttk.Button(materials_frame, text="🗑️ Delete Selected", command=self.admin_delete_selected).pack(pady=5)
        self.load_admin_materials()

        # -------------------- Suggestions Viewer --------------------
        suggestion_frame = ttk.LabelFrame(self.admin_dashboard, text="📩 Student Suggestions", padding=10)
        suggestion_frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("ID", "Name", "Message", "Submitted On")
        self.suggestion_table = ttk.Treeview(suggestion_frame, columns=columns, show="headings")
        for col in columns:
            self.suggestion_table.heading(col, text=col)
            self.suggestion_table.column(col, width=200)
        self.suggestion_table.pack(fill="both", expand=True, pady=5)

        self.load_suggestions()

    def remove_admin_dashboard(self):
        """Remove admin dashboard when logging out."""
        if hasattr(self, 'admin_dashboard'):
            self.notebook.forget(self.admin_dashboard)
            del self.admin_dashboard

    # -------------------- File Handling --------------------
    def select_file(self):
        """Open file dialog to select a file for upload."""
        path = filedialog.askopenfilename(title="Select File")
        if path:
            self.selected_file_path = path
            self.file_label.config(text=f"Selected: {os.path.basename(path)}", foreground="green")

    def upload_material(self):
        """Upload the selected material and save details to database."""
        if not self.selected_file_path:
            messagebox.showerror("Error", "Select a file first.")
            return

        course = self.upload_course_combo.get().strip()
        sem = self.upload_sem_combo.get().strip()
        year = self.upload_year_combo.get().strip()
        subject = self.upload_sub_entry.get().strip()
        mtype = self.upload_type_combo.get().strip()

        if not all([course, sem, year, subject, mtype]):
            messagebox.showerror("Error", "Fill all fields before uploading.")
            return

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

        ext = os.path.splitext(self.selected_file_path)[1]
        dest = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}{ext}")
        shutil.copy2(self.selected_file_path, dest)

        uploaded_on = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("""
            INSERT INTO materials (course_id, semester, year, subject, type, file_path, uploaded_on)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (cid, sem, year, subject, mtype, dest, uploaded_on))
        conn.commit()
        conn.close()

        messagebox.showinfo("✅ Success", "Material uploaded successfully.")
        self.selected_file_path = None
        self.file_label.config(text="No file selected", foreground="gray")
        self.load_admin_materials()

    def admin_delete_selected(self):
        """Delete a selected material from the table and database."""
        sel = self.admin_result_table.selection()
        if not sel:
            messagebox.showerror("Error", "Select a row to delete.")
            return
        mid = self.admin_result_table.item(sel[0])["values"][0]
        file_path = self.admin_result_table.item(sel[0])["values"][7]

        if os.path.exists(file_path):
            os.remove(file_path)

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("DELETE FROM materials WHERE id=?", (mid,))
        conn.commit()
        conn.close()

        self.admin_result_table.delete(sel[0])
        messagebox.showinfo("Deleted", "Material removed successfully.")

    def load_admin_materials(self):
        """Load uploaded materials into the admin table."""
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("""
            SELECT m.id, c.course_name, m.subject, m.type, m.semester, m.year, m.uploaded_on, m.file_path
            FROM materials m JOIN courses c ON m.course_id=c.id ORDER BY m.uploaded_on DESC
        """)
        rows = c.fetchall()
        conn.close()

        for i in self.admin_result_table.get_children():
            self.admin_result_table.delete(i)
        for r in rows:
            self.admin_result_table.insert("", tk.END, values=r)

    def load_suggestions(self):
        """Load all student suggestions into admin table."""
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT * FROM suggestions ORDER BY submitted_on DESC")
        rows = c.fetchall()
        conn.close()

        for i in self.suggestion_table.get_children():
            self.suggestion_table.delete(i)
        for r in rows:
            self.suggestion_table.insert("", tk.END, values=r)

    def get_courses(self):
        """Return list of available courses."""
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT course_name FROM courses")
        courses = [r[0] for r in c.fetchall()]
        conn.close()
        return courses

    # ---------------------------------------------------------
    # 🎓 STUDENT TAB
    # ---------------------------------------------------------
    def create_student_tab(self):
        """Create the Student/Visitor tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🎓 Student / Visitor")

        ttk.Label(tab, text="📖 Search Materials", font=("Arial", 14, "bold")).pack(pady=10)

        # ---------------- Search Filters ----------------
        filters = ttk.Frame(tab)
        filters.pack(pady=5)

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

        ttk.Label(filters, text="Subject:").grid(row=1, column=0, padx=5, pady=5)
        self.subject_search_combo = ttk.Combobox(filters, width=30, state="readonly")
        self.subject_search_combo.grid(row=1, column=1, columnspan=3, padx=5)

        ttk.Button(filters, text="🔍 Search", command=self.search_materials).grid(row=1, column=4, padx=5)

        self.search_course_combo.bind("<<ComboboxSelected>>", self.update_student_subjects)
        self.search_sem_combo.bind("<<ComboboxSelected>>", self.update_student_subjects)
        self.search_year_combo.bind("<<ComboboxSelected>>", self.update_student_subjects)

        # ---------------- Results Table ----------------
        table_frame = ttk.Frame(tab)
        table_frame.pack(fill="both", expand=True, pady=10)

        columns = ("Subject","Type","Semester","Year","Uploaded On","👁️ View","⬇️ Download")
        self.result_table = ttk.Treeview(table_frame, columns=columns, show="headings")
        for col in columns:
            self.result_table.heading(col, text=col)
            self.result_table.column(col, width=120)
        self.result_table.pack(fill="both", expand=True)
        self.result_table.bind("<Button-1>", self.on_student_table_click)

        # ---------------- Suggestion Box ----------------
        suggestion_frame = ttk.LabelFrame(tab, text="💬 Suggestion Box", padding=10)
        suggestion_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(suggestion_frame, text="Your Name:").grid(row=0, column=0, padx=5, pady=5)
        self.sugg_name = ttk.Entry(suggestion_frame, width=40)
        self.sugg_name.grid(row=0, column=1, padx=5)

        ttk.Label(suggestion_frame, text="Your Suggestion:").grid(row=1, column=0, padx=5, pady=5)
        self.sugg_text = tk.Text(suggestion_frame, width=50, height=4)
        self.sugg_text.grid(row=1, column=1, padx=5)

        ttk.Button(suggestion_frame, text="📨 Submit", command=self.submit_suggestion).grid(row=2, column=0, columnspan=2, pady=10)

    # ---------------- Suggestion Submission ----------------
    def submit_suggestion(self):
        """Insert student's suggestion into the database."""
        name = self.sugg_name.get().strip() or "Anonymous"
        message = self.sugg_text.get("1.0", tk.END).strip()

        if not message:
            messagebox.showerror("Error", "Please enter a suggestion.")
            return

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO suggestions (name, message, submitted_on) VALUES (?, ?, ?)",
                  (name, message, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()

        messagebox.showinfo("Thank You 🙏", "Your suggestion has been submitted!")
        self.sugg_name.delete(0, tk.END)
        self.sugg_text.delete("1.0", tk.END)

    # ---------------- Search and View ----------------
    def update_student_subjects(self, event=None):
        """Update subject dropdown based on filters."""
        course = self.search_course_combo.get()
        sem = self.search_sem_combo.get()
        year = self.search_year_combo.get()

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("""
            SELECT DISTINCT subject FROM materials m 
            JOIN courses c2 ON m.course_id=c2.id
            WHERE c2.course_name=? AND m.semester=? AND m.year=?
        """, (course, sem, year))
        subjects = [r[0] for r in c.fetchall()]
        conn.close()

        self.subject_search_combo["values"] = subjects
        if subjects:
            self.subject_search_combo.current(0)

    def search_materials(self):
        """Search materials based on filters."""
        course = self.search_course_combo.get().strip()
        sem = self.search_sem_combo.get().strip()
        year = self.search_year_combo.get().strip()
        subject = self.subject_search_combo.get().strip()
        mtype = self.filter_type_combo.get().strip()

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        query = """
            SELECT m.subject, m.type, m.semester, m.year, m.uploaded_on, m.file_path
            FROM materials m JOIN courses c2 ON m.course_id=c2.id
            WHERE c2.course_name=? AND m.semester=? AND m.year=?
        """
        params = [course, sem, year]
        if subject:
            query += " AND m.subject=?"
            params.append(subject)
        if mtype != "All":
            query += " AND m.type=?"
            params.append(mtype)

        c.execute(query, tuple(params))
        rows = c.fetchall()
        conn.close()

        for i in self.result_table.get_children():
            self.result_table.delete(i)
        for r in rows:
            self.result_table.insert("", tk.END, values=(r[0], r[1], r[2], r[3], r[4], "👁️ View", "⬇️ Download"))

    def on_student_table_click(self, event):
        """Handle view or download click events."""
        item = self.result_table.identify_row(event.y)
        column = self.result_table.identify_column(event.x)
        if not item:
            return

        values = self.result_table.item(item, "values")
        subject, file_path = values[0], None

        course = self.search_course_combo.get().strip()
        sem = self.search_sem_combo.get().strip()
        year = self.search_year_combo.get().strip()

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("""
            SELECT file_path FROM materials m 
            JOIN courses c2 ON m.course_id=c2.id
            WHERE c2.course_name=? AND m.semester=? AND m.year=? AND m.subject=?
        """, (course, sem, year, subject))
        res = c.fetchone()
        conn.close()

        if res:
            file_path = res[0]

        if not file_path or not os.path.exists(file_path):
            messagebox.showerror("Error", "File not found.")
            return

        if column == "#6":  # 👁️ View
            try:
                if sys.platform == "win32":
                    os.startfile(file_path)
                elif sys.platform == "darwin":
                    subprocess.call(["open", file_path])
                else:
                    subprocess.call(["xdg-open", file_path])
            except Exception:
                messagebox.showerror("Error", "Cannot open file.")
        elif column == "#7":  # ⬇️ Download
            dest = filedialog.asksaveasfilename(defaultextension=os.path.splitext(file_path)[1],
                                                initialfile=os.path.basename(file_path))
            if dest:
                shutil.copy2(file_path, dest)
                messagebox.showinfo("✅ Downloaded", f"File saved to:\n{dest}")


# -------------------------------------------------------------
# 🏁 MAIN EXECUTION
# -------------------------------------------------------------
if __name__ == "__main__":
    init_db()
    app = CollegeApp()
    app.mainloop()