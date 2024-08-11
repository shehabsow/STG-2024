import streamlit as st
import pandas as pd
import pytz
from datetime import datetime, timedelta
import sqlite3
import json
import os

# إعدادات Streamlit
st.set_page_config(
    layout="wide",
    page_title='STG-2024',
    page_icon='🪙')

egypt_tz = pytz.timezone('Africa/Cairo')

# إعداد قاعدة البيانات SQLite
def init_db():
    conn = sqlite3.connect('stg2024.db')
    c = conn.cursor()

    # إنشاء جداول المستخدمين والمواد وسجلات النشاط والتنبيهات
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            first_login BOOLEAN,
            name TEXT NOT NULL,
            last_password_update TEXT NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS material (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            actual_quantity INTEGER NOT NULL
        )
    ''')
    c.execute('''
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
    c.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# تحميل بيانات المستخدمين
def load_users():
    conn = sqlite3.connect('stg2024.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users')
    users = {row[0]: {'password': row[1], 'first_login': row[2], 'name': row[3], 'last_password_update': row[4]} for row in c.fetchall()}
    conn.close()
    return users

# حفظ بيانات المستخدمين
def save_users(users):
    conn = sqlite3.connect('stg2024.db')
    c = conn.cursor()
    for username, user_data in users.items():
        c.execute('''
            INSERT OR REPLACE INTO users (username, password, first_login, name, last_password_update)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, user_data['password'], user_data['first_login'], user_data['name'], user_data['last_password_update']))
    conn.commit()
    conn.close()

# تحميل بيانات المواد
def load_material():
    conn = sqlite3.connect('stg2024.db')
    c = conn.cursor()
    c.execute('SELECT * FROM material')
    df = pd.DataFrame(c.fetchall(), columns=['id', 'item_name', 'actual_quantity'])
    conn.close()
    return df

# حفظ بيانات المواد
def save_material(df):
    conn = sqlite3.connect('stg2024.db')
    c = conn.cursor()
    c.execute('DELETE FROM material')
    for _, row in df.iterrows():
        c.execute('''
            INSERT INTO material (item_name, actual_quantity)
            VALUES (?, ?)
        ''', (row['item_name'], row['actual_quantity']))
    conn.commit()
    conn.close()

# حفظ السجلات
def save_logs(logs):
    conn = sqlite3.connect('stg2024.db')
    c = conn.cursor()
    for log in logs:
        c.execute('''
            INSERT INTO logs (user, time, item, old_quantity, new_quantity, operation)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (log['user'], log['time'], log['item'], log['old_quantity'], log['new_quantity'], log['operation']))
    conn.commit()
    conn.close()

# حفظ التنبيهات
def save_alerts(alerts):
    conn = sqlite3.connect('stg2024.db')
    c = conn.cursor()
    c.execute('DELETE FROM alerts')
    for alert in alerts:
        c.execute('''
            INSERT INTO alerts (item_name)
            VALUES (?)
        ''', (alert,))
    conn.commit()
    conn.close()

# دالة تسجيل الدخول
def login(username, password):
    users = load_users()
    if username in users and users[username]['password'] == password:
        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.first_login = users[username]['first_login']
        last_password_update = datetime.strptime(users[username]['last_password_update'], '%Y-%m-%d %H:%M:%S.%f%z')
        if datetime.now(egypt_tz) - last_password_update > timedelta(days=30):
            st.session_state.password_expired = True
        else:
            st.session_state.password_expired = False
    else:
        st.error("Incorrect username or password")

# دالة تحديث كلمة المرور
def update_password(username, new_password, confirm_new_password):
    if new_password == confirm_new_password:
        users = load_users()
        users[username]['password'] = new_password
        users[username]['first_login'] = False
        users[username]['last_password_update'] = str(datetime.now(egypt_tz))
        save_users(users)
        st.session_state.first_login = False
        st.session_state.password_expired = False
        st.success("Password updated successfully!")
    else:
        st.error("Passwords do not match!")

# دالة تحديث الكمية
def update_quantity(row_index, quantity, operation, username):
    df = st.session_state.df
    old_quantity = df.loc[row_index, 'actual_quantity']
    if operation == 'add':
        df.loc[row_index, 'actual_quantity'] += quantity
    elif operation == 'subtract':
        df.loc[row_index, 'actual_quantity'] -= quantity
    new_quantity = df.loc[row_index, 'actual_quantity']
    save_material(df)
    st.success(f"Quantity updated successfully by {username}! New Quantity: {int(new_quantity)}")
    
    log_entry = {
        'user': username,
        'time': datetime.now(egypt_tz).strftime('%Y-%m-%d %H:%M:%S'),
        'item': df.loc[row_index, 'item_name'],
        'old_quantity': old_quantity,
        'new_quantity': new_quantity,
        'operation': operation
    }
    st.session_state.logs.append(log_entry)
    
    save_logs(st.session_state.logs)
    
    check_quantities()

def check_quantities():
    df = st.session_state.df
    new_alerts = df[df['actual_quantity'] < 100]['item_name'].tolist()
    st.session_state.alerts = new_alerts
    save_alerts(new_alerts)

def check_tab_quantities(tab_name, min_quantity):
    df_tab = st.session_state.df[st.session_state.df['item_name'] == tab_name]
    tab_alerts = df_tab[df_tab['actual_quantity'] < min_quantity]['item_name'].tolist()
    return tab_alerts, df_tab

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

# التحقق من تسجيل الدخول
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.logs = []

if 'logs' not in st.session_state:
    st.session_state.logs = []

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
        # التحقق من وجود username في session_state
        if 'username' in st.session_state:
            users = load_users()
            username = st.session_state.username
            if username in users:
                user_name = users[username]['name']
                st.markdown(f"<div style='text-align: right; font-size: 20px; color: green;'>Logged in by: {user_name}</div>", unsafe_allow_html=True)
            else:
                st.error("User information not found.")
        else:
            st.error("Username not found in session state.")
        
        # قراءة البيانات
        if 'df' not in st.session_state:
            st.session_state.df = load_material()

        try:
            conn = sqlite3.connect('stg2024.db')
            c = conn.cursor()
            c.execute('SELECT * FROM logs')
            st.session_state.logs = [dict(zip([column[0] for column in c.description], row)) for row in c.fetchall()]
            conn.close()
        except FileNotFoundError:
            st.session_state.logs = []
                
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
                
                tabs = [
                    'Reel Label (Small)', 'Reel Label (Large)',
                    'Ink Reels for Label', 'Red Tape', 'Adhasive Tape', 'Cartridges', 'MultiPharma Cartridge'
                ]
                for tab_name in tabs:
                    with st.tab(tab_name):
                        df_tab = st.session_state.df[st.session_state.df['item_name'] == tab_name].sort_values(by='item_name')
                        st.dataframe(df_tab, width=2000)
                        col4, col5, col6 = st.columns([2, 1, 2])
                        with col4:
                            display_tab(tab_name, 100)  # قيمة `100` يمكن تعديلها حسب الحاجة
                
            if __name__ == '__main__':
                main()
        
        elif page == 'View Logs':
            st.header('User Activity Logs')
            if st.session_state.logs:
                logs_df = pd.DataFrame(st.session_state.logs)
                st.dataframe(logs_df, width=1000, height=400)
                csv = logs_df.to_csv(index=False)
                st.download_button(label="Download Logs as sheet", data=csv, file_name='user_logs.csv', mime='text/csv')
            else:
                st.write("No logs available.")
