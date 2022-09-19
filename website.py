"""
CanteenFastCard Website backend program
"""

import os
import pyotp
import pandas
import sqlite3
from datetime import timedelta

from flask import Flask, url_for, redirect, render_template, request, session
from dotenv import load_dotenv

from scanner import scan
from __init__ import *



# connecting to the database
db = sqlite3.connect('Database/kiit_kp_canteen.db') # :memory:
sql = db.cursor()

# crearing the required tables
sql.execute('CREATE TABLE IF NOT EXISTS student_info(id INTEGER PRIMARY KEY, usid UID, student_name NAME, email TEXT)')
sql.execute('CREATE TABLE IF NOT EXISTS student_account(id INTEGER PRIMARY KEY, pin_code TEXT, amount INTEGER)')
sql.execute('CREATE TABLE IF NOT EXISTS admin_logins(SSID TEXT PRIMARY KEY, Password PASSWORD, Email TEXT)')

db.commit()

close_db(db, sql)


# website parameters (variables from env file)
load_dotenv('Database/website_info.env')
PORT = os.environ.get('PORT')
HOST = os.environ.get('HOST')
DEBUG = os.environ.get('DEBUG')

MASTER_2FA_EMAIL = os.environ.get('MASTER_2FA_EMAIL')
MASTER_PRODUCT_KEY = os.environ.get('MASTER_PRODUCT_KEY')
MASTER_PROCESS_KEY = os.environ.get('MASTER_PROCESS_KEY')


# global variables
twoFA_code = str()
website_error = list()
std_log_details = str()
admin_2FA_code = pyotp.TOTP

http = Flask(__name__)
http.secret_key = '3d9efc4wa651728'
http.permanent_session_lifetime = timedelta(minutes=3)



# **********************StudentLinks********************** #
# ******************************************************** #
@http.route('/')
def home_redirecter():
    return redirect(url_for('home'))


# ******************************************************** #
@http.route('/home')
def home():
    return render_template('Student/index.html')

@http.route('/home', methods=['POST'])
def login():
    global website_error

    _db = sqlite3.connect('Database/kiit_kp_canteen.db')
    
    session["active_student_id"] = int(request.form['std_id'])
    std_id_pin = request.form['std_id_pin']
    
    try:
        if scan_ids(_db, int(session["active_student_id"])) is True:
            if get_student_details(_db, int(session["active_student_id"]), 'pin_code') == std_id_pin:

                return redirect(url_for('dashboard', user=str(session["active_student_id"])))

            else: return render_template('Student/index.html', alert_message='[ Invalid Pin Code ]')
        else: return redirect(url_for('auto_id_registration'))

    except Exception as E:
        website_error = ['Home page post function', E]
        return render_template('Student/index.html', alert_message='[ Unable to verify ]')


# ******************************************************** #
@http.route('/dashboard/logout')
def logout():
    try: session.pop("active_student_id", None)
    except Exception: pass
    
    return redirect(url_for('home', status='logged-out'))
    

# ******************************************************** #
@http.route('/id/scan')
def login_by_scan():
    global website_error

    _db = sqlite3.connect('Database/kiit_kp_canteen.db')
    
    try:
        session["active_student_id"] = scan()

        if scan_ids(_db, int(session["active_student_id"])):
            return redirect(url_for('dashboard', user=str(session["active_student_id"])))

        else: return redirect(url_for('auto_id_registration'))
        
    except Exception as E:
        website_error = ['scanning ID', E]
        return render_template('Student/index.html', alert_message="Unable to scan the ID Card")


# ******************************************************** #
@http.route('/id/auto_registration')
def auto_id_registration():
    return render_template('Student/auto_id_registration.html', 
                           alert_message='[ Not Register! Register your ID here ]')

