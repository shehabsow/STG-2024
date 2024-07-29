import streamlit as st
import pandas as pd
import pytz
from datetime import datetime, timedelta
import json
import csv
import os

st.set_page_config(
    layout="wide",
    page_title='STG-2024',
    page_icon='🪙')




egypt_tz = pytz.timezone('Africa/Cairo')
df_Material = pd.read_csv('matril.csv')
#df_BIN = pd.read_csv('LOCATION.csv')
#df_Receving = pd.read_csv('Receving.csv')

# Load users data
def load_users():
    try:
        with open('users1.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "knhp322": {"password": "knhp322", "first_login": True, "name": "Shehab Ayman", "last_password_update": str(datetime.now(egypt_tz))},
            "KFXW551": {"password": "KFXW551", "first_login": True, "name": " Hossameldin Mostafa", "last_password_update": str(datetime.now(egypt_tz))}}

# Save users data to JSON file
def save_users(users):
    with open('users1.json', 'w') as f:
        json.dump(users, f)

# Load logs from files
def load_logs():
    try:
        logs_location = pd.read_csv('logs_location.csv').to_dict('records')
    except FileNotFoundError:
        logs_location = []
    
    try:
        logs_receving = pd.read_csv('logs_receving.csv').to_dict('records')
    except FileNotFoundError:
        logs_receving = []

    return logs_location, logs_receving

def save_alerts(alerts):
    with open('alerts.json', 'w') as f:
        json.dump(alerts, f)

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

# Function to add new location
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
        
# دالة لتحديث الكمية
def update_quantity(row_index, quantity, operation, username):
    old_quantity = st.session_state.df.loc[row_index, 'Actual Quantity']
    if operation == 'add':
        st.session_state.df.loc[row_index, 'Actual Quantity'] += quantity
    elif operation == 'subtract':
        st.session_state.df.loc[row_index, 'Actual Quantity'] -= quantity
    new_quantity = st.session_state.df.loc[row_index, 'Actual Quantity']
    st.session_state.df.to_csv('matril.csv', index=False)
    st.success(f"Quantity updated successfully by {username}! New Quantity: {int(st.session_state.df.loc[row_index, 'Actual Quantity'])}")
    log_entry = {
        'user': username,
        'time': datetime.now(egypt_tz).strftime('%Y-%m-%d %H:%M:%S'),
        'item': st.session_state.df.loc[row_index, 'Item Name'],
        'old_quantity': old_quantity,
        'new_quantity': new_quantity,
        'operation': operation
    }
    st.session_state.logs.append(log_entry)
    
    # حفظ السجلات إلى ملف CSV
    logs_df = pd.DataFrame(st.session_state.logs)
    logs_df.to_csv('logs.csv', index=False)
    
    # تحقق من الكميات وتحديث التنبيهات
    check_quantities()

def check_quantities():
    new_alerts = []
    for index, row in st.session_state.df.iterrows():
        if row['Actual Quantity'] < 100:  # تغيير القيمة حسب الحاجة
            new_alerts.append(row['Item Name'])
    
    st.session_state.alerts = new_alerts
    save_alerts(st.session_state.alerts)

# دالة للتحقق من الكميات لكل تبويب وعرض التنبيهات
def check_tab_quantities(tab_name, min_quantity):
    
    df_tab = st.session_state.df[st.session_state.df['Item Name'] == tab_name]
    tab_alerts = df_tab[df_tab['Actual Quantity'] < min_quantity]['Item Name'].tolist()
    return tab_alerts, df_tab

# عرض التبويبات
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
        st.write(f"Items in {tab_name} with low stock:")
        st.dataframe(
            df_tab.style.applymap(lambda x: 'background-color: red' if x < min_quantity else '', subset=['Actual Quantity'])
        )
users = load_users()

# واجهة تسجيل الدخول
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.logs = []
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([5, 5,5])
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
        
        # قراءة البيانات
           
        if 'df' not in st.session_state:
            st.session_state.df = pd.read_csv('matril.csv')
        try:
            logs_df = pd.read_csv('logs.csv')
            st.session_state.logs = logs_df.to_dict('records')
        except FileNotFoundError:
            st.session_state.logs = []
        st.markdown("""
                <style>
                    .main {
                        padding: 0rem 1rem;
                        width: 200%;
                    }
                    .stApp {
                        overflow: hidden;
                    }
                </style>
                """, unsafe_allow_html=True)
        
                 
        page = st. sidebar.radio('Select page', ['STG-2024', 'View Logs'])
        
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
                
                def search_in_dataframe(df_f, keyword, option):
                    if option == 'All Columns':
                        result = df_f[df_f.apply(lambda row: row.astype(str).str.contains(keyword, case=False).any(), axis=1)]
                    else:
                        result = df_f[df_f[option].astype(str).str.contains(keyword, case=False)]
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
                    peraing = df_Material[df_Material['Item Name'] == 'Reel Label (Small)'].sort_values(by='Item Name')
                    st.dataframe(peraing,width=2000)
                    col4, col5, col6 = st.columns([2,1,2])
                    with col4:
                        display_tab('Reel Label (Small)', 100)
                   
                with tab2:
                    peraing = df_Material[df_Material['Item Name'] == 'Reel Label (Large)'].sort_values(by='Item Name')
                    st.dataframe(peraing,width=2000)
                    col4, col5, col6 = st.columns([2,1,2])
                    with col4:
                        display_tab('Reel Label (Large)', 200)
                with tab3:
                    peraing = df_Material[df_Material['Item Name'] == 'Ink Reels for Label'].sort_values(by='Item Name')
                    st.dataframe(peraing,width=2000)
                    col4, col5, col6 = st.columns([2,1,2])
                    with col4:
                        display_tab('Ink Reels for Label', 150)
                with tab4:
                    peraing = df_Material[df_Material['Item Name'] == 'Red Tape'].sort_values(by='Item Name')
                    st.dataframe(peraing,width=2000)
                    col4, col5, col6 = st.columns([2,1,2])
                    with col4:
                        display_tab('Red Tape', 50)
                with tab5:
                    peraing = df_Material[df_Material['Item Name'] == 'Adhasive Tape'].sort_values(by='Item Name')
                    st.dataframe(peraing,width=2000)
                    col4, col5, col6 = st.columns([2,2,2])
                    with col4:
                        display_tab('Adhasive Tape', 75)
                with tab6:
                    peraing = df_Material[df_Material['Item Name'] == 'Cartridges'].sort_values(by='Item Name')
                    st.dataframe(peraing,width=2000)
                    col4, col5, col6 = st.columns([2,1,2])
                    with col4:
                        display_tab('Cartridges', 80)
                with tab7:
                    peraing = df_Material[df_Material['Item Name'] == 'MultiPharma Cartridge'].sort_values(by='Item Name')
                    st.dataframe(peraing,width=2000)
                    col4, col5, col6 = st.columns([2,1,2])
                    with col4:
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
      
