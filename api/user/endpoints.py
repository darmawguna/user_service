"""Routes for module books"""
import os
from flask import Blueprint, jsonify, request
from helper.db_helper import get_connection
from helper.form_validation import get_form_data
from flasgger import  swag_from
from helper.email_helper import is_valid_email,is_valid_phone_number,is_email_exists,is_email_exists_for_update

users_endpoints = Blueprint('users', __name__)

@users_endpoints.route('/', methods=['GET'])
@swag_from('./doc/get.yml')
def read():
    """
    Endpoint untuk membaca daftar pengguna dengan pagination
    """
    connection = None
    cursor = None
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 25, type=int)
        offset = (page - 1) * limit

        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        select_query = "SELECT * FROM users LIMIT %s OFFSET %s"
        cursor.execute(select_query, (limit, offset))
        results = cursor.fetchall()

        cursor.execute("SELECT COUNT(*) FROM users")
        total_count = cursor.fetchone()['COUNT(*)']

        total_pages = (total_count + limit - 1) // limit

        return jsonify({
            "message": "OK",
            "count": len(results),
            "total_count": total_count,
            "total_pages": total_pages,
            "current_page": page,
            "datas": results
        }), 200

    except Exception as e:
        
        return jsonify({"message": f"Error fetching data: {str(e)}"}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@users_endpoints.route('/create', methods=['POST'])
@swag_from('./doc/create_data.yml')
def create():
    """Endpoint untuk membuat transaksi baru"""
   
    try:
        required = get_form_data(["full_name", "email", "phone_number"])  
        full_name = required["full_name"]
        email = required["email"]
        phone_number = required["phone_number"]
        
       
        if not is_valid_email(email):
            return jsonify({"message": "Invalid email format"}), 400

        
        if not is_valid_phone_number(phone_number):
            return jsonify({"message": "Phone number must be between 10 and 15 characters"}), 400

        
        if is_email_exists(email):
            return jsonify({"message": "Email already exists"}), 400
        
    except KeyError as e:
        return jsonify({"message": f"Missing required field: {str(e)}"}), 400

   
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()

        
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
        if cursor:
            cursor.close()
        if connection:
            connection.close()



@users_endpoints.route('/<int:user_id>', methods=['PUT'])
@swag_from('./doc/edit_user.yml')
# @swag_from('docs/users_update.yml')  # Dokumentasi Flasgger
def update(user_id):
    """Method untuk update user"""
    try:
        
        required = get_form_data(["full_name", "email", "phone_number"])
        full_name = required["full_name"]
        email = required["email"]
        phone_number = required["phone_number"]

        
        if not is_valid_email(email):
            return jsonify({"message": "Invalid email format"}), 400

        
        if not is_valid_phone_number(phone_number):
            return jsonify({"message": "Phone number must be between 10 and 15 characters"}), 400

        
        if is_email_exists_for_update(email, user_id):
            return jsonify({"message": "Email already exists"}), 400

        connection = get_connection()
        cursor = connection.cursor()

        
        cursor.execute("SELECT full_name, email, phone_number FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        
        if not user:
            return jsonify({"message": "User not found"}), 404
        
        
        if (full_name == user['full_name'] and
            email == user['email'] and
            phone_number == user['phone_number']):
            return jsonify({"message": "No changes detected, user not updated"}), 200

        
        update_query = """
        UPDATE users
        SET full_name = %s, email = %s, phone_number = %s
        WHERE id = %s
        """
        cursor.execute(update_query, (full_name, email, phone_number, user_id))
        connection.commit()

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
@swag_from('./doc/delete_user.yml')
def delete(user_id):
    """Method untuk delete user"""
    try:
        connection = get_connection()
        cursor = connection.cursor()

       
        delete_query = "DELETE FROM users WHERE id = %s"
        cursor.execute(delete_query, (user_id,))
        connection.commit()

        
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




@users_endpoints.route('/validate-user/<int:user_id>', methods=['GET'])
@swag_from('./doc/validate_user.yml')
def validate_user(user_id): 
    """Endpoint untuk memeriksa keberadaan user_id"""
    connection = None
    cursor = None
    try:
        if user_id is None:
            return jsonify({"message": "Missing required parameter: user_id"}), 400

        connection = get_connection()
        cursor = connection.cursor()

        
        query = """
        SELECT user_id FROM users
        WHERE user_id = %s
        """
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()

        
        if result:
            return jsonify({"message": "true"}), 200

        
        return jsonify({"message": "false"}), 200

    except Exception as e:
        return jsonify({"message": f"Error checking user: {str(e)}"}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# TODO tambahkan 1 method untuk mengambil summary transaksi user 
# @users_endpoints.route('/get-user-summary/<int:user_id>', methods=['GET'])
# @swag_from('./doc/get_summary_user.yml')
# def get_user_summary(user_id): 
#     """Endpoint untuk mendapatkan summary transaksi user."""
#     url = f"http://127.0.0.1:5000/api/transactions/get-summary-transaction/{user_id}"
#     try:
        
#         response = requests.get(url, timeout=10)
#         response.raise_for_status()  
        
        
#         if response.headers.get('Content-Type') == 'application/msgpack':
            
#             message_data = msgpack.unpackb(response.content, raw=False)
#             print("Decoded data:", message_data)
           
#             return jsonify({
#                 "data" : message_data,
#                 "message" : "success get transaction Summary"
#                 })
#         else:
#             return jsonify({"error": "Unexpected content type", "content_type": response.headers.get('Content-Type')}), 400

#     except requests.exceptions.Timeout:
#         return jsonify({"error": "Request to external API timed out"}), 504
#     except requests.exceptions.RequestException as e:
#         return jsonify({"error": f"Error while contacting external API: {str(e)}"}), 500
#     except Exception as e:
#         return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@users_endpoints.route('/<int:user_id>/summary', methods=['GET'])
@swag_from('./doc/summary_user.yml')
def user_summary(user_id):
    """Method untuk mendapatkan ringkasan transaksi user"""
    try:
        connection = get_connection()
        cursor = connection.cursor()

        # Query untuk mengambil ringkasan transaksi
        select_query = """
        SELECT 
            user_id, 
            total_amount, 
            amount_transaction, 
            last_date_transaction
        FROM 
            user_summary_transaction
        WHERE 
            user_id = %s
        """
        cursor.execute(select_query, (user_id,))
        result = cursor.fetchone()
        total_amount = result[1]
        amount_transaction = result[2]
        last_date_transaction = result[3]
        

        # Jika tidak ada data ditemukan
        if result is None:
            return jsonify({"message": "User not found"}), 404
        

        # Menyiapkan data untuk dikembalikan
        summary = {
            
            "total_amount": total_amount,
            "amount_transaction": amount_transaction,
            "last_date_transaction": last_date_transaction,
        }

        return jsonify({
            "message": "success get transaction Summary",
            "data": summary
            }), 200

    except Exception as e:
        return jsonify({"message": f"Error retrieving data: {str(e)}"}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
