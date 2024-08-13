import streamlit as st
import pandas as pd
import pytz
import sqlite3
from datetime import datetime, timedelta
import json
import os

st.set_page_config(
    layout="wide",
    page_title='STG-2024',
    page_icon='🪙')

egypt_tz = pytz.timezone('Africa/Cairo')

# Create a connection to the SQLite database
conn = sqlite3.connect('materials.db')
c = conn.cursor()

# Create tables if they don't exist
c.execute('''
CREATE TABLE IF NOT EXISTS materials (
    id INTEGER PRIMARY KEY,
    item_name TEXT,
    actual_quantity INTEGER
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
    id INTEGER PRIMARY KEY,
    user TEXT,
    time TEXT,
    item TEXT,
    old_quantity INTEGER,
    new_quantity INTEGER,
    operation TEXT
)
''')

conn.commit()

# Load users data
def load_users():
    c.execute("SELECT * FROM users")
    users = c.fetchall()
    if not users:
        users = {
            "knhp322": {"password": "knhp322", "first_login": True, "name": "Shehab Ayman", "last_password_update": str(datetime.now(egypt_tz))},
            "KFXW551": {"password": "KFXW551", "first_login": True, "name": " Hossameldin Mostafa", "last_password_update": str(datetime.now(egypt_tz))},
            "knvp968": {"password": "knvp968", "first_login": True, "name": "  Mohamed Nader", "last_password_update": str(datetime.now(egypt_tz))},
            "kcqw615": {"password": "kcqw615", "first_login": True, "name": "Tareek Mahmoud ", "last_password_update": str(datetime.now(egypt_tz))}
        }
        for username, data in users.items():
            c.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)",
                      (username, data['password'], data['first_login'], data['name'], data['last_password_update']))
        conn.commit()
    else:
        users = {user[0]: {"password": user[1], "first_login": user[2], "name": user[3], "last_password_update": user[4]} for user in users}
    return users

# Save users data to database
def save_users(users):
    for username, data in users.items():
        c.execute("UPDATE users SET password = ?, first_login = ?, last_password_update = ? WHERE username = ?",
                  (data['password'], data['first_login'], data['last_password_update'], username))
    conn.commit()

# Load logs from database
def load_logs():
    c.execute("SELECT * FROM logs")
    logs = c.fetchall()
    return logs

# Save logs to database
def save_logs(logs):
    c.executemany("INSERT INTO logs (user, time, item, old_quantity, new_quantity, operation) VALUES (?, ?, ?, ?, ?, ?)", logs)
    conn.commit()

# Login function
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

# Update password function
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

# Update quantity function
def update_quantity(row_index, quantity, operation, username):
    c.execute("SELECT actual_quantity FROM materials WHERE id = ?", (row_index,))
    last_month = c.fetchone()[0]
    if operation == 'add':
        new_quantity = last_month + quantity
    elif operation == 'subtract':
        new_quantity = last_month - quantity
    c.execute("UPDATE materials SET actual_quantity = ? WHERE id = ?", (new_quantity, row_index))
    conn.commit()
    st.success(f"Quantity updated successfully by {username}! New Quantity: {new_quantity}")
    log_entry = (username, datetime.now(egypt_tz).strftime('%Y-%m-%d %H:%M:%S'), row_index, last_month, new_quantity, operation)
    c.execute("INSERT INTO logs (user, time, item, old_quantity, new_quantity, operation) VALUES (?, ?, ?, ?, ?, ?)", log_entry)
    conn.commit()
    check_quantities()

# Check quantities and update alerts
def check_quantities():
    c.execute("SELECT item_name FROM materials WHERE actual_quantity < 100")
    new_alerts = c.fetchall()
    st.session_state.alerts = [alert[0] for alert in new_alerts]

# Check quantities for specific tab
def check_tab_quantities(tab_name, min_quantity):
    c.execute("SELECT * FROM materials WHERE item_name = ?", (tab_name,))
    df_tab = c.fetchall()
    tab_alerts = [item for item in df_tab if item[2] < min_quantity]
    return tab_alerts, df_tab

# Display tab
def display_tab(tab_name, min_quantity):
    st.header(f'{tab_name}')
    row_number = st.number_input(f'Select row number for {tab_name}:', min_value=0, max_value=len(st.session_state.df)-1, step=1, key=f'{tab_name}_row_number')
    
    c.execute("SELECT item_name, actual_quantity FROM materials WHERE id = ?", (row_number,))
    item, quantity = c.fetchone()
    
    st.markdown(f"""
    <div style='font-size: 20px; color: blue;'>Selected Item: {item}</div>
    <div style='font-size: 20px; color: blue;'>Current Quantity: {quantity}</div>
    """, unsafe_allow_html=True)
    
    quantity = st.number_input(f'Enter quantity for {tab_name}:', min_value=1, step=1, key=f'{tab_name}_quantity')
    operation = st.radio(f'Choose operation for {tab_name}:', ('add', 'subtract'), key=f'{tab_name}_operation')

    if st.button('Update Quantity', key=f'{tab_name}_update_button'):
        update_quantity(row_number, quantity, operation, st.session_state.username)
    
    tab_alerts, df_tab = check_tab_quantities(tab_name, min_quantity)
    if tab_alerts:
        st.error(f"Low stock for items in {tab_name}:")
        st.dataframe(pd.DataFrame(df_tab, columns=['ID', 'Item Name', 'Actual Quantity']).style.applymap(lambda x: 'background-color: red' if x < min_quantity else '', subset=['Actual Quantity']))

