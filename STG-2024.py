import streamlit as st
import pandas as pd
import pytz
from datetime import datetime, timedelta
import json
import sqlite3

def create_database():
    conn = sqlite3.connect('my_database.db')
    c = conn.cursor()

    # إنشاء جدول للمواد
    c.execute('''
    CREATE TABLE IF NOT EXISTS materials (
        item_name TEXT,
        actual_quantity INTEGER
    )
    ''')

    # إنشاء جدول للسجلات
    c.execute('''
    CREATE TABLE IF NOT EXISTS logs (
        user TEXT,
        time TEXT,
        item TEXT,
        old_quantity INTEGER,
        new_quantity INTEGER,
        operation TEXT
    )
    ''')

    # إنشاء جدول للمستخدمين
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        first_login BOOLEAN,
        name TEXT,
        last_password_update TEXT
    )
    ''')

    conn.commit()
    conn.close()

create_database()


def load_csv_to_database(csv_file, table_name):
    conn = sqlite3.connect('my_database.db')
    df = pd.read_csv(csv_file)
    df.to_sql(table_name, conn, if_exists='replace', index=False)
    conn.close()

# تحميل ملفات CSV إلى قاعدة البيانات
load_csv_to_database('matril.csv', 'materials')

st.set_page_config(
    layout="wide",
    page_title='STG-2024',
    page_icon='🪙')

egypt_tz = pytz.timezone('Africa/Cairo')

def load_data_from_database(table_name):
    conn = sqlite3.connect('my_database.db')
    df = pd.read_sql_query(f'SELECT * FROM {table_name}', conn)
    conn.close()
    return df

df_Material = load_data_from_database('materials')


# تابع تحميل المستخدمين من قاعدة البيانات
def load_users():
    conn = sqlite3.connect('my_database.db')
    df = pd.read_sql_query('SELECT * FROM users', conn)
    conn.close()
    users = df.set_index('username').to_dict(orient='index')
    return {username: {
        'password': user['password'],
        'first_login': user['first_login'],
        'name': user['name'],
        'last_password_update': user['last_password_update']
    } for username, user in users.items()}

def save_users(users):
    conn = sqlite3.connect('my_database.db')
    c = conn.cursor()
    for username, user_data in users.items():
        c.execute('''
        INSERT OR REPLACE INTO users (username, password, first_login, name, last_password_update)
        VALUES (?, ?, ?, ?, ?)
        ''', (username, user_data['password'], user_data['first_login'], user_data['name'], user_data['last_password_update']))
    conn.commit()
    conn.close()

def save_logs(log_entries):
    conn = sqlite3.connect('my_database.db')
    c = conn.cursor()
    for entry in log_entries:
        c.execute('''
        INSERT INTO logs (user, time, item, old_quantity, new_quantity, operation)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (entry['user'], entry['time'], entry['item'], entry['old_quantity'], entry['new_quantity'], entry['operation']))
    conn.commit()
    conn.close()

def update_quantity(row_index, quantity, operation, username):
    conn = sqlite3.connect('my_database.db')
    c = conn.cursor()
    
    item_name = st.session_state.df.loc[row_index, 'Item Name']
    old_quantity = st.session_state.df.loc[row_index, 'Actual Quantity']
    
    if operation == 'add':
        new_quantity = old_quantity + quantity
    elif operation == 'subtract':
        new_quantity = old_quantity - quantity
    
    # تحديث الكمية في قاعدة البيانات
    c.execute('''
    UPDATE materials
    SET actual_quantity = ?
    WHERE item_name = ?
    ''', (new_quantity, item_name))
    
    conn.commit()
    conn.close()
    
    st.session_state.df.loc[row_index, 'Actual Quantity'] = new_quantity
    
    st.success(f"Quantity updated successfully by {username}! New Quantity: {new_quantity}")
    log_entry = {
        'user': username,
        'time': datetime.now(egypt_tz).strftime('%Y-%m-%d %H:%M:%S'),
        'item': item_name,
        'old_quantity': old_quantity,
        'new_quantity': new_quantity,
        'operation': operation
    }
    st.session_state.logs.append(log_entry)
    
    # حفظ السجلات إلى قاعدة البيانات
    save_logs(st.session_state.logs)
    
    # تحقق من الكميات وتحديث التنبيهات
    check_quantities()