@http.route('/id/auto_registration', methods=['POST'])
def auto_id_registration_form():
    global website_error

    _db = sqlite3.connect('Database/kiit_kp_canteen.db')

    name = request.form['std_name'] #.replace(' ', '_')
    email = request.form['email']
    id_pin_code = request.form['pin_code']
    init_amount = request.form['initial_amount']
    master_key = int(request.form['master_product_key'])
    
    if master_key != int(MASTER_PRODUCT_KEY):
        return render_template('Student/auto_id_registration.html', 
                               alert_message='Invalid Master Product Key.')

    else:
        if len(id_pin_code) < 4:
            return render_template('Student/auto_id_registration.html', 
                                alert_message='[ Pin Code too short! ]')

        elif int(init_amount) < 30:
            return render_template('Student/auto_id_registration.html', 
                                    alert_message='[ Minimum amount required is Rs.30]')

        else:
            try:
                register_student(_db, int(session["active_student_id"]), id_pin_code,
                                int(init_amount), [name, email])
                
                return redirect(url_for('dashboard', user=str(session["active_student_id"])))

            except Exception as E:
                
                website_error = ['register', E]
                return render_template('Student/auto_id_registration.html', 
                                    alert_message='[ Unable to register this ID ]')


# ******************************************************** #
@http.route('/id/manual_registration')
def manual_id_registration():
    return render_template('Student/manual_id_registration.html')

@http.route('/id/manual_registration', methods=['POST'])
def manual_id_registration_form():
    global website_error

    _db = sqlite3.connect('Database/kiit_kp_canteen.db')

    session["active_student_id"] = request.form['std_roll_no']
    name = request.form['std_name']#.replace(' ', '_')
    email = request.form['email']
    id_pin_code = request.form['pin_code']
    init_amount = request.form['initial_amount']
    master_key = int(request.form['master_product_key'])
    
    if master_key != int(MASTER_PRODUCT_KEY):
        return render_template('Student/manual_id_registration.html', 
                               alert_message='Invalid Master Product Key.')

    else:
        if len(id_pin_code) < 4:
            return render_template('Student/manual_id_registration.html', 
                                alert_message='[ Pin Code too short! ]')
        
        elif int(init_amount) < 30:
            return render_template('Student/manual_id_registration.html', 
                                    alert_message='[ Minimum amount required is Rs.30]')
        
        else:
            try:
                register_student(_db, int(session["active_student_id"]), id_pin_code,
                                int(init_amount), [name, email])
                
                return redirect(url_for('dashboard', user=str(session["active_student_id"])))

            except Exception as E:
                website_error = ['register', E]
                return render_template('Student/manual_id_registration.html', 
                                    alert_message='[ Unable to register this ID ]')


# ******************************************************** #
@http.route('/dashboard/')
def dashboard():
    if "active_student_id" in session:
        return render_template('Student/dashboard.html', 
                            web_page_msg=f'Hey there: {str(session["active_student_id"])}. Welcome!', 
                            student_roll_no=str(session["active_student_id"]))
        
    else: return redirect(url_for('home', status='logged-out'))


# ******************************************************** #
@http.route('/account/payment')
def payment():
    if "active_student_id" in session:
        return render_template('Student/payment.html', 
                            web_page_msg=f'Hey there: {str(session["active_student_id"])}. Welcome!', 
                            student_roll_no=str(session["active_student_id"]))
    
    else: return redirect(url_for('home', status='logged-out'))

@http.route('/account/payment', methods=['POST'])
def payment_form():
    global website_error
    
    _db = sqlite3.connect('Database/kiit_kp_canteen.db')
    
    amount_to_pay = request.form['amount_to_pay']
    master_product_key = int(request.form['master_product_key'])
    std_amount = get_student_details(_db, int(session["active_student_id"]), 'amount')

    if int(MASTER_PRODUCT_KEY) != int(master_product_key):
        return render_template('Student/payment.html',
                               debit_status='❌Invalid Master Product Key.')

    else:
        if int(amount_to_pay) > int(std_amount):
            return render_template('Student/payment.html', 
                                web_page_msg=f'Hey there: {str(session["active_student_id"])}. Welcome!',
                                student_roll_no=str(session["active_student_id"]),
                                debit_status=f'⚠️Amount in account is less: ₹{std_amount}')

        else:
            try:
                debit_balance(_db, int(amount_to_pay), int(session["active_student_id"]))
                return render_template('Student/payment.html', 
                                    web_page_msg=f'Hey there: {str(session["active_student_id"])}. Welcome!',
                                    student_roll_no=str(session["active_student_id"]),
                                    debit_status='✅')

            except Exception as E:
                website_error = ['payment form', E]
                return render_template('Student/payment.html', 
                                    web_page_msg=f'Hey there: {str(session["active_student_id"])}. Welcome!',
                                    student_roll_no=str(session["active_student_id"]), 
                                    debit_status='❌Failed to do the payment process.')


