from datetime import time
from flask import Flask,render_template,url_for,request,redirect,flash,session
import mysql.connector
from flask_login import LoginManager,UserMixin,current_user,login_user,login_required,logout_user
from database import getUsers,my_cursor, save_visitor,update_vehicle_permissions_status_allowed, update_vehicle_permissions_status_denied
import os,subprocess,threading
import winsound


app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

import sys
print(sys.executable)


login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return 

def get_current_user():
    user = None
    if "user" in session:
        user = session['user'] 
        print("Session of"+user)
    
    return user

def check_db_connection():
    try:
        conn=mysql.connector.connect(
           host="localhost",
           user="root",
           password="tiger"
        )
        print("succesfull connected")
        conn.commit()
        return True
    except mysql.connector.Error as e:
        return False

check_db_connection()
# user=getUsers()
# countUser = len(user)

@app.route('/')
def homePage():
    # return "hello World"
    return render_template('finalLanding/index.html')

@app.route('/login',methods=["GET","POST"])
def loginPage():
    # return "hello World"
    if request.method=="POST":
        username=request.form['username']
        user_entered_password=request.form['password']
        my_cursor.execute("use vehicledetails")
        my_cursor.execute("select * from admins where username = %s", [username,])
        user = my_cursor.fetchone()
        print(user[3])

        if user:
            if user[3]==user_entered_password:
                print("Password is correct")
                session['user'] = user[1]
                print(session)
                return redirect(url_for('dashboard'))
            else:
                print("Incorrect!!")
                return redirect(url_for('loginPage'))

    return render_template('loginAndSignup/login.html')

@app.route('/signup')
def signUpPage():
    # return "hello World"
    return render_template('loginAndSignup/signup.html')

@app.route('/admin-dashboard')
def dashboard():
    user = get_current_user()
    if user:
        return render_template('DashboardAdmin/adminDashboard.html',countUser=10,user=user)
    else:
        return render_template('loginAndSignup/access.html')

@app.route('/add-visitor', methods=['GET', 'POST'])
def addVisitor():
    user = get_current_user()
    if user:
        if request.method == 'POST':
            # Handle form submission (saving data to the database)
            visitor_name = request.form.get('visitorName')
            vehicle_validity = request.form.get('vehicleValidity')
            license_number = request.form.get('licenseNumber')
            email = request.form.get('email')

            # Call the function to save visitor data to the database
            if save_visitor(visitor_name, vehicle_validity, license_number, email):
                # Use flash to send a success message to the template
                flash('Visitor successfully registered!', 'success')
            else:
                # If there's an error, show an error message
                flash('Error saving visitor information.', 'danger')
        
        # Render the form and show any flashed messages
        return render_template('DashboardAdmin/pages/visitor.html')
    else:
        return render_template('loginAndSignup/access.html')
    

@app.route('/add-vehicle', methods=['GET', 'POST'])
def addVehicle():
    user = get_current_user()
    if user:
        if request.method == 'POST':
            # Handle form submission (saving data to the database)
            owner_name = request.form.get('onwerName')
            license_number = request.form.get('licenseNumber')
            email = request.form.get('email')

            # Call the function to save visitor data to the database
            if save_visitor(owner_name, license_number, license_number, email):
                # Use flash to send a success message to the template
                flash('Visitor successfully registered!', 'success')
            else:
                # If there's an error, show an error message
                flash('Error saving visitor information.', 'danger')
        
        # Render the form and show any flashed messages
        return render_template('DashboardAdmin/pages/addVehicle.html')
    else:
        return render_template('loginAndSignup/access.html')


# Set the path to the upload folder in the backend directory
UPLOAD_FOLDER = os.path.join('..','Backend', 'Uploads')  # Adjust the path based on your structure
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
  
@app.route('/upload', methods=['GET', 'POST'])
def uploadPage():
    user = get_current_user()
    print(user)
    if user:
        if request.method == 'POST':
            if 'video' not in request.files:
                flash('No file part', 'danger')
                return redirect(request.url)

            file = request.files['video']

            if file.filename == '':
                flash('No selected file', 'danger')
                return redirect(request.url)
            
            # Set a standardized filename
            standardized_filename = 'UserUploadedVideo.mp4'

            # Save the uploaded file to the upload folder
            
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], standardized_filename)
            file.save(file_path)

            flash('File uploaded successfully', 'success')

            # Run the main.py script asynchronously using threading
            # detection_thread = threading.Thread(target=run_detection_script, args=(file_path,user))
            detection_thread = threading.Thread(target=run_detection_script,args=(user,))
            detection_thread.start()

            flash('Video processing started. You will be notified when complete.', 'info')    

            return redirect(url_for('uploadPage'))

        return render_template('dashboardAdmin/uploadPage/upload.html', user=user)
    else:
        return render_template('loginAndSignup/access.html')
    

@app.route('/live-stream', methods=['GET', 'POST'])
def liveStream():
    user = get_current_user()
    if user:
        return render_template('dashboardAdmin/webcamPage/liveStream.html', user=user)
    else:
        return render_template('loginAndSignup/access.html')
    
