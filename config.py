import os

class Config:
    """Application configuration settings."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'petcare-secret-key-college-dbms-2026')
    
    # MySQL Database Connection Settings
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'Adisjce@2028')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'petcare_db')