# ******************************************************** #
@http.route('/account/balance/update')
def update_account_balance():
    if "active_student_id" in session:
        return render_template('Student/update_amount.html', 
                            web_page_msg=f'Hey there: {str(session["active_student_id"])}. Welcome!', 
                            student_roll_no=str(session["active_student_id"]))
        
    else: return redirect(url_for('home', status='logged-out'))

@http.route('/account/balance/update', methods=['POST'])
def update_account_balance_form():
    global website_error
    
    _db = sqlite3.connect('Database/kiit_kp_canteen.db')
    
    amount_to_update = request.form['amount_to_update']
    master_product_key = int(request.form['master_product_key'])
    
    if int(MASTER_PRODUCT_KEY) != int(master_product_key):
        return render_template('Student/update_amount.html', 
                               update_status='❌Invalid Master Product Key.')

    else:
        if int(amount_to_update) < 0:
            return render_template('Student/update_amount.html', 
                                web_page_msg=f'Hey there: {str(session["active_student_id"])}. Welcome!',
                                student_roll_no=str(session["active_student_id"]),
                                update_status='⚠️Invalid amount.')

        elif int(amount_to_update) == 0:
            return render_template('Student/update_amount.html', 
                                web_page_msg=f'Hey there: {str(session["active_student_id"])}. Welcome!',
                                student_roll_no=str(session["active_student_id"]))

        else:
            try:
                update_balance(_db, int(amount_to_update), int(session["active_student_id"]))
                return render_template('Student/update_amount.html', 
                                    web_page_msg=f'Hey there: {str(session["active_student_id"])}. Welcome!',
                                    student_roll_no=str(session["active_student_id"]),
                                    update_status='✅')
            
            except Exception as E:
                website_error = ['payment form', E]
                return render_template('Student/update_amount.html', 
                                    web_page_msg=f'Hey there: {str(session["active_student_id"])}. Welcome!',
                                    student_roll_no=str(session["active_student_id"]),
                                    update_status='❌Unable to update the account balance.')


# ******************************************************** #
@http.route('/account/balance/check')
def check_balance():
    if "active_student_id" in session:
        _db = sqlite3.connect('Database/kiit_kp_canteen.db')
        left_amount = get_student_details(_db, int(session["active_student_id"]), 'amount')
        
        return render_template('Student/balance_check.html',
                               web_page_msg=f'Hey there: {str(session["active_student_id"])}. Welcome!',
                               student_roll_no=session["active_student_id"], 
                               amount=str(left_amount))

    else: return redirect(url_for('home', status='logged-out'))


# ******************************************************** #
@http.route('/account/transaction/view')
def view_log():
    global website_error

    if "active_student_id" in session:
        try:
            _db = sqlite3.connect('Database/kiit_kp_canteen.db')
            std_log_name = get_student_details(_db, int(session["active_student_id"]), 'usid')
            
            with open(f'Database/logs/{std_log_name}.txt', 'r') as log_file:
                std_transaction_details = log_file.read()
                
            return render_template('Student/log_viewer.html', 
                                   web_page_msg=f'Hey there: {str(session["active_student_id"])}. Welcome!', 
                                   student_roll_no=str(session["active_student_id"]), 
                                   content=str(std_transaction_details))
        
        except Exception as E:
            website_error = ['view_log web method', E]
            return render_template('Student/dashboard.html', 
                                   student_roll_no=str(session["active_student_id"]), 
                                   error="Oops... Something went wrong 🤷🏼‍♂️")
        
    else: return redirect(url_for('home', status='logged-out'))


# ******************************************************** #
@http.route('/account/transaction/send_log')
def send_transaction_log():
    global website_error
    
    if "active_student_id" in session:
        _db = sqlite3.connect('Database/kiit_kp_canteen.db')
        
        try:
            std_email = get_student_details(_db, int(session["active_student_id"]), 'email')

            send_mail(_db, int(session["active_student_id"]), 'log')
            return render_template('Student/transaction_log_sender.html', 
                                   web_page_msg=f'Hey there: {str(session["active_student_id"])}. Welcome!', 
                                   student_roll_no=str(session["active_student_id"]),
                                   status=f"Log file Sent to {std_email}")
        
        except Exception as E:
            website_error = ['Sending Log (send_transaction_log web method)', E]
            return render_template('Student/dashboard.html', 
                                   student_roll_no=str(session["active_student_id"]),
                                   alert_message="Oops... Something went wrong 🤷🏼‍♂️")
        
    else: return redirect(url_for('home', status='logged-out'))


