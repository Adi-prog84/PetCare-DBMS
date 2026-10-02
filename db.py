"""
Database connection and helper module using mysql-connector-python.
Provides parameterized execution, dictionary cursors, and transaction handling.
"""

import mysql.connector
from mysql.connector import Error
from config import Config

def get_db_connection():
    """Create and return a new MySQL database connection."""
    try:
        connection = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB,
            autocommit=False
        )
        return connection
    except Error as e:
        print(f"[DATABASE ERROR] Could not connect to MySQL: {e}")
        raise e

def query_db(query, args=(), one=False, commit=False):
    """
    Execute a parameterized SQL query safely.
    - query: SQL statement with %s placeholders
    - args: Tuple of parameters to substitute into placeholders
    - one: If True, returns a single dictionary record instead of a list
    - commit: If True, commits the transaction and returns lastrowid or affected rows
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, args)
        if commit:
            conn.commit()
            last_id = cursor.lastrowid
            affected = cursor.rowcount
            return last_id if last_id else affected
        
        result = cursor.fetchall()
        return (result[0] if result else None) if one else result
    except Error as e:
        if commit:
            conn.rollback()
        print(f"[QUERY ERROR] {e} | Query: {query} | Args: {args}")
        raise e
    finally:
        cursor.close()
        conn.close()
