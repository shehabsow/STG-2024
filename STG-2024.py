import streamlit as st
import pandas as pd
import pytz
from datetime import datetime, timedelta
import json
import sqlite3

egypt_tz = pytz.timezone('Africa/Cairo')
df_Material = pd.read_csv('matril.csv')
df_BIN = pd.read_csv('LOCATION (1).csv')
df_Receving = pd.read_csv('Receving.csv')

def load_users():
    try:
        with open('users.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        now = str(datetime.now(egypt_tz))
        return {
            "knhp322": {"password": "knhp322", "first_login": True, "name": "Shehab Ayman", "last_password_update": now},
            "karm": {"password": "karm", "first_login": True, "name": "karm", "last_password_update": now},
            "kxsv748": {"password": "kxsv748", "first_login": True, "name": "Mohamed El masry", "last_password_update": now},
            "kvwp553": {"password": "kvwp553", "first_login": True, "name": "sameh", "last_password_update": now},
            "knfb489": {"password": "knfb489", "first_login": True, "name": "Yasser Hassan", "last_password_update": now},
            "kjjd308": {"password": "kjjd308", "first_login": True, "name": "Kaleed", "last_password_update": now},
            "kibx268": {"password": "kibx268", "first_login": True, "name": "Zeinab Mobarak", "last_password_update": now},
            "engy": {"password": "1234", "first_login": True, "name": "D.Engy", "last_password_update": now}
        }

def save_users(users):
    with open('users.json', 'w') as f:
        json.dump(users, f, indent=4)

def load_logs():
    try:
        logs_location = pd.read_csv('logs_location.csv').to_dict('records')
    except FileNotFoundError:
        logs_location = []
    
    try:
        logs_receving = pd.read_csv('logs_receving.csv').to_dict('records')
    except FileNotFoundError:
        logs_receving = []

    try:
        logs_confirmation = pd.read_csv('logs_confirmation.csv').to_dict('records')
    except FileNotFoundError:
        logs_confirmation = []

    return logs_location, logs_receving, logs_confirmation

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'first_login' not in st.session_state:
    st.session_state.first_login = False
if 'password_expired' not in st.session_state:
    st.session_state.password_expired = False
if 'username' not in st.session_state:
    st.session_state.username = ''
if 'logs_location' not in st.session_state:
    st.session_state.logs_location, st.session_state.logs_receving, st.session_state.logs_confirmation = load_logs()

def login(username, password):
    users = load_users()
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

def update_password(username, new_password, confirm_new_password):
    users = load_users()
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

def calculate_packag(total_boxes):
    cartons_per_pallet = 12
    boxes_per_carton = 240

    cartons = total_boxes // boxes_per_carton
    boxes_left = total_boxes % boxes_per_carton

    pallets = cartons // cartons_per_pallet
    cartons_left = cartons % cartons_per_pallet

    return pallets, cartons_left, boxes_left

def add_new_location(Product_Name, Item_Code, Batch_Number, Quantity, Date, bins, quantities, username):
    global df_BIN

    try:
        Quantity_int = int(Quantity)
    except ValueError:
        st.error("The quantity must be a valid integer.")
        return

    pallets, cartons, boxes = calculate_packag(Quantity_int)
    new_row = {
        'Product Name': Product_Name, 'Item Code': Item_Code, 'Batch Number': Batch_Number,
       'Quantity': Quantity, 'Date': Date,'bins': bins, 'quantities': quantities,
        'Pallets': pallets, 'Cartons': cartons, 'Boxes': boxes
    }
    df_BIN = df_BIN.append(new_row, ignore_index=True)
    df_BIN.to_csv('LOCATION (1).csv', index=False)
    st.success(f"New item '{Batch_Number}' added successfully with quantity {Quantity}!")
    log_entry = {
        'user': username,
        'time': datetime.now(egypt_tz).strftime('%Y-%m-%d %H:%M:%S'),
        'Batch Number': Batch_Number,
        'Quantity': Quantity,
        'BINs': [', '.join(bins)],  # تحويل قائمة BINS إلى سلسلة نصية
        'QTYs': [', '.join(quantities)],
        'Pallets': pallets,
        'Cartons': cartons,
        'Boxes': boxes,
    }
    st.session_state.logs_location.append(log_entry)
    logs_df = pd.DataFrame(st.session_state.logs_location)
    logs_df.to_csv('logs_location.csv', index=False)

def on_quantity():
    try:
        Quantity_int = int(st.session_state['Quantity'])
        st.session_state['pallets'], st.session_state['cartons_left'], st.session_state['boxes_left'] = calculate_packag(Quantity_int)
    except ValueError:
        st.error("Please enter a valid number for QTY pack.")

def calculate_packaging(total_boxes):
    cartons_per_pallet = 12
    boxes_per_carton = 240

    cartons = total_boxes // boxes_per_carton
    boxes_left = total_boxes % boxes_per_carton

    pallets = cartons // cartons_per_pallet
    cartons_left = cartons % cartons_per_pallet

    return pallets, cartons_left, boxes_left

def add_new_Batch(username, Product_Name, Batch_No, Item_Code, QTY_pack, Date, Delivered_by, Received_by):
    global df_Receving
    try:
        QTY_pack_int = int(QTY_pack)
    except ValueError:
        st.error("The quantity must be a valid integer.")
        return

    pallets, cartons, boxes = calculate_packaging(QTY_pack_int)
    new_row = {
        'Product Name': Product_Name, 'Batch No': Batch_No, 'Item Code': Item_Code, 'QTY pack': QTY_pack,
        'Date': Date, 'Delivered by': Delivered_by, 'Received by': Received_by,
        'Pallets': pallets, 'Cartons': cartons, 'Boxes': boxes
    }
    df_Receving = df_Receving.append(new_row, ignore_index=True)
    df_Receving.to_csv('Receving.csv', index=False)
    st.success(f"New item '{Batch_No}' added successfully with quantity {QTY_pack}!")
    log_entry = {
        'user': username,
        'time': datetime.now(egypt_tz).strftime('%Y-%m-%d %H:%M:%S'),
        'Batch No': Batch_No,
        'QTY pack': QTY_pack,
        'Pallets': pallets,
        'Cartons': cartons,
        'Boxes': boxes,
        'Delivered by': Delivered_by,
        'Received by': Received_by
    }
    st.session_state.logs_receving.append(log_entry)
    logs_df = pd.DataFrame(st.session_state.logs_receving)
    logs_df.to_csv('logs_receving.csv', index=False)

def on_quantity_change():
    try:
        qty_pack = int(st.session_state['QTY_pack'])
        st.session_state['pallets'], st.session_state['cartons_left'], st.session_state['boxes_left'] = calculate_packaging(qty_pack)
    except ValueError:
        st.error("Please enter a valid number for QTY pack.")

def display_batch_details_and_confirmation():
    if 'logs_confirmation' not in st.session_state:
        st.session_state.logs_confirmation = []
    st.header("Confirmed Batches")
    confirmed_file = 'confirmed_batches.csv'
    if os.path.exists(confirmed_file):
        df_confirmed = pd.read_csv(confirmed_file)
        st.dataframe(df_confirmed.style.applymap(lambda x: 'background-color: lightgreen', subset=['Batch No']))
        
        csv_confirmed = df_confirmed.to_csv(index=False)
        st.download_button(
            label="Download Confirmed Batches",
            data=csv_confirmed,
            file_name='confirmed_batches.csv',
            mime='text/csv'
        )

    st.header("Rejected Batches")
    reject_file = 'reject_batches.csv'
    if os.path.exists(reject_file):
        df_reject = pd.read_csv(reject_file)
        st.dataframe(df_reject.style.applymap(lambda x: 'background-color: lightcoral', subset=['Batch No']))
        
        csv_reject = df_reject.to_csv(index=False)
        st.download_button(
            label="Download Rejected Batches",
            data=csv_reject,
            file_name='rejected_batches.csv',
            mime='text/csv'
        )

    if st.session_state.username == "karm":  # Replace "manager" with the actual username you want to give special access
        st.header("Confirm or Reject the Batch")

        try:
            df_Receving = pd.read_csv('Receving.csv')
        except FileNotFoundError:
            st.error("Batch file is not available.")
            return

        col1, col2, col3 = st.columns([0.5, 0.5, 1])
        with col1:
            batch_number = st.selectbox("Select a batch number", df_Receving['Batch No'].unique())
            batch_df = df_Receving[df_Receving['Batch No'] == batch_number]
            
        with col2:
            if st.button("Confirm the batch"):
                st.dataframe(batch_df.style.applymap(lambda x: 'background-color: lightgreen', subset=['Batch No']))

                if os.path.exists(confirmed_file):
                    df_confirmed = pd.read_csv(confirmed_file)
                    df_confirmed = pd.concat([df_confirmed, batch_df], ignore_index=True).drop_duplicates()
                else:
                    df_confirmed = batch_df

                df_confirmed.to_csv(confirmed_file, index=False)
                st.success(f"Batch number {batch_number} has been successfully confirmed!")
                log_entry = {
                    'user': st.session_state.username,
                    'time': datetime.now(egypt_tz).strftime('%Y-%m-%d %H:%M:%S'),
                    'Batch No': batch_number,
                    'status': 'confirmed'
                }
                st.session_state.logs_confirmation.append(log_entry)
                logs_df = pd.DataFrame(st.session_state.logs_confirmation)
                logs_df.to_csv('logs_confirmation.csv', index=False)

            if st.button("Reject the batch"):
                st.dataframe(batch_df.style.applymap(lambda x: 'background-color: lightcoral', subset=['Batch No']))

                if os.path.exists(reject_file):
                    df_reject = pd.read_csv(reject_file)
                    df_reject = pd.concat([df_reject, batch_df], ignore_index=True).drop_duplicates()
                else:
                    df_reject = batch_df

                df_reject.to_csv(reject_file, index=False)
                st.success(f"Batch number {batch_number} has been successfully rejected!")
                log_entry = {
                    'user': st.session_state.username,
                    'time': datetime.now(egypt_tz).strftime('%Y-%m-%d %H:%M:%S'),
                    'Batch No': batch_number,
                    'status': 'rejected'
                }
                st.session_state.logs_confirmation.append(log_entry)
                logs_df = pd.DataFrame(st.session_state.logs_confirmation)
                logs_df.to_csv('logs_confirmation.csv', index=False)
        with col2:
             st.button("updated")
        st.dataframe(batch_df)
users = load_users()
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.logs_location, st.session_state.logs_receving, st.session_state.logs_confirmation = load_logs()
if 'logs' not in st.session_state:
    st.session_state.logs = load_logs()[0]

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

        if 'df' not in st.session_state:
            st.session_state.df = df_Material = pd.read_csv('matril.csv')

        if 'bins' not in st.session_state:
            st.session_state.bins = []
        if 'quantities' not in st.session_state:
            st.session_state.quantities = []
        try:
            df_BIN = pd.read_csv('LOCATION (1).csv')
        except FileNotFoundError:
            df_BIN = pd.DataFrame(columns=['Product Name', 'Item Code', 'Batch Number',"bins", "quantities", 
                                            'Quantity', 'Date'])
        
        try:
            df_Receving = pd.read_csv('Receving.csv')
        except FileNotFoundError:
            df_Receving = pd.DataFrame(columns=['Product Name', "Batch No", 'Item Code', "QTY pack", "Date", "Delivered by", "Received by"])
        
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

        try:
            logs_df = pd.read_csv('logs_confirmation.csv')
            st.session_state.logs_confirmation = logs_df.to_dict('records')
        except FileNotFoundError:
            st.session_state.logs_confirmation = []
        
        
        
        # Display options
        page = st.sidebar.radio("Select page", [ "Add New Batch","FINISHED GOODS BIN LOCATION SHEET","Batch Confirmation", "Logs"])
        
        if page == 'Add New Batch':
            
            def main():
                col1, col2 = st.columns([2, 0.75])
                with col1:
                    st.markdown("""
                        <h2 style='text-align: center; font-size: 40px; color: black;'>
                            Add New Batch
                        </h2>
                    """, unsafe_allow_html=True)
                col1, col2, col3= st.columns([2, 2, 2])
                with col1:
                    Product_Name = st.selectbox('Product Name', df_Material['Material Description'].dropna().values)
                    Item_Code = df_Material[df_Material['Material Description'] == Product_Name]['Material'].values[0]
                    st.markdown(f"<div style='font-size: 20px; color: red;'>Item Code: {Item_Code}</div>", unsafe_allow_html=True)
                    QTY_pack = st.text_input('QTY pack:', key='QTY_pack', on_change=on_quantity_change)
                    st.markdown(f"<div style='font-size: 20px; color: green;'>Pallets: {st.session_state.get('pallets', '')}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='font-size: 20px; color: green;'>Cartons: {st.session_state.get('cartons_left', '')}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='font-size: 20px; color: green;'>Boxes: {st.session_state.get('boxes_left', '')}</div>", unsafe_allow_html=True)
                  
                with col2:
                    Batch_No = st.text_input('Batch No:')
                    Date = st.date_input('Date:')
                with col3:
                    Delivered_by = st.text_input('Delivered by:')
                    Received_by = st.text_input('Received by:')
            
              
                
                if st.button("Add Batch"):
                    add_new_Batch(st.session_state.username, Product_Name, Batch_No, Item_Code, QTY_pack, Date, Delivered_by, Received_by)
                    st.write('## Updated Items')
                st.dataframe(df_Receving)
                csv = df_Receving.to_csv(index=False)
                st.download_button(label="Download updated sheet", data=csv, file_name='Receving.csv', mime='text/csv')
                         
            if __name__ == '__main__':
                main()
        
        
        elif page == "FINISHED GOODS BIN LOCATION SHEET":
            def main():
                col1, col2 = st.columns([2, 0.75])
                with col1:
                    st.markdown("""
                        <h2 style='text-align: center; font-size: 40px; color: black;'>
                            FINISHED GOODS BIN LOCATION SHEET
                        </h2>
                    """, unsafe_allow_html=True)
                col1, col2,col3,col4= st.columns([1,0.5,.8,0.75])
                with col1:
                    Product_Name = st.selectbox('Product Name', df_Material['Material Description'].dropna().values)
                    Item_Code = df_Material[df_Material['Material Description'] == Product_Name]['Material'].values[0]  
                    st.markdown(f"<div style='font-size: 20px; color: red;'>Item Code: {Item_Code}</div>", unsafe_allow_html=True)
                    Quantity = st.text_input('QTY pack:', key='Quantity', on_change=on_quantity)
                    st.markdown(f"<div style='font-size: 20px; color: green;'>Pallets: {st.session_state.get('pallets', '')}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='font-size: 20px; color: green;'>Cartons: {st.session_state.get('cartons_left', '')}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='font-size: 20px; color: green;'>Boxes: {st.session_state.get('boxes_left', '')}</div>", unsafe_allow_html=True)
                with col2:
                    Batch_Number = st.text_input('Batch Number:')
                   
                    Date = st.date_input('Date:')
                    

                with col4:
                    st.session_state.df = df_BIN = pd.read_csv('LOCATION (1).csv')
                    search_keyword = st.session_state.get('search_keyword', '')
                    search_keyword = st.text_input("Enter keyword to search:", search_keyword)
                    search_button = st.button("Search")
                    search_option = 'All Columns'
                
                def search_in_dataframe(df_BIN, keyword, option):
                    if option == 'All Columns':
                        result = df_BIN[df_BIN.apply(lambda row: row.astype(str).str.contains(keyword, case=False).any(), axis=1)]
                    else:
                        result = df_BIN[df_BIN[option].astype(str).str.contains(keyword, case=False)]
                    return result
                
                if st.session_state.get('refreshed', False):
                    st.session_state.search_keyword = ''
                    st.session_state.refreshed = False
                
                if search_button and search_keyword:
                    st.session_state.search_keyword = search_keyword
                    search_results = search_in_dataframe(st.session_state.df, search_keyword, search_option)
                    st.write(f"Search results for '{search_keyword}' in {search_option}:")
                    st.dataframe(search_results, width=1000, height=200)
                    csv = search_results.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download results as CSV",
                        data=csv,
                        file_name='search_results.csv',
                        mime='text/csv'
                    )

                st.session_state.df = pd.read_csv('LOCATION (1).csv')
                available_bins = ['BIN1', 'BIN2', 'BIN3', 'BIN4', 'BIN5', 'BIN6', 'BIN7', 'BIN8', 'BIN9', 'BIN10',
                      'BIN11', 'BIN12', 'BIN13', 'BIN14', 'BIN15', 'BIN16', 'BIN17', 'BIN18', 'BIN19', 'BIN20']

                col1, col2 , col3= st.columns([1, 1,2])
                with col1:
                    bin_value = st.selectbox('Select BIN:', available_bins, key='bin')
                with col2:
                    qty_value = st.text_input('QTY:', key='qty')
                if st.button("Add BIN and QTY"):
                    if bin_value and qty_value:
                        st.session_state.bins.append(bin_value)
                        st.session_state.quantities.append(qty_value)
                        st.success(f"Added BIN: {bin_value}, QTY: {qty_value}")
            
                st.write("## Current Entries")
                for i, (bin_value, qty_value) in enumerate(zip(st.session_state.bins, st.session_state.quantities)):
                    col1, col2, col3 = st.columns([1, 1, 1])
                    with col1:
                        st.write(f"BIN: {bin_value}")
                    with col2:
                        st.write(f"QTY: {qty_value}")
                    with col3:
                        if st.button(f"Remove {i}", key=f"remove_{i}"):
                            st.session_state.bins.pop(i)
                            st.session_state.quantities.pop(i)
                            st.experimental_rerun()

                if st.button("Add Location"):
                    if not Quantity:
                        st.error("The quantity must be a valid integer.")
                    else:
                        new_data = add_new_location(Product_Name, Item_Code, Batch_Number, Quantity, Date, st.session_state.bins, st.session_state.quantities, st.session_state.username)
                        st.write('## Updated Items')
                        
                        # إضافة البيانات الجديدة إلى df_BIN
                        st.session_state.df = st.session_state.df.append(new_data, ignore_index=True)
                        st.session_state.bins = []
                        st.session_state.quantities = []
                st.button("updated")
                st.dataframe(st.session_state.df)
            
                # تحديث csv للداتا فريم المحدثة
                csv = st.session_state.df.to_csv(index=False)
                st.download_button(label="Download updated sheet", data=csv, file_name='LOCATION (1).csv', mime='text/csv')

        
            if __name__ == '__main__':
                main()


        elif page == 'Batch Confirmation':   
            def main():
                display_batch_details_and_confirmation()

        

        
            if __name__ == '__main__':
                main()



        
        elif page == "Logs":
            def clear_logs(log_type):
                if log_type == "receiving":
                    st.session_state.logs_receving = []
                    if os.path.exists('logs_receving.csv'):
                        os.remove('logs_receving.csv')
                    st.success("Receiving logs cleared successfully!")
                elif log_type == "location":
                    st.session_state.logs_location = []
                    if os.path.exists('logs_location.csv'):
                        os.remove('logs_location.csv')
                    st.success("Location logs cleared successfully!")
    
            def main():
                col1, col2 = st.columns([2, 0.75])
                with col1:
                    st.markdown("""
                        <h2 style='text-align: center; font-size: 40px; color: black;'>
                            View Logs
                        </h2>
                    """, unsafe_allow_html=True)
                
                st.subheader("Receiving Logs")
                if st.session_state.get('logs_receving', []):
                    logs_df = pd.DataFrame(st.session_state.logs_receving)
                    st.dataframe(logs_df)
                    csv = logs_df.to_csv(index=False)
                    st.download_button(label="Download Logs as CSV", data=csv, file_name='user_logs_receving.csv', mime='text/csv')
                    if st.button("Clear Receiving Logs"):
                        clear_logs("receiving")
                else:
                    st.write("No receiving logs available.")
                
                st.subheader("Location Logs")
                if st.session_state.get('logs_location', []):
                    logs_df = pd.DataFrame(st.session_state.logs_location)
                    st.dataframe(logs_df)
                    csv = logs_df.to_csv(index=False)
                    st.download_button(label="Download Logs as CSV", data=csv, file_name='location_logs.csv', mime='text/csv')
                    if st.button("Clear Location Logs"):
                        clear_logs("location")
                else:
                    st.write("No location logs available.")
                    
                st.subheader("confirmation Logs")
                if st.session_state.get('logs_confirmation', []):
                    logs_df = pd.DataFrame(st.session_state.logs_confirmation)
                    st.dataframe(logs_df)
                    csv = logs_df.to_csv(index=False)
                    st.download_button(label="Download Logs as CSV", data=csv, file_name='logs_confirmation.csv', mime='text/csv')
            
            if __name__ == '__main__':
                main()