# ******************************************************** #
@http.route('/account/update/pin_code/2FA')
def twoFA():
    return render_template('Student/2FA.html', validity='')

@http.route('/account/update/pin_code/2FA', methods=['POST'])
def twoFA_form():
    global website_error
    global twoFA_code

    _db = sqlite3.connect('Database/kiit_kp_canteen.db')
    session["active_student_id"] = int(request.form['std_roll_no_pcr'])
    
    if scan_ids(_db, int(session["active_student_id"])) is True:
        twoFA_code = create_2FA_code()
        
        try:
            send_mail(_db, int(session["active_student_id"]), '2FA', twoFA_code)
            return redirect(url_for('update_account_pin_code'))
        
        except Exception as E:
            website_error = ['2FA Form', E]
            return render_template('Student/2FA.html', validity="Oops... Something went wrong 🤷🏼‍♂️")
    
    else:
        return render_template('Student/2FA.html', validity='This ID is not registered')


# ******************************************************** #
@http.route('/account/update/pin_code/reset')
def update_account_pin_code():
    if "active_student_id" in session:
        _db = sqlite3.connect('Database/kiit_kp_canteen.db')
        
        std_email = get_student_details(_db, int(session["active_student_id"]), 'email')
        msg = f'The 2FA code has been sent to {std_email}'

        return render_template('Student/pin_code_reset.html', 
                            web_page_msg=msg, 
                            student_roll_no=str(session["active_student_id"]))

    else: return redirect(url_for('home', status='logged-out'))

@http.route('/account/update/pin_code/reset', methods=['POST'])
def update_account_pin_code_form():
    global website_error
    global twoFA_code
    
    _db = sqlite3.connect('Database/kiit_kp_canteen.db')
    
    user_2FA = request.form['user_2FA']
    new_pin_code = request.form['new_pin_code']
    confirm_pin_code = request.form['confirm_pin_code']
    
    if str(user_2FA) == str(twoFA_code):
        if str(new_pin_code) == str(confirm_pin_code):
            if (str(new_pin_code).__len__() < 4) and (str(confirm_pin_code).__len__() < 4):
                sql = _db.cursor()

                try:
                    sql.execute(f'''UPDATE student_account 
                                SET pin_code = {str(confirm_pin_code)} 
                                WHERE id={int(session["active_student_id"])};''')
                    _db.commit()

                    send_mail(_db, int(session["active_student_id"]), 'pin_code_update', confirm_pin_code)
                    
                    return render_template('Student/pin_code_reset.html', 
                                            student_roll_no=str(session["active_student_id"]),
                                            web_page_msg='Pin-Code successfully changed. Now you can login.')
                    
                except Exception as E:
                    std_email = get_student_details(_db, int(session["active_student_id"]), 'email')
                    msg = f'The 2FA code has been sent to {std_email}'
                    website_error = ['Resetting user PIN code', E]

                    return render_template('Student/pin_code_reset.html', 
                            web_page_msg=msg, 
                            student_roll_no=str(session["active_student_id"]),
                            status='❌')

            else: return render_template('Student/pin_code_reset.html', 
                                    student_roll_no=str(session["active_student_id"]),
                                    error='Pin Code too short. Min 4 char')

        else: return render_template('Student/pin_code_reset.html', 
                                    student_roll_no=str(session["active_student_id"]),
                                    error='Incorrect Pin Confirmation')
        
    else: return render_template('pin_code_reset.html', 
                                student_roll_no=str(session["active_student_id"]),
                                error='Incorrect 2FA Code')



# ***********************AdminLinks*********************** #
# ******************************************************** #
@http.route('/admin/login')
def admin_login():
    return render_template('Admin/admin_login.html')

