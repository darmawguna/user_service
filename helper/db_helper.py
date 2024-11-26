"""DB Helper"""
import os
from mysql.connector.pooling import MySQLConnectionPool

# Membaca konfigurasi dari environment variables
DB_HOST = os.environ.get('DB_HOST', 'localhost').strip()
DB_NAME = os.environ.get('DB_NAME', 'db_user').strip()
DB_USER = os.environ.get('DB_USER', 'root').strip()
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'root').strip()
DB_POOLNAME = os.environ.get('DB_POOLNAME', 'user_pool').strip()
POOL_SIZE = int(os.environ.get('POOL_SIZE', '5').strip())


db_pool = MySQLConnectionPool(
    host=DB_HOST,
    user=DB_USER,
    port=3306,
    password=DB_PASSWORD,
    database=DB_NAME,
    pool_size=POOL_SIZE,  # define pool size connection
    pool_name=DB_POOLNAME
)


def get_connection():
    """
    Get connection db connection from db pool
    """
    connection = db_pool.get_connection()
    connection.autocommit = True
    return connection
