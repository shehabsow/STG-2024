import streamlit as st
import pandas as pd
import pytz
from datetime import datetime, timedelta
import json
import csv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
st.set_page_config(
    layout="wide",
    page_title='Earthquake analysis',
    page_icon='🪙')




egypt_tz = pytz.timezone('Africa/Cairo')
df_Material = pd.read_csv('matril.csv')
#df_BIN = pd.read_csv('LOCATION.csv')
#df_Receving = pd.read_csv('Receving.csv')

# Load users data
def load_users():
    try:
        with open('users.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "knhp322": {"password": "knhp322", "first_login": True, "name": "Shehab Ayman", "last_password_update": str(datetime.now(egypt_tz))},
            "karm": {"password": "karm", "first_login": True, "name": "karm", "last_password_update": str(datetime.now(egypt_tz))},
            "kxsv748": {"password": "kxsv748", "first_login": True, "name": "Mohamed El masry", "last_password_update": str(datetime.now(egypt_tz))},
            "kvwp553": {"password": "kvwp553", "first_login": True, "name": "sameh", "last_password_update": str(datetime.now(egypt_tz))},
            "knfb489": {"password": "knfb489", "first_login": True, "name": "Yasser Hassan", "last_password_update": str(datetime.now(egypt_tz))},
            "kjjd308": {"password": "kjjd308", "first_login": True, "name": "Kaleed", "last_password_update": str(datetime.now(egypt_tz))},
            "kibx268": {"password": "kibx268", "first_login": True, "name": "Zeinab Mobarak", "last_password_update": str(datetime.now(egypt_tz))},
            "engy": {"password": "1234", "first_login": True, "name": "D.Engy", "last_password_update": str(datetime.now(egypt_tz))}
        }

# Save users data to JSON file
def save_users(users):
    with open('users.json', 'w') as f:
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
def add_new_LOCATION(row_index, Product_Name, Item_Code, Batch_Number, Warehouse_Operator, Quantity, Date, BIN1, QTY1, BIN2, QTY2, BIN3, QTY3, username):
    global df_BIN
    new_row = {
        'Product Name': Product_Name, 'Item Code': Item_Code, 'Batch Number': Batch_Number,
        "Warehouse Operator": Warehouse_Operator, 'Quantity': Quantity, 'Date': Date,
        'BIN1': BIN1, 'QTY1': QTY1, 'BIN2': BIN2, 'QTY2': QTY2, 'BIN3': BIN3, 'QTY3': QTY3
    }
    df_BIN = df_BIN.append(new_row, ignore_index=True)
    df_BIN.to_csv('LOCATION.csv', index=False)
    st.success(f"New item '{Batch_Number}' added successfully with quantity {Quantity}!")
    log_entry = {
        'user': username,
        'time': datetime.now(egypt_tz).strftime('%Y-%m-%d %H:%M:%S'),
        'Batch Number': Batch_Number,
        'Quantity': Quantity,
        'BIN1': BIN1,
        'QTY1': QTY1,
        'BIN2': BIN2,
        'QTY2': QTY2,
        'BIN3': BIN3,
        'QTY3': QTY3
    }
    st.session_state.logs_location.append(log_entry)
    logs_df = pd.DataFrame(st.session_state.logs_location)
    logs_df.to_csv('logs_location.csv', index=False)

# Function to add new batch
def add_new_Batch(username, Product_Name, Batch_No, QTY_pack, Date, Delivered_by, Received_by, Remark):
    global df_Receving
    new_row = {
        'Product Name': Product_Name, 'Batch No': Batch_No, 'QTY pack': QTY_pack,
        'Date': Date, 'Delivered by': Delivered_by, 'Received by': Received_by, 'Remark': Remark
    }
    df_Receving = df_Receving.append(new_row, ignore_index=True)
    df_Receving.to_csv('Receving.csv', index=False)
    st.success(f"New item '{Batch_No}' added successfully with quantity {QTY_pack}!")
    log_entry = {
        'user': username,
        'time': datetime.now(egypt_tz).strftime('%Y-%m-%d %H:%M:%S'),
        'Batch No': Batch_No,
        'QTY pack': QTY_pack,
        'Delivered by': Delivered_by,
        'Received by': Received_by,
        'Remark': Remark
    }
    st.session_state.logs_receving.append(log_entry)
    logs_df = pd.DataFrame(st.session_state.logs_receving)
    logs_df.to_csv('logs_receving.csv', index=False)


