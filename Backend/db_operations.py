from datetime import datetime
import mysql.connector


def insert_vehicle_logs(license_number, db_name):
    """
    Insert a single record into the vehicle_logs table with the current date and time.

    Args:
        license_number (str): The license plate number to insert.
        db_name (str): The name of the database.
    """
    # Get the current date and time
    current_datetime = datetime.now()
    date = current_datetime.date()
    time = current_datetime.time()

    try:
        # Establish a database connection with `with` for automatic cleanup
        with mysql.connector.connect(
            host="localhost",
            user="root",
            password="tiger",
            database=db_name
        ) as conn:
            with conn.cursor() as cursor:
                # SQL command to insert data
                insert_query = """
                INSERT INTO vehicle_logs (license_number, date, time)
                VALUES (%s, %s, %s);
                """
                # Execute the query with the current date and time
                cursor.execute(insert_query, (license_number, date, time))
                
                # Commit the transaction
                conn.commit()
                print("Record inserted successfully.")
    except mysql.connector.Error as err:
        print(f"Error: {err}")



def get_email_for_license_plate(license_number):
    try:
        # Establish a database connection with `with` for automatic cleanup
        with mysql.connector.connect(
            host="localhost",
            user="root",
            password="tiger",
            database="rcpit_admin"
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT email FROM vehicle_owners WHERE license_number = %s", (license_number,))
                result = cursor.fetchone()

                if result:
                    return result[0]  # Return the email if found
                # else:
                #     print(f"No email found for license plate {license_number}")
                #     return None

                # Only reaches here if not found in vehicle_owners  ###ADDED CODE
                cursor.execute("SELECT email FROM visitors WHERE license_number = %s", (license_number,))
                result = cursor.fetchone()

                if result:
                    return result[0]  # Found in visitors → return email    ###ADDED CODE END 
                
    except mysql.connector.Error as e:
        print(f"Error querying the database: {e}")
        return None


def vehicle_permissions_status(formatted_license_plate):
    try:
        # Establish a database connection with a buffered cursor to ensure all results are fetched
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="tiger",
            database="rcpit_admin"
        )
        
        with conn.cursor(buffered=True) as cursor:
            current_time = datetime.now()

            # Define the SQL query to insert or update the record
            sql = """
            INSERT INTO vehicle_permissions (license_plate, permission_status, email_sent_timestamp)
            VALUES (%s, 'waiting', %s)
            ON DUPLICATE KEY UPDATE 
                license_plate = VALUES(license_plate),
                permission_status = 'waiting',
                email_sent_timestamp = VALUES(email_sent_timestamp),
                response_received_timestamp = NULL;  -- Reset response timestamp on new detection
            """
            
            # Execute the query
            cursor.execute(sql, (formatted_license_plate, current_time))
            conn.commit()  # Commit the transaction
            print("Record inserted or updated successfully.")
            
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        
    finally:
        # Close the connection in the finally block to ensure it's closed even if an error occurs
        conn.close()


def update_suspicious_status(db_name):
    # Use `with` statements for database connection and cursor
    with mysql.connector.connect(
        host="localhost",
        user="root",
        password="tiger",
        database=db_name
    ) as conn:
        with conn.cursor() as cursor:
            # SQL query to update is_suspicious status
            update_query = """
            UPDATE vehicle_logs
            LEFT JOIN rto_vehicles ON vehicle_logs.license_number = rto_vehicles.license_number
            SET vehicle_logs.is_suspicious = CASE
                WHEN rto_vehicles.license_number IS NULL THEN 'Yes'
                ELSE 'No'
            END;
            """
            try:
                cursor.execute(update_query)
                conn.commit()  # Commit the changes
                print("Suspicious status updated successfully.")
            except mysql.connector.Error as err:
                print(f"Error: {err}")

