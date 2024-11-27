import re
from helper.db_helper import get_connection 
def is_valid_email(email):
    """
    Fungsi untuk memvalidasi format email menggunakan regex.
    """
    email_regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
    return re.match(email_regex, email) is not None


def is_email_exists_for_update(email, user_id):
    """
    Fungsi untuk memeriksa apakah email sudah terdaftar di database
    dengan pengecualian untuk user yang sedang diupdate.
    """
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM users WHERE email = %s AND id != %s", (email, user_id))
        count = cursor.fetchone()[0]
        return count > 0  # Jika count > 0, berarti email sudah ada untuk user lain
    finally:
        cursor.close()
        connection.close()



def is_valid_phone_number(phone_number):
    """
    Fungsi untuk memvalidasi panjang nomor telepon.
    Nomor telepon harus antara 10 hingga 15 karakter.
    """
    return len(phone_number) >= 10 and len(phone_number) <= 15


def is_email_exists(email):
    """
    Fungsi untuk memeriksa apakah email sudah terdaftar di database.
    """
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM users WHERE email = %s", (email,))
        count = cursor.fetchone()[0]
        return count > 0  # Jika count > 0, berarti email sudah ada
    finally:
        cursor.close()
        connection.close()


