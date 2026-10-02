"""
Database Initializer Script
Runs schema.sql and sample_data.sql directly through Python.
"""

import os
import mysql.connector
from config import Config

def init_database():
    print("=" * 60)
    print("PetCare+ Database Setup")
    print("=" * 60)
    
    # 1. Connect to MySQL Server (without selecting database first)
    try:
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            autocommit=True
        )
        cursor = conn.cursor()
        print(f"[OK] Connected to MySQL Server at {Config.MYSQL_HOST}:{Config.MYSQL_PORT}")
    except mysql.connector.Error as err:
        print(f"[FAIL] Failed to connect to MySQL: {err}")
        print("Please check your MySQL username and password in config.py")
        return False

    # 2. Path to SQL scripts
    base_dir = os.path.dirname(os.path.abspath(__file__))
    schema_path = os.path.join(base_dir, 'database', 'schema.sql')
    sample_data_path = os.path.join(base_dir, 'database', 'sample_data.sql')

    def execute_sql_file(file_path, description):
        print(f"\n[*] Executing {description} ({os.path.basename(file_path)})...")
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split statements by semicolon while ignoring comments
        statements = []
        current_stmt = []
        for line in content.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith('--') or stripped.startswith('/*'):
                continue
            current_stmt.append(line)
            if stripped.endswith(';'):
                stmt = '\n'.join(current_stmt).strip()
                if stmt.endswith(';'):
                    stmt = stmt[:-1]
                if stmt:
                    statements.append(stmt)
                current_stmt = []

        count = 0
        for stmt in statements:
            try:
                cursor.execute(stmt)
                count += 1
            except mysql.connector.Error as err:
                print(f"[!] Warning on statement: {err}\nQuery snippet: {stmt[:100]}...")
        print(f"[OK] Successfully executed {count} statements from {os.path.basename(file_path)}.")

    try:
        execute_sql_file(schema_path, "Database Schema & Views")
        execute_sql_file(sample_data_path, "Sample Data")
        print("\n" + "=" * 60)
        print("SUCCESS: PetCare+ database initialized successfully!")
        print("Default users:")
        print("  - Admin:         username 'admin'        | password 'admin123'")
        print("  - Receptionist:  username 'receptionist' | password 'recep123'")
        print("  - Veterinarian:  username 'drsmith'      | password 'vet123'")
        print("=" * 60)
        return True
    except Exception as e:
        print(f"[✗] Error initializing database: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    init_database()
