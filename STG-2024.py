import streamlit as st
import pandas as pd
import pytz
import sqlite3
from datetime import datetime, timedelta

# إعداد صفحة التطبيق
st.set_page_config(
    layout="wide",
    page_title='STG-2024',
    page_icon='🪙')

egypt_tz = pytz.timezone('Africa/Cairo')

# إنشاء اتصال بقاعدة بيانات SQLite
conn = sqlite3.connect('materials.db')
c = conn.cursor()

# إنشاء الجداول إذا لم تكن موجودة
c.execute('''
CREATE TABLE IF NOT EXISTS materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name TEXT,
    actual_quantity INTEGER,
    monthly_quantity INTEGER
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT,
    first_login BOOLEAN,
    name TEXT,
    last_password_update TEXT
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT,
    time TEXT,
    item TEXT,
    old_quantity INTEGER,
    new_quantity INTEGER,
    operation TEXT
)
''')

conn.commit()

# تحميل بيانات المستخدمين
def load_users():
    c.execute("SELECT * FROM users")
    users = c.fetchall()
    if not users:
        users = {
            "knhp322": {"password": "knhp322", "first_login": True, "name": "Shehab Ayman", "last_password_update": str(datetime.now(egypt_tz))},
            "KFXW551": {"password": "KFXW551", "first_login": True, "name": "Hossameldin Mostafa", "last_password_update": str(datetime.now(egypt_tz))},
            "knvp968": {"password": "knvp968", "first_login": True, "name": "Mohamed Nader", "last_password_update": str(datetime.now(egypt_tz))},
            "kcqw615": {"password": "kcqw615", "first_login": True, "name": "Tareek Mahmoud", "last_password_update": str(datetime.now(egypt_tz))}
        }
        for username, data in users.items():
            c.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)",
                      (username, data['password'], data['first_login'], data['name'], data['last_password_update']))
        conn.commit()
    else:
        users = {user[0]: {"password": user[1], "first_login": user[2], "name": user[3], "last_password_update": user[4]} for user in users}
    return users

# حفظ بيانات المستخدمين في قاعدة البيانات
def save_users(users):
    for username, data in users.items():
        c.execute("UPDATE users SET password = ?, first_login = ?, last_password_update = ? WHERE username = ?",
                  (data['password'], data['first_login'], data['last_password_update'], username))
    conn.commit()

# تحميل السجلات من قاعدة البيانات
def load_logs():
    c.execute("SELECT * FROM logs")
    logs = c.fetchall()
    return logs

# حفظ السجلات في قاعدة البيانات
def save_logs(logs):
    c.executemany("INSERT INTO logs (user, time, item, old_quantity, new_quantity, operation) VALUES (?, ?, ?, ?, ?, ?)", logs)
    conn.commit()

# إضافة المواد الافتراضية إلى قاعدة البيانات إذا لم تكن موجودة
def add_default_materials():
    c.execute("SELECT COUNT(*) FROM materials")
    count = c.fetchone()[1]
    if count == 1:
        default_materials = [
            ('Reel Label (Small)', 50, 100),
            ('Reel Label (Large)', 100, 200),
            ('Ink Reels for Label', 150, 300),
            ('Red Tape', 30, 50),
            ('Adhesive Tape', 200, 400),
            ('Cartridges', 60, 120),
            ('MultiPharma Cartridge', 20, 40)
        ]
        c.executemany("INSERT INTO materials (item_name, actual_quantity, monthly_quantity) VALUES (?, ?, ?)", default_materials)
        conn.commit()

# وظيفة تسجيل الدخول
def login(username, password):
    if username in users and users[username]["password"] == password:
        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.first_login = users[username]["first_login"]
        last_password_update = datetime.strptime(users[username]["last_password_update"], '%Y-%m-%d %H:%M:%S.%f%z')
        if datetime.now(egypt_tz) - last_password_update > timedelta(days=30):
            st.session_state.password_expired = True
        else:
            st.session_state.password_expired = False
    else:
        st.error("Incorrect username or password")

# وظيفة تحديث كلمة المرور
def update_password(username, new_password, confirm_new_password):
    if new_password == confirm_new_password:
        users[username]["password"] = new_password
        users[username]["first_login"] = False
        users[username]["last_password_update"] = str(datetime.now(egypt_tz))
        save_users(users)
        st.session_state.first_login = False
        st.session_state.password_expired = False
        st.success("Password updated successfully!")
    else:
        st.error("Passwords do not match!")

# وظيفة تحديث الكمية
def update_quantity(row_index, quantity, operation, username):
    c.execute("SELECT actual_quantity FROM materials WHERE id = ?", (row_index,))
    result = c.fetchone()
    if result:
        last_quantity = result[0]
        if operation == 'add':
            new_quantity = last_quantity + quantity
        elif operation == 'subtract':
            new_quantity = last_quantity - quantity
        c.execute("UPDATE materials SET actual_quantity = ? WHERE id = ?", (new_quantity, row_index))
        conn.commit()
        st.success(f"Quantity updated successfully by {username}! New Quantity: {new_quantity}")
        log_entry = (username, datetime.now(egypt_tz).strftime('%Y-%m-%d %H:%M:%S'), row_index, last_quantity, new_quantity, operation)
        c.execute("INSERT INTO logs (user, time, item, old_quantity, new_quantity, operation) VALUES (?, ?, ?, ?, ?, ?)", log_entry)
        conn.commit()
        check_quantities()
    else:
        st.error("No data found for the selected item.")

