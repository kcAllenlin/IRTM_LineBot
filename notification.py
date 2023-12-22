import psycopg2
db_url = os.environ['DATABASE_URL']

def get_all_user_ids():
    connection = psycopg2.connect(db_url)

    cursor = connection.cursor()
    cursor.execute("SELECT user_id FROM user_data")
    result = cursor.fetchall()
    cursor.close()
    connection.close()
    return [row[0] for row in result] i 
# send_alert_message()
user_ids = get_all_user_ids()
print(user_ids)