# college_portal_streamlit.py
import streamlit as st
import sqlite3
import os
import datetime
import shutil
import uuid
from io import BytesIO

DB_NAME = "college_materials.db"
UPLOAD_FOLDER = "uploads"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_name TEXT UNIQUE
        )
    """)
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
    c.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            username TEXT PRIMARY KEY,
            password TEXT
        )
    """)
    c.execute("INSERT OR IGNORE INTO admins VALUES ('nishant', '45009Ni')")
    # Add some default courses
    default_courses = [
        'BSc Physical Science with Computer Science',
        'BSc honours Chemistry',
        'BCom',
        'BA'
    ]
    for course in default_courses:
        c.execute("INSERT OR IGNORE INTO courses (course_name) VALUES (?)", (course,))
    conn.commit()
    conn.close()

def get_courses():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT course_name FROM courses ORDER BY course_name")
    courses = [r[0] for r in c.fetchall()]
    conn.close()
    return courses

def add_course(course_name):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO courses (course_name) VALUES (?)", (course_name,))
    conn.commit()
    conn.close()

def insert_material(course_name, semester, year, subject, mtype, saved_path):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # ensure course exists
    c.execute("SELECT id FROM courses WHERE course_name=?", (course_name,))
    res = c.fetchone()
    if not res:
        c.execute("INSERT INTO courses (course_name) VALUES (?)", (course_name,))
        conn.commit()
        c.execute("SELECT id FROM courses WHERE course_name=?", (course_name,))
        res = c.fetchone()
    cid = res[0]
    uploaded_on = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("""
        INSERT INTO materials (course_id, semester, year, subject, type, file_path, uploaded_on)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (cid, semester, year, subject, mtype, saved_path, uploaded_on))
    conn.commit()
    conn.close()

def query_materials(course=None, semester=None, year=None, mtype=None, subject_like=None):
    query = """
        SELECT m.id, c.course_name, m.subject, m.type, m.semester, m.year, m.uploaded_on, m.file_path
        FROM materials m JOIN courses c ON m.course_id=c.id
        WHERE 1=1
    """
    params = []
    if course:
        query += " AND c.course_name=?"
        params.append(course)
    if semester:
        query += " AND m.semester=?"
        params.append(semester)
    if year:
        query += " AND m.year=?"
        params.append(year)
    if mtype and mtype != "All":
        query += " AND m.type=?"
        params.append(mtype)
    if subject_like:
        query += " AND m.subject LIKE ?"
        params.append(f"%{subject_like}%")
    query += " ORDER BY m.uploaded_on DESC"
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return rows

def delete_material(mid, file_path):
    # remove file
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        st.warning(f"Could not remove file: {e}")
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM materials WHERE id=?", (mid,))
    conn.commit()
    conn.close()

# ---------- Streamlit UI ----------
st.set_page_config(page_title="College PYQ & Notes Portal", layout="wide")
st.title("📚 College PYQ & Notes Portal (Streamlit)")

init_db()

# handle simple session-state admin login
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
if "admin_user" not in st.session_state:
    st.session_state.admin_user = ""

tabs = st.tabs(["Student / Visitor", "Admin Login" if not st.session_state.admin_logged_in else "Admin Dashboard"])

# ---------- STUDENT TAB ----------
with tabs[0]:
    st.header("📖 Search Materials")
    col1, col2 = st.columns([3,1])
    with col1:
        # Filters
        courses = get_courses()
        course = st.selectbox("Course", options=[""] + courses)
        semester = st.selectbox("Semester", options=["", "1st","2nd","3rd","4th","5th","6th"])
        year = st.selectbox("Year", options=["", "2022","2023","2024","2025","2026"])
        mtype = st.selectbox("Type", options=["All","Notes","PYQ","Other"])
        subject = st.text_input("Subject (partial match)")
        if st.button("🔍 Search"):
            pass  # just triggers rerun

        rows = query_materials(course if course else None,
                               semester if semester else None,
                               year if year else None,
                               mtype,
                               subject if subject else None)

        if not rows:
            st.info("No materials found for the selected filters.")
        else:
            # show as table and provide view & download
            import pandas as pd
            df = pd.DataFrame(rows, columns=["ID","Course","Subject","Type","Semester","Year","Uploaded On","File Path"])
            # shorten path for display
            df_display = df.copy()
            df_display["File Name"] = df_display["File Path"].apply(lambda p: os.path.basename(p) if p else "")
            df_display = df_display[["ID","Course","Subject","Type","Semester","Year","Uploaded On","File Name"]]
            st.dataframe(df_display, use_container_width=True)

            # Action on selected
            sel_id = st.number_input("Enter ID to View / Download", min_value=0, step=1, value=0)
            if sel_id:
                matched = df[df["ID"] == int(sel_id)]
                if matched.empty:
                    st.warning("ID not found in results.")
                else:
                    rec = matched.iloc[0]
                    fp = rec["File Path"]
                    st.write(f"**Selected:** {rec['Subject']} — {rec['Course']} [{rec['Type']}]")
                    if os.path.exists(fp):
                        # try to display preview for images/pdf/text
                        ext = os.path.splitext(fp)[1].lower()
                        if ext in [".png", ".jpg", ".jpeg", ".bmp", ".gif"]:
                            st.image(fp)
                        elif ext in [".pdf"]:
                            with open(fp, "rb") as f:
                                pdf_bytes = f.read()
                            st.download_button("⬇️ Download PDF", data=pdf_bytes, file_name=os.path.basename(fp), mime="application/pdf")
                            st.write("Preview: (PDF preview may not show in all deployments)")
                            try:
                                st.pdf(fp)
                            except Exception:
                                pass
                        else:
                            # generic download
                            with open(fp, "rb") as f:
                                file_bytes = f.read()
                            st.download_button("⬇️ Download File", data=file_bytes, file_name=os.path.basename(fp))
                    else:
                        st.error("File not found on server.")

# ---------- ADMIN LOGIN / DASHBOARD ----------
with tabs[1]:
    if not st.session_state.admin_logged_in:
        st.subheader("🧑‍💻 Admin Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT * FROM admins WHERE username=? AND password=?", (username.strip(), password.strip()))
            res = c.fetchone()
            conn.close()
            if res:
                st.session_state.admin_logged_in = True
                st.session_state.admin_user = username.strip()
                st.success(f"Welcome, {username}!")
                st.rerun()
            else:
                st.error("Invalid credentials.")
        st.markdown("---")
        st.write("If you need to create/modify admin credentials directly, update the database.")
    else:
        st.header("🧑‍💻 Admin Dashboard")
        st.write(f"Logged in as: **{st.session_state.admin_user}**")
        if st.button("Logout"):
            st.session_state.admin_logged_in = False
            st.session_state.admin_user = ""
            st.rerun()

        st.markdown("### Upload Material")
        colA, colB = st.columns([2,1])
        with colA:
            courses = get_courses()
            course_sel = st.selectbox("Course", options=courses)
            add_new_course = st.text_input("Or add new course (leave blank if not)")
            semester_u = st.selectbox("Semester", options=["1st","2nd","3rd","4th","5th","6th"])
            year_u = st.selectbox("Year", options=["2022","2023","2024","2025","2026"])
            subject_u = st.text_input("Subject")
            type_u = st.selectbox("Type", options=["Notes","PYQ","Other"])
            uploaded_file = st.file_uploader("Select file to upload", type=None)
            if add_new_course and st.button("Add Course"):
                add_course(add_new_course.strip())
                st.success("Course added. Select it from the Course dropdown.")
                st.rerun()
        with colB:
            st.info("Uploads are saved on the server in `uploads/`.")
            st.write("Use the admin dashboard to delete materials.")

        if st.button("⬆️ Upload File"):
            if add_new_course:
                course_to_use = add_new_course.strip()
            else:
                course_to_use = course_sel
            if not uploaded_file:
                st.error("Please select a file to upload.")
            elif not all([course_to_use, semester_u, year_u, subject_u, type_u]):
                st.error("Fill all metadata fields.")
            else:
                # save file
                ext = os.path.splitext(uploaded_file.name)[1]
                saved_name = f"{uuid.uuid4()}{ext}"
                saved_path = os.path.join(UPLOAD_FOLDER, saved_name)
                with open(saved_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                insert_material(course_to_use, semester_u, year_u, subject_u, type_u, saved_path)
                st.success("Material uploaded.")
                st.rerun()

        st.markdown("---")
        st.markdown("### Uploaded Materials (Admin View)")
        rows = query_materials()
        import pandas as pd
        if not rows:
            st.info("No uploaded materials.")
        else:
            df_admin = pd.DataFrame(rows, columns=["ID","Course","Subject","Type","Semester","Year","Uploaded On","File Path"])
            df_admin["File Name"] = df_admin["File Path"].apply(lambda p: os.path.basename(p) if p else "")
            st.dataframe(df_admin[["ID","Course","Subject","Type","Semester","Year","Uploaded On","File Name"]], use_container_width=True)

            st.write("**Delete a material**")
            del_id = st.number_input("Enter ID to delete", min_value=0, step=1, value=0, key="del_id_input")
            if st.button("🗑️ Delete Selected"):
                if del_id:
                    matched = df_admin[df_admin["ID"] == int(del_id)]
                    if matched.empty:
                        st.warning("ID not found.")
                    else:
                        fp = matched.iloc[0]["File Path"]
                        delete_material(int(del_id), fp)
                        st.success("Material deleted.")
                        st.rerun()
                else:
                    st.warning("Provide a valid ID to delete.")

# ---------- Footer / Notes ----------
st.sidebar.title("About")
st.sidebar.info("This Streamlit version stores uploads in the `uploads/` folder and uses an SQLite DB (`college_materials.db`).\n\nRun locally with `streamlit run college_portal_streamlit.py`.")