# Clear logs
def clear_logs():
    c.execute("DELETE FROM logs")
    conn.commit()
    st.success("Logs cleared successfully!")

# Load users and logs
users = load_users()
st.session_state.logs = load_logs()

# Login interface
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        st.button("Login")
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
        st.markdown(f"<div style='text-align: right; font-size: 20px; color: green;'>Logged in by: {users[st.session_state.username]['name']}</div>", unsafe_allow_html=True)
        
        # Load data into session state
        if 'df' not in st.session_state:
            c.execute("SELECT * FROM materials")
            data = c.fetchall()
            st.session_state.df = pd.DataFrame(data, columns=['ID', 'Item Name', 'Actual Quantity'])
                
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
                
                tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
                    'Reel Label (Small)', 'Reel Label (Large)',
                    'Ink Reels for Label', 'Red Tape', 'Adhasive Tape', 'Cartridges', 'MultiPharma Cartridge'
                ])
                
                with tab1:
                    Small = st.session_state.df[st.session_state.df['Item Name'] == 'Reel Label (Small)'].sort_values(by='Item Name')
                    st.dataframe(Small,width=2000)
                    col4, col5, col6 = st.columns([2,1,2])
                    with col4:
                        display_tab('Reel Label (Small)', 20)
                   
                with tab2:
                    Large = st.session_state.df[st.session_state.df['Item Name'] == 'Reel Label (Large)'].sort_values(by='Item Name')
                    st.dataframe(Large,width=2000)
                    col4, col5, col6 = st.columns([2,1,2])
                    with col4:
                        display_tab('Reel Label (Large)', 60)
                with tab3:
                    Ink = st.session_state.df[st.session_state.df['Item Name'] == 'Ink Reels for Label'].sort_values(by='Item Name')
                    st.dataframe(Ink,width=2000)
                    col4, col5, col6 = st.columns([2,1,2])
                    with col4:
                        display_tab('Ink Reels for Label', 20)
                with tab4:
                    Tape = st.session_state.df[st.session_state.df['Item Name'] == 'Red Tape'].sort_values(by='Item Name')
                    st.dataframe(Tape,width=2000)
                    col4, col5, col6 = st.columns([2,1,2])
                    with col4:
                        display_tab('Red Tape', 5)
                with tab5:
                    Adhasive = st.session_state.df[st.session_state.df['Item Name'] == 'Adhasive Tape'].sort_values(by='Item Name')
                    st.dataframe(Adhasive,width=2000)
                    col4, col5, col6 = st.columns([2,2,2])
                    with col4:
                        display_tab('Adhasive Tape', 100)
                with tab6:
                    Cartridges = st.session_state.df[st.session_state.df['Item Name'] == 'Cartridges'].sort_values(by='Item Name')
                    st.dataframe(Cartridges,width=2000)
                    col4, col5, col6 = st.columns([2,1,2])
                    with col4:
                        display_tab('Cartridges', 50)
                with tab7:
                    MultiPharma = st.session_state.df[st.session_state.df['Item Name'] == 'MultiPharma Cartridge'].sort_values(by='Item Name')
                    st.dataframe(MultiPharma,width=2000)
                    col4, col5, col6 = st.columns([2,1,2])
                    with col4:
                        display_tab('MultiPharma Cartridge', 5)

                st.button("updated page")
                csv = st.session_state.df.to_csv(index=False)
                st.download_button(label="Download updated sheet", data=csv, file_name='updated.csv', mime='text/csv')
        
                
        
            if __name__ == '__main__':
                main()
        elif page == 'View Logs':
            st.header('User Activity Logs')
            if st.session_state.logs:
                logs_df = pd.DataFrame(st.session_state.logs, columns=['ID', 'User', 'Time', 'Item', 'Old Quantity', 'New Quantity', 'Operation'])
                st.dataframe(logs_df, width=1000, height=400)
                csv = logs_df.to_csv(index=False)
                st.download_button(label="Download Logs as CSV", data=csv, file_name='user_logs.csv', mime='text/csv')
                if st.button("Clear Logs"):
                    clear_logs()
            
            else:
                st.write("No logs available.")
