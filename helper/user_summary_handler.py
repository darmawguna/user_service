from helper.db_helper import get_connection

import json
from datetime import datetime

def save_redis_data_to_db(latest_message):
    """Fungsi untuk menyimpan data dari Redis ke database tanpa mengembalikan apapun."""
    try:
       

        if latest_message:
            # Decode untuk mendapatkan string, lalu parsing JSON
            message_data = json.loads(latest_message.decode('utf-8'))

            # Ambil dan validasi data
            try:
                user_id = int(message_data.get("user_id"))
                total_amount = float(message_data.get("total_amount"))
                amount_transaction = int(message_data.get("amount_transaction"))
                last_date_transaction = datetime.strptime(
                    message_data.get("last_date_transaction"), "%Y-%m-%d %H:%M:%S"
                )
            except (ValueError, TypeError, KeyError) as e:
                # Jika ada kesalahan pada data, tidak mengembalikan apapun, hanya log kesalahan
                print(f"Invalid data format: {str(e)}")
                return

            # Membuat koneksi ke database
            connection = get_connection()
            cursor = connection.cursor()

            # Cek apakah data dengan user_id sudah ada
            check_query = """
            SELECT * FROM user_summary_transaction WHERE user_id = %s
            """
            cursor.execute(check_query, (user_id,))
            existing_data = cursor.fetchone()

            if existing_data:
                # Jika data sudah ada, lakukan UPDATE
                update_query = """
                UPDATE user_summary_transaction
                SET total_amount = %s, amount_transaction = %s, last_date_transaction = %s, updated = CURRENT_TIMESTAMP
                WHERE user_id = %s
                """
                cursor.execute(update_query, (total_amount, amount_transaction, last_date_transaction, user_id))
                connection.commit()
            else:
                # Jika data belum ada, lakukan INSERT
                insert_query = """
                INSERT INTO user_summary_transaction (user_id, total_amount, amount_transaction, last_date_transaction, created, updated)
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """
                request_insert = (user_id, total_amount, amount_transaction, last_date_transaction)
                cursor.execute(insert_query, request_insert)
                connection.commit()

            # Menutup cursor dan koneksi
            cursor.close()
            connection.close()

    except Exception as e:
        # Jika ada error yang tidak terduga, cukup log kesalahan tersebut
        print(f"Error occurred: {str(e)}")
