from helper.db_helper import get_connection

def handle_transaction_success(event_data):
    connection = get_connection()
    cursor = connection.cursor()

    user_id = event_data["user_id"]
    amount = float(event_data["amount"])
    transaction_date = event_data["transaction_date"]

    # Update atau insert data summary
    update_query = """
    INSERT INTO user_summary (user_id, total_transactions, total_amount, last_transaction)
    VALUES (%s, 1, %s, %s)
    ON DUPLICATE KEY UPDATE
        total_transactions = total_transactions + 1,
        total_amount = total_amount + VALUES(total_amount),
        last_transaction = VALUES(last_transaction)
    """
    cursor.execute(update_query, (user_id, amount, transaction_date))
    connection.commit()
    cursor.close()
    connection.close()