@http.route('/admin/login', methods=['POST'])
def admin_login_form():
    global website_error
    
    session["active_admin_ssid"] = str(request.form['ssid'])
    pswd = str(request.form['pswd'])
    
    _db = sqlite3.connect('Database/kiit_kp_canteen.db')
    sql = _db.cursor()
    
    try: 
        sql.execute(f'SELECT Password, Email FROM admin_logins WHERE SSID="{session["active_admin_ssid"]}"')
        login_details = sql.fetchone()
        
        PSWD = str(login_details[0])
        # EMAIL = str(login_details[1])
        
        if pswd == PSWD:
            # admin_2FA_code = create_2FA_code()
            # send_2FA_2_admin(EMAIL, admin_2FA_code)
            return redirect(url_for('admin_2FA'))
                
        else: return render_template('Admin/admin_login.html', 
                                     alert_message='[ Wrong Password ]')
        
    except Exception as E:
        website_error = ['Admin login', E]
        return render_template('Admin/admin_login.html', alert_message='[ Wrong SSID ]')


@http.route('/admin/dashboard/logout')
def admin_logout():
    try: session.pop("active_admin_ssid", None)
    except KeyError: return '<h3 align="center">Unable to logout!'
    
    return redirect(url_for('admin_login', status='logged-out'))


# ******************************************************** #
@http.route('/admin/register')
def admin_register():
    return render_template('Admin/admin_registration.html', 
                           web_page_msg=greeting(),
                           next_bool=False)

@http.route('/admin/register', methods=['POST'])
def admin_register_form():
    global website_error
    
    _db = sqlite3.connect('Database/kiit_kp_canteen.db')
    sql = _db.cursor()
    
    session["active_admin_ssid"] = request.form['ussid']
    EMAIL = request.form['email']
    PSWD = request.form['new_password']
    C_PSWD = request.form['confirm_password']
    MASTER_KEY = request.form['master_key']
    
    if MASTER_KEY != MASTER_PROCESS_KEY:
        return render_template('Admin/admin_registration.html', 
                               error='Invalid Process Key')

    else:
        sql.execute(f"SELECT SSID FROM admin_logins")
        ssid_s = sql.fetchall()

        admin_ssid_s = []

        for ssid in ssid_s:
            admin_ssid_s += [ssid[0]]
        
        if session["active_admin_ssid"] in admin_ssid_s:
            return render_template('Admin/admin_registration.html', 
                                error='[ SSID already in use. ]',
                                status="❌",
                                next_bool=False)
        
        elif PSWD != C_PSWD:
            return render_template('Admin/admin_registration.html',
                                error='[ Wrong confirmation password. ]',
                                status="❌",
                                next_bool=False)
            
        elif (len(PSWD) < 4) and (len(C_PSWD) < 4):
            return render_template('Admin/admin_registration.html',
                                error='[ Password too short. ]',
                                status="❌",
                                next_bool=False)
        
        else:
            register_status = register_admin(_db, session["active_admin_ssid"], PSWD, EMAIL)
            if register_status is True:
                return render_template('Admin/admin_registration.html',
                                    web_page_msg2='Registered, click `NEXT` to authenticate account.',
                                    status='✅',
                                    next_bool=True)
                
            else:
                website_error = ['admin registration', register_status]
                return render_template('Admin/admin_registration.html',
                                    error='[ Registration Failed. ]',
                                    next_bool=False)


# ******************************************************** #
@http.route('/admin/login/authentication')
def authentication():
    global website_error
    global admin_2FA_code

    if "active_admin_ssid" in session:
        admin_2FA_code = pyotp.TOTP('3232323232323232')
        
        try: google_authentication(admin_2FA_code, session["active_admin_ssid"])
        except Exception as E:
            website_error = ['authentication web method', E]
            return render_template('Admin/google_authenticator.html', 
                            error='[ Oops! Something went wrong... 🤷🏻‍♂️]',
                            user=session["active_admin_ssid"])

        return render_template('Admin/google_authenticator.html', 
                            web_page_msg='Scan the QR Code and enter the oAuth code to Activate 2FA',
                            user=session["active_admin_ssid"])
    
    else: return redirect(url_for('admin_register'))

