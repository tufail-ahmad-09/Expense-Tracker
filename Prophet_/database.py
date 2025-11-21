"""
Database models and operations for user management
Using SQLite with proper password hashing
"""

import sqlite3
import bcrypt
from typing import Optional, Dict
from datetime import datetime
import os

# Database file path
DB_PATH = os.path.join(os.path.dirname(__file__), 'expense_tracker.db')

def get_db_connection():
    """Create and return a database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn

def init_database():
    """Initialize the database with required tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create budgets table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            period TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Create expenses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_budgets_user ON budgets(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_expenses_user ON expenses(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(date)')
    
    conn.commit()
    conn.close()
    print(f"✅ Database initialized at: {DB_PATH}")

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
    return password_hash.decode('utf-8')

def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

def create_user(name: str, email: str, password: str, phone: Optional[str] = None) -> Dict:
    """
    Create a new user in the database
    Returns user data if successful, raises exception if email exists
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if user already exists
        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        if cursor.fetchone():
            raise ValueError("Email already exists")
        
        # Hash the password
        password_hash = hash_password(password)
        
        # Insert new user
        cursor.execute('''
            INSERT INTO users (name, email, password_hash, phone)
            VALUES (?, ?, ?, ?)
        ''', (name, email, password_hash, phone))
        
        user_id = cursor.lastrowid
        conn.commit()
        
        # Return user data (without password hash)
        return {
            'id': str(user_id),
            'name': name,
            'email': email,
            'phone': phone
        }
    
    finally:
        conn.close()

def authenticate_user(email: str, password: str) -> Optional[Dict]:
    """
    Authenticate a user by email and password
    Returns user data if successful, None if authentication fails
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get user by email
        cursor.execute('''
            SELECT id, name, email, password_hash, phone 
            FROM users 
            WHERE email = ?
        ''', (email,))
        
        user = cursor.fetchone()
        
        if not user:
            return None
        
        # Verify password
        if not verify_password(password, user['password_hash']):
            return None
        
        # Return user data (without password hash)
        return {
            'id': str(user['id']),
            'name': user['name'],
            'email': user['email'],
            'phone': user['phone']
        }
    
    finally:
        conn.close()

def get_user_by_id(user_id: int) -> Optional[Dict]:
    """Get user by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, name, email, phone, created_at
            FROM users 
            WHERE id = ?
        ''', (user_id,))
        
        user = cursor.fetchone()
        
        if not user:
            return None
        
        return {
            'id': str(user['id']),
            'name': user['name'],
            'email': user['email'],
            'phone': user['phone'],
            'created_at': user['created_at']
        }
    
    finally:
        conn.close()

def get_user_by_email(email: str) -> Optional[Dict]:
    """Get user by email"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, name, email, phone, created_at
            FROM users 
            WHERE email = ?
        ''', (email,))
        
        user = cursor.fetchone()
        
        if not user:
            return None
        
        return {
            'id': str(user['id']),
            'name': user['name'],
            'email': user['email'],
            'phone': user['phone'],
            'created_at': user['created_at']
        }
    
    finally:
        conn.close()

# Budget functions
def create_budget(user_id: int, amount: float, period: str) -> Dict:
    """Create or update user budget"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO budgets (user_id, amount, period)
            VALUES (?, ?, ?)
        ''', (user_id, amount, period))
        
        budget_id = cursor.lastrowid
        conn.commit()
        
        return {
            'id': budget_id,
            'user_id': user_id,
            'amount': amount,
            'period': period
        }
    finally:
        conn.close()

def get_user_budget(user_id: int, period: str) -> Optional[Dict]:
    """Get user's budget for a specific period"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, user_id, amount, period, created_at
            FROM budgets 
            WHERE user_id = ? AND period = ?
            ORDER BY created_at DESC
            LIMIT 1
        ''', (user_id, period))
        
        budget = cursor.fetchone()
        if not budget:
            return None
        
        return {
            'id': budget['id'],
            'user_id': budget['user_id'],
            'amount': budget['amount'],
            'period': budget['period'],
            'created_at': budget['created_at']
        }
    finally:
        conn.close()

# Expense functions
def create_expense(user_id: int, category: str, amount: float, description: str, date: str) -> Dict:
    """Create a new expense"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO expenses (user_id, category, amount, description, date)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, category, amount, description, date))
        
        expense_id = cursor.lastrowid
        conn.commit()
        
        return {
            'id': expense_id,
            'user_id': user_id,
            'category': category,
            'amount': amount,
            'description': description,
            'date': date
        }
    finally:
        conn.close()

def get_user_expenses(user_id: int, start_date: Optional[str] = None, end_date: Optional[str] = None):
    """Get user's expenses, optionally filtered by date range"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if start_date and end_date:
            cursor.execute('''
                SELECT id, user_id, category, amount, description, date, created_at
                FROM expenses 
                WHERE user_id = ? AND date BETWEEN ? AND ?
                ORDER BY date DESC
            ''', (user_id, start_date, end_date))
        else:
            cursor.execute('''
                SELECT id, user_id, category, amount, description, date, created_at
                FROM expenses 
                WHERE user_id = ?
                ORDER BY date DESC
            ''', (user_id,))
        
        expenses = cursor.fetchall()
        
        return [{
            'id': exp['id'],
            'user_id': exp['user_id'],
            'category': exp['category'],
            'amount': exp['amount'],
            'description': exp['description'],
            'date': exp['date'],
            'created_at': exp['created_at']
        } for exp in expenses]
    finally:
        conn.close()

def get_expense_stats(user_id: int) -> Dict:
    """Get expense statistics for a user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Today's spending
        cursor.execute('''
            SELECT COALESCE(SUM(amount), 0) as total
            FROM expenses
            WHERE user_id = ? AND date = DATE('now')
        ''', (user_id,))
        today = cursor.fetchone()['total']
        
        # This week's spending
        cursor.execute('''
            SELECT COALESCE(SUM(amount), 0) as total
            FROM expenses
            WHERE user_id = ? AND date >= DATE('now', '-7 days')
        ''', (user_id,))
        week = cursor.fetchone()['total']
        
        # This month's spending
        cursor.execute('''
            SELECT COALESCE(SUM(amount), 0) as total
            FROM expenses
            WHERE user_id = ? AND date >= DATE('now', 'start of month')
        ''', (user_id,))
        month = cursor.fetchone()['total']
        
        # Largest purchase
        cursor.execute('''
            SELECT COALESCE(MAX(amount), 0) as max
            FROM expenses
            WHERE user_id = ?
        ''', (user_id,))
        largest = cursor.fetchone()['max']
        
        # Category-wise spending
        cursor.execute('''
            SELECT category, SUM(amount) as total
            FROM expenses
            WHERE user_id = ?
            GROUP BY category
        ''', (user_id,))
        by_category = {row['category']: row['total'] for row in cursor.fetchall()}
        
        return {
            'today': today,
            'week': week,
            'month': month,
            'largest': largest,
            'by_category': by_category
        }
    finally:
        conn.close()

# Initialize database when module is imported
init_database()
