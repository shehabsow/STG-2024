import sqlite3

def create_database():
    conn = sqlite3.connect('my_database.db')  # الاتصال بقاعدة بيانات SQLite (أو إنشاؤها إذا لم تكن موجودة)
    c = conn.cursor()

    # إنشاء جدول للمواد
    c.execute('''
    CREATE TABLE IF NOT EXISTS materials (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT NOT NULL,
        actual_quantity INTEGER NOT NULL
    )
    ''')

    # إنشاء جدول للمستخدمين
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL,
        first_login BOOLEAN,
        name TEXT,
        last_password_update TEXT
    )
    ''')

    # إنشاء جدول للسجلات
    c.execute('''
    CREATE TABLE IF NOT EXISTS logs (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT NOT NULL,
        time TEXT NOT NULL,
        item TEXT NOT NULL,
        old_quantity INTEGER NOT NULL,
        new_quantity INTEGER NOT NULL,
        operation TEXT NOT NULL
    )
    ''')

    conn.commit()
    conn.close()

# تشغيل الوظيفة لإنشاء قاعدة البيانات
create_database()

def insert_sample_data():
    conn = sqlite3.connect('my_database.db')
    c = conn.cursor()

    # إدخال بيانات نموذجية للمواد
    materials = [
        ('Reel Label (Small)', 100),
        ('Reel Label (Large)', 200),
        ('Ink Reels for Label', 150),
        ('Red Tape', 50),
        ('Adhesive Tape', 75),
        ('Cartridges', 80),
        ('MultiPharma Cartridge', 120)
    ]
    c.executemany('''
    INSERT INTO materials (item_name, actual_quantity)
    VALUES (?, ?)
    ''', materials)

    # إدخال بيانات نموذجية للمستخدمين
    users = [
        ('admin', 'password123', True, 'Admin User', '2024-01-01'),
        ('user1', 'password123', True, 'User One', '2024-01-01'),
        ('user2', 'password123', False, 'User Two', '2024-01-01'),
        ('user3', 'password123', False, 'User Three', '2024-01-01'),
        ('user4', 'password123', False, 'User Four', '2024-01-01')
    ]
    c.executemany('''
    INSERT INTO users (username, password, first_login, name, last_password_update)
    VALUES (?, ?, ?, ?, ?)
    ''', users)

    conn.commit()
    conn.close()

# تشغيل الوظيفة لإدخال البيانات النموذجية
insert_sample_data()

import streamlit as st
import pandas as pd
import sqlite3

def load_data_from_database(table_name):
    conn = sqlite3.connect('my_database.db')
    df = pd.read_sql_query(f'SELECT * FROM {table_name}', conn)
    conn.close()
    return df

# تحميل المواد
df_materials = load_data_from_database('materials')
# عرض البيانات في Streamlit
st.write("Materials Data:", df_materials)

# تحميل المستخدمين
df_users = load_data_from_database('users')
# عرض البيانات في Streamlit
st.write("Users Data:", df_users)