@http.route('/admin/login/authentication', methods=['POST'])
def authenticator_verification():
    global admin_2FA_code

    gAuth_otp = request.form['gAuth']
    if (str(gAuth_otp) == str(admin_2FA_code.now())):
        return redirect(url_for("admin_dashboard"))
    
    else:
        return render_template('Admin/google_authenticator.html', 
                           error='[ Invalid Authentication Code. ]',
                           user=session["active_admin_ssid"])


# ******************************************************** #
@http.route('/admin/login/authentication-AppInstall')
def authenticator_install():
    if "active_admin_ssid" in session:
        return render_template('Admin/gAuth_app_download.html')

    else: return redirect(url_for('admin_register'))

# ******************************************************** #
@http.route('/admin/login/2FA')
def admin_2FA():
    return render_template('Admin/admin_2FA.html')

@http.route('/admin/login/2FA', methods=['POST'])
def admin_2FA_form():
    global admin_2FA_code

    admin_2FA_code = pyotp.TOTP('3232323232323232')
    code = request.form['admin_2FA_code']

    if (str(code) == str(admin_2FA_code.now())):
        return redirect(url_for('admin_dashboard', admin=session["active_admin_ssid"]))
    
    else: return render_template('Admin/admin_2FA.html', validity='[ Wrong 2FA Code given ]')


# ******************************************************** #
@http.route('/admin/login/password-reset/verification')
def admin_pswd_reset_redirector():
    return render_template('Admin/pswd_reset_redirect.html')

@http.route('/admin/login/password-reset/verification', methods=['POST'])
def admin_pswd_reset_redirect_form():
    global website_error
    global admin_2FA_code

    _db = sqlite3.connect('Database/kiit_kp_canteen.db')
    sql = _db.cursor()

    session["active_admin_ssid"] = str(request.form['admin_ssid'])

    try:
        sql.execute("SELECT SSID FROM admin_logins")
        admin_ssid_s = sql.fetchone()[0]

        if str(session["active_admin_ssid"]) in admin_ssid_s:
            return redirect(url_for('admin_pswd_reset'))
        
        elif str(session["active_admin_ssid"]) not in admin_ssid_s:
            return render_template('Admin/pswd_reset_redirect.html',
                               validity='[ Invalid Admin SSID ]')
    
    except Exception as E:
        website_error = ['admin pswd-reset redirector', E]
        return render_template('Admin/pswd_reset_redirect.html',
                               validity='[ Unable to process. Myabe wrong SSID given. ]')


# ******************************************************** #
@http.route('/admin/login/password-reset')
def admin_pswd_reset():
    return render_template('Admin/admin_password_reset.html',
                           web_page_msg=greeting())

@http.route('/admin/login/password-reset', methods=['POST'])
def admin_pswd_reset_form():
    global website_error
    global admin_2FA_code
    
    admin_2FA_code = pyotp.TOTP('3232323232323232')

    _db = sqlite3.connect('Database/kiit_kp_canteen.db')
    sql = _db.cursor()
    
    admin_2FA = request.form['admin_2FA']
    new_pswd = request.form['new_password']
    re_new_pswd = request.form['confirm_password']
    
    if str(admin_2FA) != str(admin_2FA_code.now()):
        return render_template('Admin/admin_password_reset.html', 
                               error='[ Wrong 2FA Code ]')
    
    elif (len(new_pswd) < 4) and (len(re_new_pswd) < 4):
        return render_template('Admin/admin_password_reset.html', 
                               error='[ Password is too short. Min 6 chars ]')

    elif new_pswd != re_new_pswd:
        return render_template('Admin/admin_password_reset.html',
                               error='[ Password confirmation failed ]')
    
    else:
        ssid = session["active_admin_ssid"]
        sql.execute(f"UPDATE admin_logins SET Password='{re_new_pswd}' WHERE SSID={ssid}")
        _db.commit()
        
        return render_template('Admin/admin_password_reset.html',
                               web_page_msg2='Password successfully updated.',
                               status='✅')


# ******************************************************** #
@http.route('/admin/dashboard')
def admin_dashboard():
    if "active_admin_ssid" in session:
        return render_template('Admin/admin_dashboard.html',
                               web_page_msg=greeting())
    
    else: return redirect(url_for('admin_login', status='logged-out'))