users = load_users()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.logs_location, st.session_state.logs_receving = load_logs()

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
            if st.button("Update Password"):
                if not new_password or not confirm_new_password:
                    st.error("Please fill in all the fields.")
                else:
                    update_password(st.session_state.username, new_password, confirm_new_password)
    else:
        st.markdown(f"<div style='text-align: right; font-size: 20px; color: green;'> Login by : {users[st.session_state.username]['name']}</div>", unsafe_allow_html=True)

        # Load data frames
        if 'df' not in st.session_state:
            st.session_state.df = df_Material = pd.read_csv('matril.csv')
        try:
            df_BIN = pd.read_csv('LOCATION.csv')
        except FileNotFoundError:
            df_BIN = pd.DataFrame(columns=['Product Name', 'Item Code', 'Batch Number', "Warehouse Operator",
                                        'Quantity', 'Date', 'BIN1', 'QTY1', 'BIN2', 'QTY2', 'BIN3', 'QTY3'])
        
        try:
            df_Receving = pd.read_csv('Receving.csv')
        except FileNotFoundError:
            df_Receving = pd.DataFrame(columns=['Product Name', "Batch No", "QTY pack", "Date", "Delivered by", "Received by", "Remark"])
        
        try:
            logs_df = pd.read_csv('logs_location.csv')
            st.session_state.logs_location = logs_df.to_dict('records')
        except FileNotFoundError:
            st.session_state.logs_location = []
        
        try:
            logs_df = pd.read_csv('logs_receving.csv')
            st.session_state.logs_receving = logs_df.to_dict('records')
        except FileNotFoundError:
            st.session_state.logs_receving = []
        
        # Display options
        page = st.sidebar.radio("Select page", [ "Add New Batch","Add New Location", "Logs"])
        
        if page == 'Add New Batch':
            def main():
                st.dataframe(df_Material) 
                col1, col2 = st.columns([2, 0.75])
                with col1:
                    st.markdown("""
                        <h2 style='text-align: center; font-size: 40px; color: black;'>
                            Add New Batch
                        </h2>
                    """, unsafe_allow_html=True)
                col1, col2, col3, col4, col5, col6 = st.columns([3, 2, 1.5, 1.5, 1.5, 1.5])
                with col1:
                    Product_Name = st.selectbox('Product Name', df_Material['Item Name'].dropna().values)
                    Warehouse_Operator = st.text_input('Warehouse Operator:')
                with col2:
                    Batch_No = st.text_input('Batch No:')
                    Date = st.date_input('Date:')
                with col3:
                    QTY_pack = st.text_input('QTY pack:')
                with col4:
                    Delivered_by = st.text_input('Delivered by:')
                with col5:
                    Received_by = st.text_input('Received by:')
                with col6:
                    Remark = st.text_input('Remark:')
        
                if st.button("Add Batch"):
                    add_new_Batch(st.session_state.username, Product_Name, Batch_No, QTY_pack, Date, Delivered_by, Received_by, Remark)
                    st.write('## Updated Items')
                    st.dataframe(df_Receving)
                csv = df_Receving.to_csv(index=False)
                st.download_button(label="Download updated sheet", data=csv, file_name='updated_spare_parts.csv', mime='text/csv')
            
        
            if __name__ == '__main__':
                main()
        
        
        elif page == "Add New Location":
            def main():
                col1, col2 = st.columns([2, 0.75])
                with col1:
                    st.markdown("""
                        <h2 style='text-align: center; font-size: 40px; color: black;'>
                            Add New Location
                        </h2>
                    """, unsafe_allow_html=True)
                col1, col2, col3, col4, col5 = st.columns([2.5, 1.5, 1.5, 1.5, 1.5])
                with col1:
                    Product_Name = st.selectbox('Product Name', df_Material['Item Name'].dropna().values)
                    Item_Code = st.text_input('Item Code:')
                    Warehouse_Operator = st.text_input('Warehouse Operator:')
                with col2:
                    Batch_Number = st.text_input('Batch Number:')
                    Quantity = st.text_input('Quantity:')
                    Date = st.date_input('Date:')
                with col3:
                    BIN1 = st.text_input('BIN1:')
                    QTY1 = st.number_input('QTY1:',min_value=0)
                with col4:
                    BIN2 = st.text_input('BIN2:')
                    QTY2 = st.number_input('QTY2:',min_value=0)
                with col5:
                    BIN3 = st.text_input('BIN3:')
                    QTY3 = st.number_input('QTY3:',min_value=0)
                if st.button("Add Location"):
                    row_index = len(df_BIN)
                    add_new_LOCATION(row_index, Product_Name, Item_Code, Batch_Number, Warehouse_Operator, Quantity, Date, BIN1, QTY1, BIN2, QTY2, BIN3, QTY3, st.session_state.username)
                    st.write('## Updated Items')
                    st.dataframe(df_BIN)
                csv = df_BIN.to_csv(index=False)
                st.download_button(label="Download updated sheet", data=csv, file_name='updated_spare_parts.csv', mime='text/csv')
            
        
            if __name__ == '__main__':
                main()
        
        elif page == "Logs":
            def main():
                
                col1, col2 = st.columns([2, 0.75])
                with col1:
                    st.markdown("""
                        <h2 style='text-align: center; font-size: 40px; color: black;'>
                            View Logs
                        </h2>
                    """, unsafe_allow_html=True)
                st.subheader("receving Logs")
                if st.session_state.logs_receving:
                    logs_df = pd.DataFrame(st.session_state.logs_receving)
                    st.dataframe(logs_df)
                    csv = logs_df.to_csv(index=False)
                    st.download_button(label="Download Logs as sheet", data=csv, file_name='user_logs_receving.csv', mime='text/csv')
                else:
                    st.write("No receving logs available.")
        
                st.subheader("Location Logs")
                if st.session_state.logs_location:
                    logs_df = pd.DataFrame(st.session_state.logs_location)
                    st.dataframe(logs_df)
                    csv = logs_df.to_csv(index=False)
                    st.download_button(label="Download Logs as CSV", data=csv, file_name='location_logs.csv', mime='text/csv')
                else:
                    st.write("No location logs available.")
            if __name__ == '__main__':
                main()
