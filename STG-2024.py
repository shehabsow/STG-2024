import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# إعداد صفحة التطبيق
st.set_page_config(layout="wide", page_title='Materials Management', page_icon='🪙')

# إنشاء اتصال بقاعدة بيانات SQLite
conn = sqlite3.connect('new_materials.db')
c = conn.cursor()

# إنشاء الجداول إذا لم تكن موجودة
c.execute('''
CREATE TABLE IF NOT EXISTS materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name TEXT,
    actual_quantity INTEGER,
    monthly_quantity INTEGER,
    description TEXT
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    name TEXT
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    time TEXT,
    item_id INTEGER,
    old_quantity INTEGER,
    new_quantity INTEGER,
    operation TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (item_id) REFERENCES materials (id)
)
''')

conn.commit()

# إضافة المواد الافتراضية إلى قاعدة البيانات إذا لم تكن موجودة
def add_default_materials():
    c.execute("SELECT COUNT(*) FROM materials")
    count = c.fetchone()[0]
    if count == 0:
        default_materials = [
            ('Reel Label (Small)', 50, 100, 'Description for Reel Label (Small)'),
            ('Reel Label (Large)', 100, 200, 'Description for Reel Label (Large)'),
            ('Ink Reels for Label', 150, 300, 'Description for Ink Reels for Label'),
            ('Red Tape', 30, 50, 'Description for Red Tape'),
            ('Adhesive Tape', 200, 400, 'Description for Adhesive Tape'),
            ('Cartridges', 60, 120, 'Description for Cartridges'),
            ('MultiPharma Cartridge', 20, 40, 'Description for MultiPharma Cartridge')
        ]
        c.executemany("INSERT INTO materials (item_name, actual_quantity, monthly_quantity, description) VALUES (?, ?, ?, ?)", default_materials)
        conn.commit()

# إضافة المستخدمين الافتراضيين إلى قاعدة البيانات إذا لم تكن موجودة
def add_default_users():
    c.execute("SELECT COUNT(*) FROM users")
    count = c.fetchone()[0]
    if count == 0:
        default_users = [
            ('user1', 'password1', 'User One'),
            ('user2', 'password2', 'User Two'),
            ('user3', 'password3', 'User Three'),
            ('user4', 'password4', 'User Four'),
            ('user5', 'password5', 'User Five')
        ]
        c.executemany("INSERT INTO users (username, password, name) VALUES (?, ?, ?)", default_users)
        conn.commit()

# وظيفة تسجيل الدخول
def login(username, password):
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = c.fetchone()
    if user:
        st.session_state.logged_in = True
        st.session_state.user_id = user[0]
        st.session_state.username = username
        st.session_state.name = user[3]
    else:
        st.error("Incorrect username or password")

# وظيفة تحديث الكمية
def update_quantity(item_id, quantity, operation, user_id):
    c.execute("SELECT actual_quantity FROM materials WHERE id = ?", (item_id,))
    result = c.fetchone()
    if result:
        last_quantity = result[0]
        if operation == 'add':
            new_quantity = last_quantity + quantity
        elif operation == 'subtract':
            new_quantity = last_quantity - quantity
        c.execute("UPDATE materials SET actual_quantity = ? WHERE id = ?", (new_quantity, item_id))
        conn.commit()
        st.success(f"Quantity updated successfully! New Quantity: {new_quantity}")
        log_entry = (user_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), item_id, last_quantity, new_quantity, operation)
        c.execute("INSERT INTO logs (user_id, time, item_id, old_quantity, new_quantity, operation) VALUES (?, ?, ?, ?, ?, ?)", log_entry)
        conn.commit()
    else:
        st.error("No data found for the selected item.")

# وظيفة عرض علامة التبويب
def display_tab(item_name):
    st.header(f'{item_name}')
    c.execute("SELECT * FROM materials WHERE item_name = ?", (item_name,))
    df_tab = c.fetchone()
    if df_tab:
        st.markdown(f"""
        <div style='font-size: 20px; color: blue;'>Selected Item: {df_tab[1]}</div>
        <div style='font-size: 20px; color: blue;'>Current Quantity: {df_tab[2]}</div>
        <div style='font-size: 20px; color: blue;'>Description: {df_tab[4]}</div>
        """, unsafe_allow_html=True)

        quantity = st.number_input(f'Enter quantity for {item_name}:', min_value=1, step=1, key=f'{item_name}_quantity')
        operation = st.radio(f'Choose operation for {item_name}:', ('add', 'subtract'), key=f'{item_name}_operation')

        if st.button('Update Quantity', key=f'{item_name}_update_button'):
            update_quantity(df_tab[0], quantity, operation, st.session_state.user_id)
    else:
        st.error(f"No data available for {item_name}")

# وظيفة عرض السجلات
def display_logs():
    c.execute("SELECT logs.id, users.name, logs.time, materials.item_name, logs.old_quantity, logs.new_quantity, logs.operation FROM logs JOIN users ON logs.user_id = users.id JOIN materials ON logs.item_id = materials.id")
    logs = c.fetchall()
    if logs:
        logs_df = pd.DataFrame(logs, columns=['Log ID', 'User', 'Time', 'Item', 'Old Quantity', 'New Quantity', 'Operation'])
        st.dataframe(logs_df)
    else:
        st.info("No logs available.")

# تحميل البيانات عند بدء تشغيل التطبيق
add_default_materials()
add_default_users()

# بدء تشغيل التطبيق
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        login(username, password)
else:
    st.title(f"Welcome {st.session_state.name}")
    st.sidebar.title("Navigation")
    pages = ["Materials", "Logs"]
    page = st.sidebar.radio("Go to", pages)

    if page == "Materials":
        tab_names = ['Reel Label (Small)', 'Reel Label (Large)', 'Ink Reels for Label', 'Red Tape', 'Adhesive Tape', 'Cartridges', 'MultiPharma Cartridge']
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(tab_names)

        with tab1:
            display_tab('Reel Label (Small)')
        with tab2:
            display_tab('Reel Label (Large)')
        with tab3:
            display_tab('Ink Reels for Label')
        with tab4:
            display_tab('Red Tape')
        with tab5:
            display_tab('Adhesive Tape')
        with tab6:
            display_tab('Cartridges')
        with tab7:
            display_tab('MultiPharma Cartridge')
    elif page == "Logs":
        display_logs()

conn.close()