# ******************************************************** #
@http.route('/admin/developer/database/database_file/view/student')
def view_student_database():
    global website_error

    if "active_admin_ssid" in session:
        _db = sqlite3.connect('Database/kiit_kp_canteen.db')

        try:
            try: std_acnt_data = read_database_file(_db, 'account')
            except Exception: std_acnt_data = 'No data found'
            
            try: std_info_data = read_database_file(_db, 'info')
            except Exception: std_info_data = 'No data found'

            return render_template('Admin/admin_STdatabase_viewer.html', 
                                    student_account_info=std_acnt_data,
                                    student_info=std_info_data)
            
        except Exception as E:
            website_error = ['reading the database (view_student_database web method)', E]
            
            return render_template('Admin/admin_STdatabase_viewer.html', 
                                   page_error='Oops something went wrong 😬')

    else: return redirect(url_for('admin_login', status='logged-out'))

@http.route('/admin/developer/database/database_file/view/admin')
def view_admin_database():
    global website_error
    
    _db = sqlite3.connect('Database/kiit_kp_canteen.db')
    
    if "active_admin_ssid" in session:
        login_details = read_database_file(_db, 'admin_logins', ['SSID', 'Passwoord', 'Email'])
        if type(login_details) is pandas.DataFrame:
            return render_template('Admin/admin_ADdatabase_viewer.html',
                                   admin_login_details=login_details)
        
        elif type(login_details) is Exception:
            website_error = ['view_admin_database web method', login_details]
            return render_template('Admin/admin_ADdatabase_viewer.html',
                                   page_error='Unable to show admin database.')

    else: return redirect(url_for('admin_login', status='logged-out'))


# ******************************************************** #
@http.route('/admin/developer/database/database_file/edit')
def edit_database():
    if "active_admin_ssid" in session:
        return render_template('Admin/admin_database_editor.html', 
                               query_result='No query result(s)')
    
    else: return redirect(url_for('admin_login', status='logged-out'))

@http.route('/admin/developer/database/database_file/edit', methods=['POST'])
def database_editor():
    global website_error

    query = str(request.form['query'])
    query_keywords = query.split(' ')

    if str(query_keywords[0]) == 'SELECT':
        _db = sqlite3.connect('Database/kiit_kp_canteen.db')
        _sql = _db.cursor()
        
        try:
            _sql.execute(query)
            data = _sql.fetchall()
            
            _sql.close()
            _db.close()
        
        except Exception as E:
            website_error = ['database_editor web method', E]
            return render_template('Admin/admin_database_editor.html', 
                                   query_result='No data available to show.')

        if query_keywords[1] == '*':
            return render_template('Admin/admin_database_editor.html', 
                                   long_data=data)
            
        elif (query_keywords[1] == '*') and ('WHERE' in query_keywords):
            final_data = []
            for d_val in data[0]:
                final_data += [d_val]
            
            return render_template('Admin/admin_database_editor.html',
                                   query_result=final_data)

        else:
            return render_template('Admin/admin_database_editor.html', 
                                   long_data=data)  

    elif str(query_keywords[0]) == 'DELETE':
        _db = sqlite3.connect('Database/kiit_kp_canteen.db')
        _sql = _db.cursor()

        try:
            _sql.execute(query)
            _db.commit()
            
            _sql.close()
            _db.close()

            return render_template('Admin/admin_database_editor.html',
                    query_result='Query\command successfully executed.')

        except Exception as E:
            website_error = ['database_editor web method', E]
            return render_template('Admin/admin_database_editor.html',
                                   page_error='[ Unable to execute the query. ]')

    elif str(query_keywords[0]) == 'UPDATE':
        return render_template('Admin/admin_database_editor.html',
                            query_result='Update feature is not supported for now.')

    elif 'remove user' in query:
        user_id = int(query_keywords[-1])

        _db = sqlite3.connect('Database/kiit_kp_canteen.db')
        _sql = _db.cursor()

        try:
            usid = get_student_details(_db, user_id, 'usid')
            
            try:
                _sql.execute(f'DELETE FROM student_info WHERE id={int(user_id)}')
                _sql.execute(f'DELETE FROM student_account WHERE id={int(user_id)}')
            
            except Exception as E:
                website_error = ['database editor web method', E]
                return render_template('Admin/admin_database_editor.html',
                                   page_error=f'[ Unable to remove user with id={user_id} from databse file. ]')

            try: os.remove(f"Database/logs/{usid}.txt")
            except Exception as E:
                website_error = ['database editor web method', E]
                return render_template('Admin/admin_database_editor.html',
                                   page_error=f'[ Unable to remove log of user with id={user_id}. ]')

            return render_template('Admin/admin_database_editor.html',
                                   query_result=f'User {user_id} successfully removed.')

        except Exception as E:
            website_error = ['database editor web method', E]
            return render_template('Admin/admin_database_editor.html',
                                   page_error=f'[ Unable to remove user with id={user_id}. ]')

        finally: 
            _sql.close()
            _db.close()

    else:
        _db = sqlite3.connect('Database/kiit_kp_canteen.db')
        _sql = _db.cursor()

        try:
            _sql.execute(query)
            _db.commit()
            
            _sql.close()
            _db.close()
            
            return render_template('Admin/admin_database_editor.html',
                                   query_result='Query successfully executed.')

        except Exception as E:
            website_error = ['database_editor web method', E]
            return render_template('Admin/admin_database_editor.html',
                                   page_error='[ Unable to execute query. ]')


