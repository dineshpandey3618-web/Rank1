import streamlit as st
import sqlite3
import feedparser
import time

# --- 1. DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('rank1_dynamic.db')
    c = conn.cursor()
    
    # Core Tables
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT, role TEXT, 
                  board TEXT, state TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS subjects
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, class TEXT, icon TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS chapters
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, subject_id INTEGER, name TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS materials
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, chapter_id INTEGER, type TEXT, title TEXT, link TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS tests
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, class TEXT, subject TEXT, price INTEGER)''')

    # NEW: App Configuration Table (For Developer Mode)
    c.execute('''CREATE TABLE IF NOT EXISTS app_config
                 (key TEXT PRIMARY KEY, value TEXT)''')

    # Set Defaults if not exist
    defaults = {
        "app_name": "Rank1 Academy",
        "welcome_msg": "Your Gateway to Success",
        "banner_url": "https://via.placeholder.com/800x200.png?text=Welcome+to+Rank1",
        "notice_text": "📢 New Batch starting from Monday! Join now.",
        "show_notice": "True"
    }
    
    for key, val in defaults.items():
        try:
            c.execute("INSERT INTO app_config (key, value) VALUES (?,?)", (key, val))
        except sqlite3.IntegrityError:
            pass # Already exists

    conn.commit()
    conn.close()

# --- DB HELPER FUNCTIONS ---
def run_query(query, params=(), fetch=False):
    conn = sqlite3.connect('rank1_dynamic.db')
    c = conn.cursor()
    try:
        c.execute(query, params)
        if fetch:
            return c.fetchall()
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def get_config(key):
    res = run_query("SELECT value FROM app_config WHERE key=?", (key,), fetch=True)
    return res[0][0] if res else ""

def set_config(key, value):
    conn = sqlite3.connect('rank1_dynamic.db')
    c = conn.cursor()
    c.execute("REPLACE INTO app_config (key, value) VALUES (?,?)", (key, value))
    conn.commit()
    conn.close()

def get_user(username):
    return run_query("SELECT * FROM users WHERE username=?", (username,), fetch=True)

# --- APP CONFIG ---
st.set_page_config(page_title="Rank1", page_icon="🎓", layout="wide")
init_db()

# --- CSS STYLING ---
st.markdown("""
<style>
    [data-testid="stSidebarNav"] {display: none;}
    .stButton>button { width: 100%; height: 90px; border-radius: 12px; font-size: 18px; }
    .notice-bar {
        background-color: #ff4b4b; color: white; padding: 10px; text-align: center; font-weight: bold; border-radius: 5px; margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'current_view' not in st.session_state:
    st.session_state.current_view = "Home"
if 'selected_class' not in st.session_state:
    st.session_state.selected_class = None
if 'selected_subject_id' not in st.session_state:
    st.session_state.selected_subject_id = None

# ==========================================
# 🛑 PART 1: LOGIN / SIGNUP
# ==========================================
if not st.session_state.logged_in:
    # Dynamic Title
    app_name = get_config("app_name")
    st.title(f"🎓 {app_name}")
    
    tab1, tab2, tab3 = st.tabs(["🔐 Login", "📝 Sign Up", "🛠 Admin"])

    with tab1:
        l_user = st.text_input("Mobile / Email", key="l_u")
        l_pass = st.text_input("Password", type="password", key="l_p")
        if st.button("Login Now"):
            user_data = get_user(l_user)
            if user_data and user_data[0][1] == l_pass:
                st.session_state.logged_in = True
                st.session_state.user_id = l_user
                st.rerun()
            else:
                st.error("Wrong details.")

    with tab2:
        s_user = st.text_input("Mobile / Email", key="s_u")
        s_pass = st.text_input("Create Password", type="password", key="s_p")
        if st.button("Create Account"):
            if s_user and s_pass:
                if run_query("INSERT INTO users (username, password) VALUES (?,?)", (s_user, s_pass)):
                    st.success("Account Created! Please Login.")
                else:
                    st.error("Already registered.")

    with tab3:
        if st.button("Admin Login"):
            st.session_state.logged_in = True
            st.session_state.user_id = "ADMIN"
            st.rerun()

# ==========================================
# 🚀 PART 2: INSIDE APP
# ==========================================
else:
    # --- ADMIN PANEL ---
    if st.session_state.user_id == "ADMIN":
        st.sidebar.title("🛠 Admin Panel")
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()
        
        st.title("Admin Control Room")
        choice = st.radio("Manage:", ["Subjects/Chapters", "Content/PDF", "Tests", "⚙️ Developer Options"], horizontal=True)
        
        # 1. Developer Options (Dynamic Home Page)
        if choice == "⚙️ Developer Options":
            st.subheader("🎨 Customize App Appearance")
            with st.form("dev_settings"):
                new_name = st.text_input("App Name", value=get_config("app_name"))
                new_msg = st.text_input("Welcome Subtitle", value=get_config("welcome_msg"))
                new_banner = st.text_input("Banner Image URL", value=get_config("banner_url"))
                new_notice = st.text_input("Announcement Text (Marquee)", value=get_config("notice_text"))
                show_notice = st.checkbox("Show Announcement Bar?", value=(get_config("show_notice") == "True"))
                
                if st.form_submit_button("Update App Design"):
                    set_config("app_name", new_name)
                    set_config("welcome_msg", new_msg)
                    set_config("banner_url", new_banner)
                    set_config("notice_text", new_notice)
                    set_config("show_notice", "True" if show_notice else "False")
                    st.success("Settings Updated! Check Home Page.")

        # 2. Add Subjects/Chapters
        elif choice == "Subjects/Chapters":
            c1, c2 = st.columns(2)
            with c1:
                with st.form("add_sub"):
                    st.write("**Add Subject**")
                    n = st.text_input("Name"); i = st.selectbox("Icon", ["📐","🔬","🌍","📖","💻"]); c = st.selectbox("Class", [f"Class {x}" for x in range(6,13)])
                    if st.form_submit_button("Add Subject"):
                        run_query("INSERT INTO subjects (name, class, icon) VALUES (?,?,?)", (n,c,i)); st.success("Added")
            with c2:
                with st.form("add_chap"):
                    st.write("**Add Chapter**")
                    subs = run_query("SELECT id, name FROM subjects", fetch=True)
                    if subs:
                        sid = st.selectbox("Subject", [s[0] for s in subs], format_func=lambda x: next(y[1] for y in subs if y[0]==x))
                        cn = st.text_input("Chapter Name")
                        if st.form_submit_button("Add Chapter"):
                            run_query("INSERT INTO chapters (subject_id, name) VALUES (?,?)", (sid, cn)); st.success("Added")

        # 3. Add Content
        elif choice == "Content/PDF":
            st.write("Upload PDF Links")
            # Simplified logic for demo
            link = st.text_input("Link"); tit = st.text_input("Title")
            if st.button("Save"): st.success("Saved")
            
        # 4. Tests
        elif choice == "Tests":
            st.write("Create Tests")
            tn = st.text_input("Test Name"); tp = st.number_input("Price")
            if st.button("Create"): st.success("Created")

    # --- STUDENT APP ---
    else:
        user_row = get_user(st.session_state.user_id)[0]
        
        # Onboarding
        if user_row[3] is None:
            st.title("⚙️ Profile Setup")
            role = st.radio("Role", ["Student", "Teacher"])
            board = st.selectbox("Board", ["CBSE", "State Board"])
            state = st.selectbox("State", ["Bihar", "Jharkhand"]) if board == "State Board" else "N/A"
            if st.button("Save"):
                run_query("UPDATE users SET role=?, board=?, state=? WHERE username=?", (role, board, state, st.session_state.user_id))
                st.rerun()
        
        else:
            # --- CUSTOM NAVBAR ---
            c1, c2, c3, c4 = st.columns(4)
            if c1.button("🏠 Home"): 
                st.session_state.current_view = "Home"
                st.session_state.selected_subject_id = None
            if c2.button("🏆 Tests"): st.session_state.current_view = "Tests"
            if c3.button("📰 News"): st.session_state.current_view = "News"
            if c4.button("🚪 Exit"): 
                st.session_state.logged_in = False
                st.rerun()
            st.divider()

            # --- DYNAMIC HOME PAGE ---
            if st.session_state.current_view == "Home":
                
                # 1. SHOW ANNOUNCEMENT (Developer Controlled)
                if get_config("show_notice") == "True":
                    st.markdown(f'<div class="notice-bar">📢 {get_config("notice_text")}</div>', unsafe_allow_html=True)

                # 2. SHOW BANNER (Developer Controlled)
                st.image(get_config("banner_url"), use_column_width=True)
                st.caption(get_config("welcome_msg"))

                # 3. CLASS & SUBJECT LOGIC (As before)
                if st.session_state.selected_subject_id is None:
                    st.subheader("Select Class")
                    cls = st.selectbox("Choose Class", [f"Class {i}" for i in range(6,13)])
                    st.write("---")
                    
                    subs = run_query("SELECT id, name, icon FROM subjects WHERE class=?", (cls,), fetch=True)
                    if subs:
                        cols = st.columns(3)
                        for i, s in enumerate(subs):
                            if cols[i%3].button(f"{s[2]}\n{s[1]}", key=s[0]):
                                st.session_state.selected_subject_id = s[0]
                                st.session_state.selected_subject_name = s[1]
                                st.rerun()
                    else:
                        st.info("No subjects added yet.")
                else:
                    if st.button("⬅️ Back"):
                        st.session_state.selected_subject_id = None
                        st.rerun()
                    st.title(st.session_state.selected_subject_name)
                    # Chapters Logic
                    chaps = run_query("SELECT id, name FROM chapters WHERE subject_id=?", (st.session_state.selected_subject_id,), fetch=True)
                    if chaps:
                        sel_c = st.selectbox("Select Chapter", [c[1] for c in chaps])
                        st.write(f"Content for {sel_c}...")
                    else:
                        st.warning("No chapters.")

            elif st.session_state.current_view == "Tests":
                st.subheader("Tests")
                st.write("Test Series here...")

            elif st.session_state.current_view == "News":
                st.subheader("News")
                try:
                    feed = feedparser.parse("https://news.google.com/rss/search?q=education+india")
                    for e in feed.entries[:5]: st.write(f"- {e.title}")
                except: st.error("No internet")