def check_quantities():
    new_alerts = []
    for index, row in st.session_state.df.iterrows():
        if row['Actual Quantity'] < 100:  # تغيير القيمة حسب الحاجة
            new_alerts.append(row['Item Name'])
            
    st.session_state.alerts = new_alerts
    save_alerts(st.session_state.alerts)

# تابع للتحقق من الكميات لكل تبويب وعرض التنبيهات
def check_tab_quantities(tab_name, min_quantity):
    df_tab = st.session_state.df[st.session_state.df['Item Name'] == tab_name]
    tab_alerts = df_tab[df_tab['Actual Quantity'] < min_quantity]['Item Name'].tolist()
    return tab_alerts, df_tab

# تابع عرض التبويبات
def display_tab(tab_name, min_quantity):
    st.header(f'{tab_name}')
    row_number = st.number_input(f'Select row number for {tab_name}:', min_value=0, max_value=len(st.session_state.df)-1, step=1, key=f'{tab_name}_row_number')
    
    st.markdown(f"""
    <div style='font-size: 20px; color: blue;'>Selected Item: {st.session_state.df.loc[row_number, 'Item Name']}</div>
    <div style='font-size: 20px; color: blue;'>Current Quantity: {int(st.session_state.df.loc[row_number, 'Actual Quantity'])}</div>
    """, unsafe_allow_html=True)
    
    quantity = st.number_input(f'Enter quantity for {tab_name}:', min_value=1, step=1, key=f'{tab_name}_quantity')
    operation = st.radio(f'Choose operation for {tab_name}:', ('add', 'subtract'), key=f'{tab_name}_operation')

    if st.button('Update Quantity', key=f'{tab_name}_update_button'):
        update_quantity(row_number, quantity, operation, st.session_state.username)
    
    tab_alerts, df_tab = check_tab_quantities(tab_name, min_quantity)
    if tab_alerts:
        st.error(f"Low stock for items in {tab_name}:")
        st.dataframe(df_tab.style.applymap(lambda x: 'background-color: red' if x < min_quantity else '', subset=['Actual Quantity']))

def load_users():
    conn = sqlite3.connect('my_database.db')
    df = pd.read_sql_query('SELECT * FROM users', conn)
    conn.close()
    users = df.set_index('username').to_dict(orient='index')
    return {username: {
        'password': user['password'],
        'first_login': user['first_login'],
        'name': user['name'],
        'last_password_update': user['last_password_update']
    } for username, user in users.items()}

# دالة لتسجيل الدخول
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

# دالة لتحديث كلمة المرور
def update_password(username, new_password, confirm_new_password):
    if new_password == confirm_new_password:
        conn = sqlite3.connect('my_database.db')
        c = conn.cursor()
        c.execute('''
        UPDATE users
        SET password = ?, last_password_update = ?
        WHERE username = ?
        ''', (new_password, datetime.now(egypt_tz).strftime('%Y-%m-%d %H:%M:%S.%f%z'), username))
        conn.commit()
        conn.close()
        st.success("Password updated successfully")
    else:
        st.error("Passwords do not match")

# واجهة تسجيل الدخول
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

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
        st.markdown(f"<div style='text-align: right; font-size: 20px; color: green;'>Logged in by: {st.session_state.username}</div>", unsafe_allow_html=True)
    #else:
        #st.markdown(f"<div style='text-align: right; font-size: 20px; color: green;'>Logged in by: {users[st.session_state.username]['name']}</div>", unsafe_allow_html=True)
        
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
                
                def search_in_dataframe(df_Material, keyword, option):
                    if option == 'All Columns':
                        result = df_Material[df_Material.apply(lambda row: row.astype(str).str.contains(keyword, case=False).any(), axis=1)]
                    else:
                        result = df_Material[df_Material[option].astype(str).str.contains(keyword, case=False)]
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
                
                tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
                    'Reel Label (Small)', 'Reel Label (Large)',
                    'Ink Reels for Label', 'Red Tape', 'Adhasive Tape', 'Cartridges', 'MultiPharma Cartridge'
                ])
                
                with tab1:
                    display_tab('Reel Label (Small)', 100)
                   
                with tab2:
                    display_tab('Reel Label (Large)', 200)
                with tab3:
                    display_tab('Ink Reels for Label', 150)
                with tab4:
                    display_tab('Red Tape', 50)
                with tab5:
                    display_tab('Adhasive Tape', 75)
                with tab6:
                    display_tab('Cartridges', 80)
                with tab7:
                    display_tab('MultiPharma Cartridge', 120)
        
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
