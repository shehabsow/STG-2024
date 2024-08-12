import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# تحميل بيانات الإكسل إلى DataFrame
excel_file = 'path/to/yourfile.xlsx'

df = pd.read_csv('matril.csv')

# إنشاء أو الاتصال بقاعدة البيانات
conn = sqlite3.connect('inventory.db')
c = conn.cursor()

# إنشاء جدول البيانات الأساسي إذا لم يكن موجوداً
c.execute('''
CREATE TABLE IF NOT EXISTS inventory (
    item_name TEXT,
    Actual_Quantity INTEGER,
    monthly_consumption REAL,
    coverage_in_month REAL
)
''')

# تحميل البيانات من DataFrame إلى قاعدة البيانات
df.to_sql('inventory', conn, if_exists='replace', index=False)

# إنشاء جدول المستخدمين
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    password TEXT
)
''')

# إنشاء جدول تسجيل التغييرات
c.execute('''
CREATE TABLE IF NOT EXISTS changes (
    change_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    item_name TEXT,
    change_type TEXT,
    change_quantity INTEGER,
    change_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# حفظ التغييرات
conn.commit()

# وظيفة لإظهار الكمية الموجودة
def show_quantity(item_name):
    with sqlite3.connect('inventory.db') as conn:
        c = conn.cursor()
        c.execute('SELECT actual_quantity FROM inventory WHERE item_name=?', (item_name,))
        result = c.fetchone()
        return result[0] if result else None

# وظيفة لتحديث الكمية
def update_quantity(user_id, item_name, change_type, change_quantity):
    with sqlite3.connect('inventory.db') as conn:
        c = conn.cursor()
        current_quantity = show_quantity(item_name)
        if current_quantity is not None:
            new_quantity = current_quantity + change_quantity if change_type == 'add' else current_quantity - change_quantity
            c.execute('UPDATE inventory SET actual_quantity=? WHERE item_name=?', (new_quantity, item_name))
            c.execute('INSERT INTO changes (user_id, item_name, change_type, change_quantity) VALUES (?, ?, ?, ?)', (user_id, item_name, change_type, change_quantity))
            conn.commit()
            return new_quantity
        else:
            return None

# واجهة المستخدم باستخدام Streamlit
st.title('Inventory Management System')

# تسجيل دخول المستخدم
st.sidebar.title('User Login')
username = st.sidebar.text_input('Username')
password = st.sidebar.text_input('Password', type='password')
user_id = None

if st.sidebar.button('Login'):
    with sqlite3.connect('inventory.db') as conn:
        c = conn.cursor()
        c.execute('SELECT user_id FROM users WHERE username=? AND password=?', (username, password))
        user = c.fetchone()
        if user:
            user_id = user[0]
            st.sidebar.success('Logged in as {}'.format(username))
        else:
            st.sidebar.error('Invalid username or password')

# إضافة جزء لإدارة المستخدمين
if st.sidebar.checkbox('Manage Users'):
    st.sidebar.subheader('Add New User')
    new_username = st.sidebar.text_input('New Username')
    new_password = st.sidebar.text_input('New Password', type='password')
    if st.sidebar.button('Add User'):
        if new_username and new_password:
            with sqlite3.connect('inventory.db') as conn:
                c = conn.cursor()
                c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (new_username, new_password))
                conn.commit()
                st.sidebar.success('User added successfully')
        else:
            st.sidebar.error('Please enter both username and password')

if user_id:
    st.header('Welcome, {}'.format(username))
    
    # عرض الكمية الحالية
    item_name = st.selectbox('Select Item', df['Item Name'].unique())
  
    st.write('Current quantity of {}: {}'.format(item_name, show_quantity(item_name)))

    # تحديث الكمية
    change_type = st.selectbox('Change Type', ['add', 'subtract'])
    change_quantity = st.number_input('Change Quantity', min_value=0, step=1)
    
    if st.button('Update Quantity'):
        new_quantity = update_quantity(user_id, item_name, change_type, change_quantity if change_type == 'add' else -change_quantity)
        if new_quantity is not None:
            st.success('New quantity of {}: {}'.format(item_name, new_quantity))
        else:
            st.error('Failed to update quantity')