@app.route('/start-stream', methods=['POST'])
def startStream():
    user = get_current_user()

    # Start the live stream detection in a background thread
    stream_detection_thread = threading.Thread(target=run_live_stream_detection,args=(user,))
    stream_detection_thread.start()

    flash('Live stream detection started!', 'info')
    return redirect(url_for('liveStream'))
    

@app.route('/vehicleLogs-table')
def table():
    # print(user)
    current_user=get_current_user()
    check_db_connection()
    # my_cursor.execute("use rcpit_admin")
    my_cursor.execute(f"USE {current_user}")
    my_cursor.execute("select * from vehicle_logs")

    vehicle_logs = my_cursor.fetchall()
    # print(user)

    return render_template('DashboardAdmin/pages/tables/basic-table.html',logs=vehicle_logs,user=current_user)

# @app.route('/vehicleLogs-charts')
# def charts():
#     # print(user)
#     user=get_current_user()
#     return render_template('DashboardAdmin/pages/charts/chartjs.html',user=user)


# Function to run main.py asynchronously
def run_detection_script(user):
     python_executable = os.path.join('..','..', 'new_env', 'Scripts', 'python.exe')
     if not os.path.exists(python_executable):
         print(f"Python executable not found: {python_executable}")
     else:
         print(f"Found Python executable: {python_executable}")
     main_script_path = os.path.abspath(os.path.join('..', 'Backend', 'main.py'))
     file_path = os.path.abspath(os.path.join('..', 'Backend','Uploads', 'UserUploadedVideo.mp4'))
     print(main_script_path)
     print(file_path)
     #subprocess.run([python_executable, main_script_path, file_path,user])
     subprocess.run([python_executable, main_script_path, file_path, user])


    #  python_executable = os.path.join('..', 'new_env', 'Scripts', 'python.exe')
    #  subprocess.run([python_executable, os.path.join('..','Backend', 'main.py'),current_user,file_path])


# Function to run main.py asynchronously
def run_live_stream_detection(user):
     python_executable = os.path.join('..','..', 'new_env', 'Scripts', 'python.exe')
     liveStream_script_path = os.path.abspath(os.path.join('..', 'Backend', 'livestream.py'))
     #subprocess.run([python_executable, main_script_path, file_path,user])
     subprocess.run([python_executable, liveStream_script_path,user])


#-------------------------------NOTIFICATION CODE__________________________
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# SMTP server configuration - bxev ktip ufuf kfbk  && yqwl fcbs xjnk ynge
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "waghvinod4625@gmail.com"
SENDER_PASSWORD = "yqwlfcbsxjnkynge" 
def send_deny_notification(license_number):
    subject = f"Vehicle Exit Denied: {license_number}"
    message_body = f"""
    <html>
    <body>
    <p>Hello Admin,</p>
    <p>The exit request for the vehicle with license number <b>{license_number}</b> has been denied.</p>
    <p>Please check the system for further details.</p>
    </body>
    </html>
    """

    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = "campusguard2025@gmail.com"
    msg["Subject"] = subject
    msg.attach(MIMEText(message_body, "html"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, "campusguard2025@gmail.com", msg.as_string())
            print(f"Denial notification sent to admin for vehicle {license_number}")
    except Exception as e:
        print(f"Error sending denial email: {e}")

        
# Flask routes for Allow and Deny
@app.route('/allow/<license_number>', methods=['GET'])  #To make sure that user give permisson multiple times so maintain table after pressing the link goes to route update status of permisson given this can be used in live stream
def allow_exit(license_number):
    # update_vehicle_permissions_status_allowed(license_number)
    print(f"Vehicle {license_number} allowed to exit.")
    play_sound(True) 
    return f"Vehicle {license_number} is allowed to exit."

@app.route('/deny/<license_number>', methods=['GET'])
def deny_exit(license_number):
    # update_vehicle_permissions_status_denied(license_number)
    print(f"Vehicle {license_number} denied exit.")
    play_sound(False) 
    send_deny_notification(license_number)
    return f"Vehicle {license_number} is denied exit."

#--------------------ALERT SYSTEM-----------------#

import time
# import winsound
import msvcrt  # To detect key presses

# Flag to control whether the sound should continue or not
stop_alert = False

def play_sound(is_allowed):
    global stop_alert

    if is_allowed:
        # Play sound for "Allowed"
        winsound.Beep(1000, 1000)  # 1000 Hz for 1 second
    else:
        # Play sound for "Denied" in a loop until the 'Esc' key is pressed
        print("Playing 'Denied' sound. Press 'Esc' to stop.")
        
        while not stop_alert:
            winsound.Beep(500, 1000)  # 500 Hz for 1 second
            time.sleep(1)  # Delay for 1 second between beeps
            
            # Check if 'Esc' key is pressed
            if msvcrt.kbhit():  # Check if a key is pressed
                key = msvcrt.getch()  # Get the pressed key
                if key == b'\x1b':  # ASCII for 'Esc' key
                    stop_alert = True
                    print("Esc key pressed. Stopping the sound.")
                    break


if __name__ == '__main__':
    app.run(debug=True)