"""Routes for module books"""
import os
from flask import Blueprint, jsonify, request
from helper.db_helper import get_connection
from helper.form_validation import get_form_data
from flasgger import  swag_from
import redis

users_endpoints = Blueprint('users', __name__)
# Koneksi ke Redis yang berjalan di localhost (port 6379)
r = redis.StrictRedis(host='localhost', port=6379, db=0)

@users_endpoints.route('/', methods=['GET'])
def read():
    
    # Membuat koneksi ke database
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    # Query untuk mendapatkan daftar buku
    select_query = "SELECT * FROM users"
    cursor.execute(select_query)
    results = cursor.fetchall()
    
    # Menutup cursor dan koneksi
    cursor.close()
    connection.close()
    
    # Mengembalikan respons dalam format JSON
    return jsonify({"message": "OK", "datas": results}), 200

@users_endpoints.route('/create', methods=['POST'])
def create():
    """Endpoint untuk membuat transaksi baru"""
    # Validasi input dari form
    try:
        required = get_form_data(["full_name", "email", "phone_number"])  
        full_name = required["full_name"]
        email = required["email"]
        phone_number = required["phone_number"]

        
    except KeyError as e:
        return jsonify({"message": f"Missing required field: {str(e)}"}), 400

    # Memasukkan data ke database
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()

        # Query untuk memasukkan transaksi baru
        insert_query = """
        INSERT INTO users (full_name, email, phone_number)
        VALUES (%s, %s, %s)
        """
        request_insert = (full_name, email, phone_number)
        cursor.execute(insert_query, request_insert)
        connection.commit()
        

        return jsonify(
         {
            "message": "User successfully created",
            "datas": {
                "full_name": full_name,
                "email": email,
                "phone_number": phone_number,
            }
         }), 201

    except Exception as e:
        if connection:
            connection.rollback()
        return jsonify({"message": f"Error inserting data: {str(e)}"}), 500

    finally:
        if cursor:  # Pastikan cursor telah didefinisikan
            cursor.close()
        if connection:  # Pastikan connection telah didefinisikan
            connection.close()


@users_endpoints.route('/<int:user_id>', methods=['PUT'])
# @swag_from('docs/users_update.yml')  # Dokumentasi Flasgger
def update(user_id):
    """Update a user's information"""
    try:
        # Validasi input
        required = get_form_data(["full_name", "email", "phone_number"])
        full_name = required["full_name"]
        email = required["email"]
        phone_number = required["phone_number"]

        connection = get_connection()
        cursor = connection.cursor()

        # Query untuk memperbarui user
        update_query = """
        UPDATE users
        SET full_name = %s, email = %s, phone_number = %s
        WHERE id = %s
        """
        cursor.execute(update_query, (full_name, email, phone_number, user_id))
        connection.commit()

        # Cek apakah ada baris yang diperbarui
        if cursor.rowcount == 0:
            return jsonify({"message": "User not found"}), 404

        return jsonify({
            "id": user_id,
            "full_name": full_name,
            "email": email,
            "phone_number": phone_number,
            "message": "User successfully updated"
        }), 200

    except KeyError as e:
        return jsonify({"message": f"Missing required field: {str(e)}"}), 400

    except Exception as e:
        if connection:
            connection.rollback()
        return jsonify({"message": f"Error updating data: {str(e)}"}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@users_endpoints.route('/<int:user_id>', methods=['DELETE'])
# @swag_from('docs/users_delete.yml')  # Dokumentasi Flasgger
def delete(user_id):
    """Delete a user"""
    try:
        connection = get_connection()
        cursor = connection.cursor()

        # Query untuk menghapus user
        delete_query = "DELETE FROM users WHERE id = %s"
        cursor.execute(delete_query, (user_id,))
        connection.commit()

        # Cek apakah ada baris yang dihapus
        if cursor.rowcount == 0:
            return jsonify({"message": "User not found"}), 404

        return jsonify({"message": "User successfully deleted"}), 200

    except Exception as e:
        if connection:
            connection.rollback()
        return jsonify({"message": f"Error deleting data: {str(e)}"}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@users_endpoints.route('summary-user', methods=['GET'])
def get_user_summary():
    """Endpoint untuk mengambil summary user dari Redis dan menyimpannya ke database"""
    try:
        # Mengambil data dari Redis dengan key 'latest_message'
        latest_message = r.get('latest_message')

        if latest_message:
            # Decode untuk mendapatkan string, lalu parsing JSON
            import json
            from datetime import datetime
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
                return jsonify({"message": f"Invalid data format: {str(e)}"}), 400

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
                message = "Data successfully updated in database."
            else:
                # Jika data belum ada, lakukan INSERT
                insert_query = """
                INSERT INTO user_summary_transaction (user_id, total_amount, amount_transaction, last_date_transaction, created, updated)
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """
                request_insert = (user_id, total_amount, amount_transaction, last_date_transaction)
                cursor.execute(insert_query, request_insert)
                connection.commit()
                message = "Data successfully saved to database."

            # Menutup cursor dan koneksi
            cursor.close()
            connection.close()

            return jsonify({"message": message}), 200

        else:
            return jsonify({"message": "No message found in Redis."}), 404

    except Exception as e:
        return jsonify({"message": f"Error occurred: {str(e)}"}), 500



