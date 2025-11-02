from datetime import datetime
import mysql.connector

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="tiger",
)

my_cursor = mydb.cursor()

def getUsers():
    my_cursor.execute("use vehicledetails")
    my_cursor.execute("select * from authorized_users")

    users = my_cursor.fetchall()

    return users

def getLoginUsers():
    my_cursor.execute("use vehicledetails")


def update_vehicle_permissions_status_allowed(license_number):
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="tiger",
        database= "rcpit_admin"
    )
    cursor = conn.cursor()
    current_time = datetime.now()

    # Define the SQL query to insert or update the record
    sql = """
    UPDATE vehicle_permissions
    SET permission_status = 'allowed', response_received_timestamp = %s
    WHERE license_plate = %s
    """
    
    # Execute the query, updating the record with the new license plate and timestamps
    cursor.execute(sql, (current_time, license_number))

    # Commit the transaction if you're using a transactional database
    cursor.conn.commit()


def update_vehicle_permissions_status_denied(license_number):
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="tiger",
        database= "rcpit_admin"
    )
    cursor = conn.cursor()
    current_time = datetime.now()

    # Define the SQL query to insert or update the record
    sql = """
    UPDATE vehicle_permissions
    SET permission_status = 'denied', response_received_timestamp = %s
    WHERE license_plate = %s
    """
    
    # Execute the query, updating the record with the new license plate and timestamps
    cursor.execute(sql, (current_time, license_number))

    # Commit the transaction if you're using a transactional database
    cursor.conn.commit()



# Function to save visitor details
def save_visitor(visitor_name, vehicle_validity, license_number, email):
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="tiger",
        database="rcpit_admin"  # Adjust the database name if necessary
    )
    cursor = conn.cursor()

    current_time = datetime.now()

    # SQL query to insert visitor data into the table
    sql = """
    INSERT INTO visitors (name, license_number, validity, email)
    VALUES (%s, %s, %s, %s)
    """

    # Execute the query with the provided visitor details
    cursor.execute(sql, (visitor_name,license_number, vehicle_validity,email))

    # Commit the transaction to save the data in the database
    conn.commit()

    # Close the connection
    cursor.close()
    conn.close()

    # Return True to indicate successful insertion
    return True