# ******************************************************** #
@http.route('/admin/developer/database/logs/view')
def admin_log_view():
    if "active_admin_ssid" in session:
        log_names = [name[:16] for name in os.listdir('Database/logs')]

        return render_template('Admin/admin_STlog_viewer.html', 
                                web_page_msg=greeting(),
                                logs=log_names)

    else: return redirect(url_for('admin_login', status='logged-out'))
    
@http.route('/admin/developer/database/logs/view', methods=['POST'])
def admin_log_list():
    global website_error
    global std_log_details
    
    log_name = str(request.form['log_name'])
    
    try:
        with open(f'Database/logs/{log_name}.txt', 'r') as log_file:
            name_line = log_file.readlines(1)
            std_log_details = log_file.read()

        name_line = name_line[0].split('\n')[0]
        std_full_name = str(name_line.split(' ')[-2] + ' ' + name_line.split(' ')[-1])
        
        return redirect(url_for('admin_log_context_viewer', std_name=std_full_name))

    except Exception as E:
        website_error = ['log context viewer', E]
        return render_template('Admin/admin_STlog_viewer.html', 
                                error="[ Opps! Something's wrong. Can't read log file. ]")


# ******************************************************** #
@http.route('/admin/developer/database/logs/view/<std_name>')
def admin_log_context_viewer(std_name):
    global website_error
    global std_log_details

    if "active_admin_ssid" in session:
        return render_template('Admin/log_context_viewer.html', 
                                web_page_msg=greeting(),
                                std_name=str(std_name),
                                log_details=str(std_log_details))
    
    else: return redirect(url_for('admin_login', status='logged-out'))


# ******************************************************** #
@http.route('/admin/developer/backend/error')
def developer_error_page(): 
    if "active_admin_ssid" in session:
        try:
            error_message = f'Error in {website_error[0]} function.\nError: {website_error[1]}'
            return render_template('Admin/admin_developer_error.html', dev_error_message=error_message)
        
        except Exception:
            return render_template('Admin/admin_developer_error.html', dev_error_message='No Error Found Yet')

    else: return redirect(url_for('admin_login', status='logged-out'))


# ******************************************************** #
@http.route('/admin/developer/server_shutdown')
def server_shutdown_2FA(): 
    if "active_admin_ssid" in session: return render_template('Admin/admin_2FA.html')
    else: return redirect(url_for('admin_login', status='logged-out'))

@http.route('/admin/developer/server_shutdown', methods=['POST'])
def server_shutdown_2FA_form():
    global admin_2FA_code
    global website_error
    
    admin_2FA_code = pyotp.TOTP('3232323232323232')
    
    code = request.form['admin_2FA_code']
    if (str(code) == str(admin_2FA_code.now())):
        
        try: quit()
        except KeyboardInterrupt as KI:
            website_error = ['shutting down the server', KI]
            exit()
        
        except Exception as E:
            website_error = ['shutting down the server', E]
            return render_template('Admin/admin_2FA.html', validity='Oops something went wrong 😬')
            
    else: return render_template('Admin/admin_2FA.html', validity='[ Invalid 2FA Code ]')



if __name__ == '__main__':

    http.run(port=PORT, debug=DEBUG)