# وظيفة التحقق من الكميات
def check_quantities():
    c.execute("SELECT item_name FROM materials WHERE actual_quantity < 100")
    new_alerts = c.fetchall()
    st.session_state.alerts = [alert[0] for alert in new_alerts]

# وظيفة التحقق من الكميات لعناصر محددة
def check_tab_quantities(tab_name, min_quantity):
    c.execute("SELECT * FROM materials WHERE item_name = ?", (tab_name,))
    df_tab = c.fetchall()
    tab_alerts = [item for item in df_tab if item[2] < min_quantity]
    return tab_alerts, df_tab

# وظيفة عرض علامة التبويب
def display_tab(tab_name, min_quantity):
    st.header(f'{tab_name}')
    c.execute("SELECT * FROM materials WHERE item_name = ?", (tab_name,))
    df_tab = c.fetchall()
    if df_tab:
        df_tab_df = pd.DataFrame(df_tab, columns=['ID', 'Item Name', 'Actual Quantity', 'Monthly Quantity'])
        row_number = st.number_input(f'Select row number for {tab_name}:', min_value=0, max_value=len(df_tab_df)-1, step=1, key=f'{tab_name}_row_number')
        item, quantity = df_tab_df.iloc[row_number][['Item Name', 'Actual Quantity']]

        st.markdown(f"""
        <div style='font-size: 20px; color: blue;'>Selected Item: {item}</div>
        <div style='font-size: 20px; color: blue;'>Current Quantity: {quantity}</div>
        """, unsafe_allow_html=True)

        quantity = st.number_input(f'Enter quantity for {tab_name}:', min_value=1, step=1, key=f'{tab_name}_quantity')
        operation = st.radio(f'Choose operation for {tab_name}:', ('add', 'subtract'), key=f'{tab_name}_operation')

        if st.button('Update Quantity', key=f'{tab_name}_update_button'):
            update_quantity(df_tab_df.iloc[row_number]['ID'], quantity, operation, st.session_state.username)

        tab_alerts, _ = check_tab_quantities(tab_name, min_quantity)
        if tab_alerts:
            st.error(f"Low stock for items in {tab_name}:")
            st.dataframe(df_tab_df.style.applymap(lambda x: 'background-color: red' if x < min_quantity else '', subset=['Actual Quantity']))
    else:
        st.error(f"No data available for {tab_name}")

# وظيفة مسح السجلات
def clear_logs():
    c.execute("DELETE FROM logs")
    conn.commit()
    st.success("Logs cleared successfully!")

# تحميل المستخدمين والسجلات
users = load_users()
st.session_state.logs = load_logs()

# إضافة المواد الافتراضية
add_default_materials()

# واجهة تسجيل الدخول
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.first_login = False
    st.session_state.password_expired = False

if not st.session_state.logged_in:
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        login(username, password)
else:
    if st.session_state.first_login or st.session_state.password_expired:
        st.title("Update Password")
        new_password = st.text_input("New Password", type="password")
        confirm_new_password = st.text_input("Confirm New Password", type="password")
        if st.button("Update Password"):
            update_password(st.session_state.username, new_password, confirm_new_password)
    else:
        st.title("Materials Management")

        tab_names = ['Reel Label (Small)', 'Reel Label (Large)', 'Ink Reels for Label', 'Red Tape', 'Adhesive Tape', 'Cartridges', 'MultiPharma Cartridge']
        tab_min_quantities = [50, 50, 50, 50, 50, 50, 50]

        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(tab_names)

        with tab1:
            display_tab('Reel Label (Small)', tab_min_quantities[0])

        with tab2:
            display_tab('Reel Label (Large)', tab_min_quantities[1])

        with tab3:
            display_tab('Ink Reels for Label', tab_min_quantities[2])

        with tab4:
            display_tab('Red Tape', tab_min_quantities[3])

        with tab5:
            display_tab('Adhesive Tape', tab_min_quantities[4])

        with tab6:
            display_tab('Cartridges', tab_min_quantities[5])

        with tab7:
            display_tab('MultiPharma Cartridge', tab_min_quantities[6])

        st.header("Alerts")
        if 'alerts' not in st.session_state:
            st.session_state.alerts = []
        if st.session_state.alerts:
            st.error(f"Low stock for items: {', '.join(st.session_state.alerts)}")
        else:
            st.success("All items are sufficiently stocked.")

        if st.button("Clear Logs"):
            clear_logs()

        st.header("Logs")
        logs_df = pd.DataFrame(st.session_state.logs, columns=['ID', 'User', 'Time', 'Item', 'Old Quantity', 'New Quantity', 'Operation'])
        st.dataframe(logs_df)

conn.close()
