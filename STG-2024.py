import streamlit as st
import pandas as pd
import pytz
from datetime import datetime, timedelta
import sqlite3
import json

# إعداد قاعدة البيانات
def create_database():
    conn = sqlite3.connect('app_database.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            first_login BOOLEAN NOT NULL,
            name TEXT NOT NULL,
            last_password_update TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS material (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            actual_quantity INTEGER NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL,
            time TEXT NOT NULL,
            item TEXT NOT NULL,
            old_quantity INTEGER NOT NULL,
            new_quantity INTEGER NOT NULL,
            operation TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

create_database()

# تحميل بيانات المستخدمين من قاعدة البيانات
def load_users():
    conn = sqlite3.connect('app_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users')
    users = {row[0]: {"password": row[1], "first_login": row[2], "name": row[3], "last_password_update": row[4]} for row in cursor.fetchall()}
    conn.close()
    return users

# حفظ بيانات المستخدمين إلى قاعدة البيانات
def save_users(users):
    conn = sqlite3.connect('app_database.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM users')
    for username, user_info in users.items():
        cursor.execute('INSERT INTO users (username, password, first_login, name, last_password_update) VALUES (?, ?, ?, ?, ?)',
                       (username, user_info["password"], user_info["first_login"], user_info["name"], user_info["last_password_update"]))
    conn.commit()
    conn.close()

# تحميل المواد من قاعدة البيانات
def load_material():
    conn = sqlite3.connect('app_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM material')
    data = cursor.fetchall()
    df = pd.DataFrame(data, columns=['id', 'item_name', 'actual_quantity'])
    conn.close()
    return df

# حفظ المواد إلى قاعدة البيانات
def save_material(df):
    conn = sqlite3.connect('app_database.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM material')
    for _, row in df.iterrows():
        cursor.execute('INSERT INTO material (item_name, actual_quantity) VALUES (?, ?)', (row['item_name'], row['actual_quantity']))
    conn.commit()
    conn.close()

# تحميل السجلات من قاعدة البيانات
def load_logs():
    conn = sqlite3.connect('app_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM logs')
    logs = cursor.fetchall()
    conn.close()
    return logs

# حفظ السجلات إلى قاعدة البيانات
def save_logs(logs):
    conn = sqlite3.connect('app_database.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM logs')
    cursor.executemany('INSERT INTO logs (user, time, item, old_quantity, new_quantity, operation) VALUES (?, ?, ?, ?, ?, ?)', logs)
    conn.commit()
    conn.close()

# تحميل التنبيهات من قاعدة البيانات
def load_alerts():
    conn = sqlite3.connect('app_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT item_name FROM alerts')
    alerts = [row[0] for row in cursor.fetchall()]
    conn.close()
    return alerts

# حفظ التنبيهات إلى قاعدة البيانات
def save_alerts(alerts):
    conn = sqlite3.connect('app_database.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM alerts')
    cursor.executemany('INSERT INTO alerts (item_name) VALUES (?)', [(alert,) for alert in alerts])
    conn.commit()
    conn.close()

# تسجيل الدخول
def login(username, password):
    users = load_users()
    if username in users and users[username]['password'] == password:
        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.first_login = users[username]['first_login']
        if st.session_state.first_login:
            st.session_state.refreshed = False
    else:
        st.error("Invalid username or password.")

# تحديث كلمة المرور
def update_password(username, new_password, confirm_new_password):
    if new_password != confirm_new_password:
        st.error("Passwords do not match.")
        return
    
    conn = sqlite3.connect('app_database.db')
    cursor = conn.cursor()
    
    cursor.execute('UPDATE users SET password = ?, first_login = ? WHERE username = ?', (new_password, False, username))
    conn.commit()
    conn.close()
    
    st.success("Password updated successfully!")
    st.session_state.first_login = False

# تحديث الكمية
def update_quantity(row_index, quantity, operation, username):
    conn = sqlite3.connect('app_database.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM material WHERE id = ?', (row_index,))
    row = cursor.fetchone()
    old_quantity = row[2]
    
    new_quantity = old_quantity + quantity if operation == 'add' else old_quantity - quantity
    
    cursor.execute('UPDATE material SET actual_quantity = ? WHERE id = ?', (new_quantity, row_index))
    conn.commit()
    
    log_entry = (username, datetime.now(egypt_tz).strftime('%Y-%m-%d %H:%M:%S'), row[1], old_quantity, new_quantity, operation)
    cursor.execute('INSERT INTO logs (user, time, item, old_quantity, new_quantity, operation) VALUES (?, ?, ?, ?, ?, ?)', log_entry)
    
    conn.commit()
    conn.close()
    
    st.success(f"Quantity updated successfully by {username}! New Quantity: {new_quantity}")
    
    check_quantities()

# التحقق من الكميات
def check_quantities():
    df = load_material()
    new_alerts = [row['item_name'] for _, row in df.iterrows() if row['actual_quantity'] < 100]
    
    save_alerts(new_alerts)

# التحقق من الكميات لكل تبويب
def check_tab_quantities(tab_name, min_quantity):
    df_tab = st.session_state.df[st.session_state.df['item_name'] == tab_name]
    tab_alerts = df_tab[df_tab['actual_quantity'] < min_quantity]['item_name'].tolist()
    return tab_alerts, df_tab

# عرض التبويبات
def display_tab(tab_name, min_quantity):
    st.header(f'{tab_name}')
    row_number = st.number_input(f'Select row number for {tab_name}:', min_value=0, max_value=len(st.session_state.df)-1, step=1, key=f'{tab_name}_row_number')
    
    st.markdown(f"""
    <div style='font-size: 20px; color: blue;'>Selected Item: {st.session_state.df.loc[row_number, 'item_name']}</div>
    <div style='font-size: 20px; color: blue;'>Current Quantity: {int(st.session_state.df.loc[row_number, 'actual_quantity'])}</div>
    """, unsafe_allow_html=True)
    
    quantity = st.number_input(f'Enter quantity for {tab_name}:', min_value=1, step=1, key=f'{tab_name}_quantity')
    operation = st.radio(f'Choose operation for {tab_name}:', ('add', 'subtract'), key=f'{tab_name}_operation')

    if st.button('Update Quantity', key=f'{tab_name}_update_button'):
        update_quantity(row_number, quantity, operation, st.session_state.username)
    
    tab_alerts, df_tab = check_tab_quantities(tab_name, min_quantity)
    if tab_alerts:
        st.error(f"Low stock for items in {tab_name}:")
        st.dataframe(df_tab.style.applymap(lambda x: 'background-color: red' if x < min_quantity else '', subset=['actual_quantity']))

# واجهة تسجيل الدخول
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.logs = []

if 'logs' not in st.session_state:
    st.session_state.logs = load_logs()

if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            login(username, password)
else:
    if st.session_state.first_login:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.subheader("Change Password")
            new_password = st.text_input("New Password", type="password")
            confirm_new_password = st.text_input("Confirm Password", type="password")
            if st.button("Change Password"):
                if not new_password or not confirm_new_password:
                    st.error("Please fill in all the fields.")
                else:
                    update_password(st.session_state.username, new_password, confirm_new_password)
    else:
        st.markdown(f"<div style='text-align: right; font-size: 20px; color: green;'>Logged in by: {load_users()[st.session_state.username]['name']}</div>", unsafe_allow_html=True)
        
        if 'df' not in st.session_state:
            st.session_state.df = load_material()
                
        page = st.sidebar.radio('Select page', ['STG-2024', 'View Logs'])
        
        if page == 'STG-2024':
            def main():
                st.markdown("""
                <style>
                    .stProgress > div > div > div {
                        background-color: #FFD700;
                        border-radius: 50%;
                    }
                </style>
                """, unsafe_allow_html=True)
                
                with st.spinner("Data loaded successfully!"):
                    import time
                    time.sleep(1)
                
                col1, col2 = st.columns([2, 0.75])
                with col1:
                    st.markdown("""
                        <h2 style='text-align: center; font-size: 40px; color: red;'>
                            Find your parts
                        </h2>
                    """, unsafe_allow_html=True)
                
                with col2:
                    search_keyword = st.session_state.get('search_keyword', '')
                    search_keyword = st.text_input("Enter keyword to search:", search_keyword)
                    search_button = st.button("Search")
                    search_option = 'All Columns'
                
                def search_in_dataframe(df, keyword, option):
                    if option == 'All Columns':
                        result = df[df.apply(lambda row: row.astype(str).str.contains(keyword, case=False).any(), axis=1)]
                    else:
                        result = df[df[option].astype(str).str.contains(keyword, case=False)]
                    return result
                
                if st.session_state.get('refreshed', False):
                    st.session_state.search_keyword = ''
                    st.session_state.refreshed = False
                
                if search_button and search_keyword:
                    st.session_state.search_keyword = search_keyword
                    search_results = search_in_dataframe(st.session_state.df, search_keyword, search_option)
                    st.write(f"Search results for '{search_keyword}' in {search_option}:")
                    st.dataframe(search_results, width=1000, height=200)
                st.session_state.refreshed = True
                
                tabs = ['Reel Label (Small)', 'Reel Label (Large)', 'Ink Reels for Label', 'Red Tape', 'Adhasive Tape', 'Cartridges', 'MultiPharma Cartridge']
                for tab in tabs:
                    with st.expander(tab):
                        df_tab = st.session_state.df[st.session_state.df['item_name'] == tab].sort_values(by='item_name')
                        st.dataframe(df_tab, width=2000)
                        display_tab(tab, 100)  # Use the appropriate min_quantity for each tab
        
            if __name__ == '__main__':
                main()
        
        elif page == 'View Logs':
            logs_df = pd.DataFrame(st.session_state.logs, columns=['ID', 'User', 'Time', 'Item', 'Old Quantity', 'New Quantity', 'Operation'])
            st.dataframe(logs_df, width=1000, height=500)
            csv = logs_df.to_csv(index=False)
            st.download_button(label="Download Logs as CSV", data=csv, file_name='user_logs.csv', mime='text/csv')
