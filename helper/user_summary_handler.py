from helper.db_helper import get_connection
from datetime import datetime

def save_data_to_db(data):
    """Fungsi untuk menyimpan data dari Kafka ke database."""
    try:
        # Parsing data JSON
        user_id = int(data.get("user_id"))
        total_amount = float(data.get("total_amount"))
        amount_transaction = int(data.get("amount_transaction"))
        last_date_transaction = datetime.strptime(
            data.get("last_date_transaction"), "%Y-%m-%d %H:%M:%S"
        )

        # Gunakan context manager untuk koneksi database
        with get_connection() as connection:
            with connection.cursor() as cursor:
                # Cek apakah data dengan user_id sudah ada
                check_query = """
                SELECT * FROM user_summary_transaction WHERE user_id = %s
                """
                cursor.execute(check_query, (user_id,))
                existing_data = cursor.fetchone()

                if existing_data:
                    # Update jika data sudah ada
                    update_query = """
                    UPDATE user_summary_transaction
                    SET total_amount = %s, amount_transaction = %s, last_date_transaction = %s, updated = CURRENT_TIMESTAMP
                    WHERE user_id = %s
                    """
                    cursor.execute(update_query, (total_amount, amount_transaction, last_date_transaction, user_id))
                    print(f"Data for user_id {user_id} updated successfully.")
                else:
                    # Insert jika data baru
                    insert_query = """
                    INSERT INTO user_summary_transaction (user_id, total_amount, amount_transaction, last_date_transaction, created, updated)
                    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """
                    cursor.execute(insert_query, (user_id, total_amount, amount_transaction, last_date_transaction))
                    print(f"Data for user_id {user_id} inserted successfully.")

            connection.commit()  # Commit perubahan
    except Exception as e:
        print(f"Error while saving data to database: {str(e)}")


