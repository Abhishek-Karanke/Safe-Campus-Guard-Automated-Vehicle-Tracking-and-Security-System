# import smtplib
# from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText

# # SMTP server configuration
# SMTP_SERVER = "smtp.gmail.com"
# SMTP_PORT = 587
# SENDER_EMAIL = "waghvinod4625@gmail.com"  # Sender's email
# SENDER_PASSWORD = "yqzfdsvijbzjxweu"     # Sender's App Password (use an app password if 2FA is enabled)

# def send_email_notification(to_email, subject, message_body):
#     # Set up the email
#     msg = MIMEMultipart()
#     msg["From"] = SENDER_EMAIL
#     msg["To"] = to_email   # This is where the recipient's email goes
#     msg["Subject"] = subject

#     # Attach the message body
#     msg.attach(MIMEText(message_body, "plain"))

#     # Send the email
#     try:
#         with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
#             server.starttls()  # Secure connection
#             server.login(SENDER_EMAIL, SENDER_PASSWORD)
#             server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
#             print("Email sent successfully to", to_email)
#     except Exception as e:
#         print("Error sending email:", e)

# # Testing the email function
# to_email = "vinodwagh.rcpit2003@gmail.com"  # The recipient's email
# subject = "Test Email for ANPR System"
# message_body = "This is a test email to confirm that the notification system works."

# send_email_notification(to_email, subject, message_body)


#SENDER_PASSWORD = "yqzfdsvijbzjxweu"
# Function to send email notification with "Allow" and "Deny" links
# def send_email_notification(to_email, subject, message_body):
#     msg = MIMEMultipart()
#     msg["From"] = SENDER_EMAIL
#     msg["To"] = to_email
#     msg["Subject"] = subject

#     msg.attach(MIMEText(message_body, "html"))  # Use HTML to add clickable links

#     try:
#         with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
#             server.starttls()
#             server.login(SENDER_EMAIL, SENDER_PASSWORD)
#             server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
#             print(f"Email sent successfully to {to_email}")
#     except Exception as e:
#         print(f"Error sending email: {e}")


# # Route to trigger sending the email with the links
# @app.route('/send_email', methods=['GET'])
# def send_notification():
#     license_number = "XYZ123"  # Replace with dynamic license number if needed
#     vehicle_owner_email = "recipient_email@example.com"  # Replace with actual email

#     subject = "Vehicle Exit Request"
#     message_body = f"""
#     <html>
#     <body>
#     <p>Hello,</p>
#     <p>A vehicle with license number {license_number} is requesting to exit the campus.</p>
#     <p>Please choose one of the following actions:</p>
#     <ul>
#         <li><a href="http://127.0.0.1:5000/allow/{license_number}">Allow</a></li>
#         <li><a href="http://127.0.0.1:5000/deny/{license_number}">Deny</a></li>
#     </ul>
#     <p>Thank you.</p>
#     </body>
#     </html>
#     """

#     # Send email
#     send_email_notification(vehicle_owner_email, subject, message_body)
#     return "Email sent successfully with options for vehicle owner."



import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# SMTP server configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "waghvinod4625@gmail.com"
SENDER_PASSWORD = "yqwlfcbsxjnkynge" 
# Function to send email notification with "Allow" and "Deny" links
def send_email_notification(to_email, subject, message_body):
    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.attach(MIMEText(message_body, "html"))  # Use HTML to add clickable links

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
            print(f"Email sent successfully to {to_email}")
    except Exception as e:
        print(f"Error sending email: {e}")



def send_notification(license_number,vehicle_owner_email):
    # license_number = "XYZ123"  # Replace with dynamic license number if needed
    vehicle_owner_email = vehicle_owner_email  

    subject = "Vehicle Exit Request"
    message_body = f"""
    <html>
    <body>
    <p>Hello,</p>
    <p>A vehicle with license number {license_number} is requesting to exit the campus.</p>
    <p>Please choose one of the following actions:</p>
    <ul>
        <li><a href="http://127.0.0.1:5000/allow/{license_number}">Allow</a></li>
        <li><a href="http://127.0.0.1:5000/deny/{license_number}">Deny</a></li>
    </ul>
    <p>Thank you.</p>
    </body>
    </html>
    """

    # Send email
    send_email_notification(vehicle_owner_email, subject, message_body)
    return "Email sent successfully with options for vehicle owner."
