"""
CanteenFastCard Website backend program
"""

import os
import pandas
import sqlite3

from flask import Flask, url_for, redirect, render_template, request
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


# global variables
student_roll_no = int()
twoFA_code = str()
student_login = bool(False)

website_error = list()
std_log_details = str()

admin_2FA_code = str()
admin_ssid = str()
admin_login_status = bool(False)

http = Flask(__name__)
# http.config['SECRET_KEY'] = '3d9efc4wa651728'



# **********************StudentLinks********************** #
# ******************************************************** #
@http.route('/')
def home_redirecter():
    return redirect(url_for('home'))


# ******************************************************** #
@http.route('/home')
def home():
    global student_roll_no, student_login
    global admin_login_status
    
    student_login = False
    student_roll_no = int()
    
    admin_login_status = False

    return render_template('Student/index.html')

@http.route('/home', methods=['POST'])
def student_id_info():
    _db = sqlite3.connect('Database/kiit_kp_canteen.db')

    global student_roll_no, student_login
    global website_error
    
    student_roll_no = int(request.form['std_id'])
    std_id_pin = request.form['std_id_pin']
    
    try:
        if scan_ids(_db, int(student_roll_no)) is True:
            if get_student_details(_db, int(student_roll_no), 'pin_code') == std_id_pin:
                
                student_login = True
                return redirect(url_for('dashboard', user=str(student_roll_no)))

            else: return render_template('Student/index.html', alert_message='[ Invalid Pin Code ]')
        else: return redirect(url_for('auto_id_registration'))

    except Exception as E:
        website_error = ['Home page post function', E]
        return render_template('Student/index.html', alert_message='[ Unable to verify ]')


# ******************************************************** #
@http.route('/id/scan')
def scan_std_id():
    global student_roll_no, student_login
    global website_error

    _db = sqlite3.connect('Database/kiit_kp_canteen.db')
    
    try:
        student_roll_no = scan()

        if scan_ids(_db, int(student_roll_no)): 
            student_login=True
            return redirect(url_for('dashboard', user=str(student_roll_no)))

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
    global student_roll_no, student_login

    _db = sqlite3.connect('Database/kiit_kp_canteen.db')

    name = request.form['std_name'] #.replace(' ', '_')
    email = request.form['email']
    id_pin_code = request.form['pin_code']
    init_amount = request.form['initial_amount']
    
    if len(id_pin_code) < 0:
        return render_template('Student/auto_id_registration.html', 
                               alert_message='[ Pin Code too short! ]')

    elif int(init_amount) < 30:
        return render_template('Student/auto_id_registration.html', 
                                alert_message='[ Minimum amount required is Rs.30]')

    else:
        try:
            register_student(_db, int(student_roll_no), id_pin_code,
                            int(init_amount), [name, email])
            
            student_login = True
            
            return redirect(url_for('dashboard', user=str(student_roll_no)))

        except Exception as E:
            global website_error
            
            website_error = ['register', E]
            return render_template('Student/auto_id_registration.html', 
                                alert_message='[ Unable to register this ID ]')


# ******************************************************** #
@http.route('/id/manual_registration')
def manual_id_registration():
    return render_template('Student/manual_id_registration.html')

@http.route('/id/manual_registration', methods=['POST'])
def manual_id_registration_form():
    global student_roll_no, student_login

    _db = sqlite3.connect('Database/kiit_kp_canteen.db')

    student_roll_no = request.form['std_roll_no']
    name = request.form['std_name']#.replace(' ', '_')
    email = request.form['email']
    id_pin_code = request.form['pin_code']
    init_amount = request.form['initial_amount']
    
    if len(id_pin_code) < 0:
        return render_template('Student/manual_id_registration.html', 
                               alert_message='[ Pin Code too short! ]')
    
    elif int(init_amount) < 30:
        return render_template('Student/manual_id_registration.html', 
                                alert_message='[ Minimum amount required is Rs.30]')
    
    else:
        try:
            register_student(_db, int(student_roll_no), id_pin_code,
                            int(init_amount), [name, email])
            
            student_login = True
            
            return redirect(url_for('dashboard', user=str(student_roll_no)))

        except Exception as E:
            global website_error
            
            website_error = ['register', E]
            return render_template('Student/manual_id_registration.html', 
                                alert_message='[ Unable to register this ID ]')


# ******************************************************** #
@http.route('/dashboard/<user>')
def dashboard(user):
    global student_login
    
    if student_login is True:
        return render_template('Student/dashboard.html', 
                            web_page_msg=f'Hey there: {str(user)}. Welcome!', 
                            student_roll_no=str(user))
        
    else: return redirect(url_for('home'))


# ******************************************************** #
@http.route('/account/payment')
def payment():
    global student_roll_no, student_login
    
    if student_login is True:
        return render_template('Student/payment.html', 
                            web_page_msg=f'Hey there: {str(student_roll_no)}. Welcome!', 
                            student_roll_no=str(student_roll_no))
    
    else: return redirect(url_for('home'))

@http.route('/account/payment', methods=['POST'])
def payment_form():
    global student_roll_no
    global website_error
    
    _db = sqlite3.connect('Database/kiit_kp_canteen.db')
    amount_to_pay = request.form['amount_to_pay']

    try:
        debit_balance(_db, int(amount_to_pay), int(student_roll_no))
        return render_template('Student/payment.html', 
                               web_page_msg=f'Hey there: {str(student_roll_no)}. Welcome!',
                               student_roll_no=str(student_roll_no),
                               debit_status='✅')
    
    except Exception as E:
        website_error = ['payment form', E]
        return render_template('Student/payment.html', 
                               web_page_msg=f'Hey there: {str(student_roll_no)}. Welcome!',
                               student_roll_no=str(student_roll_no), 
                               debit_status='Unable to do the transaction')


# ******************************************************** #
@http.route('/account/update/balance')
def update_account_balance():
    global student_roll_no, student_login
    
    if student_login is True:
        return render_template('Student/update_amount.html', 
                            web_page_msg=f'Hey there: {str(student_roll_no)}. Welcome!', 
                            student_roll_no=str(student_roll_no))
        
    else: return redirect(url_for('home'))

@http.route('/account/update/balance', methods=['POST'])
def update__account_balance_form():
    global student_roll_no
    global website_error
    
    _db = sqlite3.connect('Database/kiit_kp_canteen.db')
    amount_to_pay = request.form['amount_to_update']

    try:
        update_balance(_db, int(amount_to_pay), int(student_roll_no))
        return render_template('Student/update_amount.html', 
                               web_page_msg=f'Hey there: {str(student_roll_no)}. Welcome!',
                               student_roll_no=str(student_roll_no),
                               update_status='✅')
    
    except Exception as E:
        website_error = ['payment form', E]
        return render_template('Student/update_amount.html', 
                               web_page_msg=f'Hey there: {str(student_roll_no)}. Welcome!',
                               student_roll_no=str(student_roll_no),
                               update_status='Unable to do the transaction')


# ******************************************************** #
@http.route('/account/check_balance')
def check_balance():
    global student_roll_no, student_login

    if student_login is True:
        _db = sqlite3.connect('Database/kiit_kp_canteen.db')
        left_amount = get_student_details(_db, int(student_roll_no), 'amount')
        
        return render_template('Student/balance_check.html',
                               web_page_msg=f'Hey there: {str(student_roll_no)}. Welcome!',
                               student_roll_no=student_roll_no, 
                               amount=f'Left Amount: Rs. {str(left_amount)}')
        
    else: return redirect(url_for('home'))


# ******************************************************** #
@http.route('/account/transaction/view')
def view_log():
    global student_roll_no, student_login
    global website_error

    if student_login is True:
        try:
            _db = sqlite3.connect('Database/kiit_kp_canteen.db')
            std_log_name = get_student_details(_db, int(student_roll_no), 'usid')
            
            with open(f'Database/logs/{std_log_name}.txt', 'r') as log_file:
                std_transaction_details = log_file.read()
                
            return render_template('Student/log_viewer.html', 
                                   web_page_msg=f'Hey there: {str(student_roll_no)}. Welcome!',
                                   content=str(std_transaction_details))
        
        except Exception as E:
            website_error = ['view_log web method', E]
            return render_template('Student/dashboard.html', web_page_msg="Oops... Something went wrong 🤷🏼‍♂️")
        
    else: return redirect(url_for('home'))


# ******************************************************** #
@http.route('/account/transaction/send_log')
def send_transaction_log():
    global student_roll_no, student_login
    global website_error
    
    if student_login is True:
        _db = sqlite3.connect('Database/kiit_kp_canteen.db')
        
        try:
            std_email = get_student_details(_db, int(student_roll_no), 'email')

            send_mail(_db, int(student_roll_no), 'log')
            return render_template('Student/transaction_log_sender.html', 
                                   web_page_msg=f'Hey there: {str(student_roll_no)}. Welcome!',
                                   status=f"Log file Sent to {std_email}")
        
        except Exception as E:
            website_error = ['Sending Log (send_transaction_log web method)', E]
            return render_template('Student/dashboard.html', web_page_msg="Oops... Something went wrong 🤷🏼‍♂️")
        
    else: return redirect(url_for('home'))


# ******************************************************** #
@http.route('/account/update/pin_code/2FA')
def twoFA():
    return render_template('Student/2FA.html')

@http.route('/account/update/pin_code/2FA', methods=['POST'])
def twoFA_form():
    global student_roll_no, student_login
    global website_error
    global twoFA_code

    _db = sqlite3.connect('Database/kiit_kp_canteen.db')
    student_roll_no = int(request.form['std_roll_no_pcr'])
    
    if scan_ids(_db, int(student_roll_no)) is True:
        twoFA_code = create_2FA_code()
        student_login = True
        
        try:
            send_mail(_db, int(student_roll_no), '2FA', twoFA_code)
            return redirect(url_for('update_account_pin_code'))
        
        except Exception as E:
            website_error = ['2FA Form', E]
            return render_template('Student/2FA.html', validity="Oops... Something went wrong 🤷🏼‍♂️")
    
    else:
        return render_template('Student/2FA.html', validity='Is ID is not registered')


# ******************************************************** #
@http.route('/account/update/pin_code/reset')
def update_account_pin_code():
    global student_roll_no, student_login
    
    if student_login is True:
        _db = sqlite3.connect('Database/kiit_kp_canteen.db')
        
        std_email = get_student_details(_db, int(student_roll_no), 'email')
        msg = f'The 2FA code has been sent to {std_email}'

        return render_template('Student/pin_code_reset.html', 
                            web_page_msg=msg, 
                            student_roll_no=str(student_roll_no))

    else: return redirect(url_for('home'))

@http.route('/account/update/pin_code/reset', methods=['POST'])
def update_account_pin_code_form():
    global student_roll_no
    global website_error
    global twoFA_code
    
    _db = sqlite3.connect('Database/kiit_kp_canteen.db')
    
    user_2FA = request.form['user_2FA']
    new_pin_code = request.form['new_pin_code']
    confirm_pin_code = request.form['confirm_pin_code']
    
    if str(user_2FA) == str(twoFA_code):
        if str(new_pin_code) == str(confirm_pin_code):
            sql = _db.cursor()

            try:
                sql.execute(f'''UPDATE student_account 
                            SET pin_code = {str(confirm_pin_code)} 
                            WHERE id={int(student_roll_no)};''')
                _db.commit()

                send_mail(_db, int(student_roll_no), 'pin_code_update', confirm_pin_code)
                
                return render_template('Student/pin_code_reset.html', 
                                        student_roll_no=str(student_roll_no),
                                        web_page_msg='Pin-Code successfully changed. Now you can login.')
                
            except Exception as E:
                std_email = get_student_details(_db, int(student_roll_no), 'email')
                msg = f'The 2FA code has been sent to {std_email}'
                website_error = ['Resetting user PIN code', E]

                return render_template('Student/pin_code_reset.html', 
                           web_page_msg=msg, 
                           student_roll_no=str(student_roll_no),
                           status='Unable to reset pin code')
                
        else: return render_template('Student/pin_code_reset.html', 
                                    student_roll_no=str(student_roll_no),
                                    web_page_msg='Incorrect Pin Confirmation')
        
    else: return render_template('pin_code_reset.html', 
                                student_roll_no=str(student_roll_no),
                                web_page_msg='Incorrect 2FA Code')



# ***********************AdminLinks*********************** #
# ******************************************************** #
@http.route('/admin/login')
def admin_login():
    global admin_login_status
    
    admin_login_status = False
    return render_template('Admin/admin_login.html')

@http.route('/admin/login', methods=['POST'])
def admin_login_form():
    global website_error
    global admin_2FA_code, admin_login_status
    
    ssid = str(request.form['ssid'])
    pswd = str(request.form['pswd'])
    
    _db = sqlite3.connect('Database/kiit_kp_canteen.db')
    sql = _db.cursor()
    
    try: 
        sql.execute(f'SELECT Password, Email FROM admin_logins WHERE SSID="{ssid}"')
        login_details = sql.fetchone()
        
        PSWD = str(login_details[0])
        EMAIL = str(login_details[1])
        
        if pswd == PSWD:
            admin_2FA_code = create_2FA_code()

            try:
                send_2FA_2_admin(EMAIL, admin_2FA_code)
                return redirect(url_for('admin_2FA'))
                # admin_login_status = True
                # return redirect(url_for('admin_dashboard'))
            
            except Exception as E:
                website_error = ['admin login form', E]
                return render_template('Admin/admin_login.html', 
                                        alert_message='[ Unable to send 2FA code. ]')
                
        else: return render_template('Admin/admin_login.html', 
                                     alert_message='[ Wrong Password ]')
        
    except Exception as E:
        website_error = ['Admin login', E]
        return render_template('Admin/admin_login.html', alert_message='[ Wrong SSID ]')


# ******************************************************** #
@http.route('/admin/login/register')
def admin_register():
    return render_template('Admin/admin_registration.html', 
                           web_page_msg=greeting())

@http.route('/admin/login/register', methods=['POST'])
def admin_register_form():
    global website_error
    
    _db = sqlite3.connect('Database/kiit_kp_canteen.db')
    sql = _db.cursor()
    
    SSID = request.form['ussid']
    EMAIL = request.form['email']
    PSWD = request.form['new_password']
    C_PSWD = request.form['confirm_password']
    
    sql.execute(f"SELECT SSID FROM admin_logins")
    ssid_s = sql.fetchall()

    admin_ssid_s = []

    for ssid in ssid_s:
        admin_ssid_s += [ssid[0]]
    
    if SSID in admin_ssid_s:
        return render_template('Admin/admin_registration.html', 
                               error='[ SSID already in use. ]',
                               status="❌")
    
    elif PSWD != C_PSWD:
        return render_template('Admin/admin_registration.html',
                               error='[ Wrong confirmation password. ]',
                               status="❌")
        
    elif (len(PSWD) < 4) and (len(C_PSWD) < 4):
        return render_template('Admin/admin_registration.html',
                               error='[ Password too short. ]',
                               status="❌")
    
    else:
        register_status = register_admin(_db, SSID, PSWD, EMAIL)
        if register_status is True:
            return render_template('Admin/admin_registration.html',
                                   web_page_msg='Now you can login.',
                                   status='✅')
            
        else:
            website_error = ['admin registration', register_status]
            return render_template('Admin/admin_registration.html',
                                   error='[ Registration Failed. ]')


# ******************************************************** #
@http.route('/admin/login/2FA')
def admin_2FA():
    return render_template('Admin/admin_2FA.html')

@http.route('/admin/login/2FA', methods=['POST'])
def admin_2FA_form():
    global admin_2FA_code
    global admin_login_status
    
    code = request.form['admin_2FA_code']
    if code == admin_2FA_code:
        admin_login_status = True
        return redirect(url_for('admin_dashboard'))
    
    else: return render_template('Admin/admin_2FA.html', validity='[ Wrong 2FA Code given ]')


# ******************************************************** #
@http.route('/admin/login/password-reset/redirector')
def admin_pswd_reset_redirector():
    return render_template('Admin/pswd_reset_redirect.html')

@http.route('/admin/login/password-reset/redirector', methods=['POST'])
def admin_pswd_reset_redirect_form():
    global website_error
    global admin_ssid, admin_2FA_code

    _db = sqlite3.connect('Database/kiit_kp_canteen.db')
    sql = _db.cursor()

    admin_ssid = str(request.form['admin_ssid'])

    try:
        sql.execute(f"SELECT Email FROM admin_logins WHERE SSID='{admin_ssid}'")
        admin_email = sql.fetchone()[0]

        admin_2FA_code = create_2FA_code(code_type='alpha')

        send_2FA_2_admin(str(admin_email), admin_2FA_code, 'pswd-reset')
        return redirect(url_for('admin_pswd_reset'))
    
    except Exception as E:
        website_error = ['admin pswd-reset redirector', E]
        return render_template('Admin/pswd_reset_redirect.html',
                               validity='[ Unable to process. Myabe wrong SSID given. ]')


# ******************************************************** #
@http.route('/admin/login/pswd-reset')
def admin_pswd_reset():
    return render_template('Admin/admin_password_reset.html',
                           web_page_msg=greeting())

@http.route('/admin/login/pswd-reset', methods=['POST'])
def admin_pswd_reset_form():
    global website_error
    global admin_ssid, admin_2FA_code

    _db = sqlite3.connect('Database/kiit_kp_canteen.db')
    sql = _db.cursor()
    
    admin_2FA = request.form['admin_2FA']
    new_pswd = request.form['new_password']
    re_new_pswd = request.form['confirm_password']
    
    if str(admin_2FA) != str(admin_2FA_code):
        return render_template('Admin/admin_password_reset.html', 
                               error='[ Wrong 2FA Code ]')
    
    elif (len(new_pswd) < 6) and (len(re_new_pswd) < 6):
        return render_template('Admin/admin_password_reset.html', 
                               error='[ Password is too short. Min 6 chars ]')

    elif new_pswd != re_new_pswd:
        return render_template('Admin/admin_password_reset.html',
                               error='[ Password confirmation failed ]')
    
    else:
        sql.execute(f"UPDATE admin_logins SET Password='{re_new_pswd}' WHERE SSID='{admin_ssid}'")
        _db.commit()
        
        return render_template('Admin/admin_password_reset.html',
                               web_page_msg='Password successfully updated.',
                               status='✅')


# ******************************************************** #
@http.route('/admin/dashboard')
def admin_dashboard():
    global admin_login_status
    
    if admin_login_status is True:
        return render_template('Admin/admin_dashboard.html',
                               web_page_msg=greeting())
    
    else: return redirect(url_for('admin_login'))


# ******************************************************** #
@http.route('/admin/developer/database/database_file/view/student')
def view_student_database():
    global admin_login_status
    global website_error

    if admin_login_status is True:
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

    else: return redirect(url_for('admin_login'))

@http.route('/admin/developer/database/database_file/view/admin')
def view_admin_database():
    global admin_login_status
    global website_error
    
    _db = sqlite3.connect('Database/kiit_kp_canteen.db')
    
    if admin_login_status is True:
        login_details = read_database_file(_db, 'admin_logins', ['SSID', 'Passwoord', 'Email'])
        if type(login_details) is pandas.DataFrame:
            return render_template('Admin/admin_ADdatabase_viewer.html',
                                   admin_login_details=login_details)
        
        elif type(login_details) is Exception:
            website_error = ['view_admin_database web method', login_details]
            return render_template('Admin/admin_ADdatabase_viewer.html',
                                   page_error='Unable to show admin database.')

    else: return redirect(url_for('admin_login'))


# ******************************************************** #
@http.route('/admin/developer/database/database_file/edit')
def edit_database():
    global admin_login_status
    
    if admin_login_status is True:
        return render_template('Admin/admin_database_editor.html', 
                               query_result='No query result(s)')
    
    else: return redirect(url_for('admin_login'))

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
                                   query_result=final_data,
                                   long_data=[])
            
        else:
            final_data = {}
            
            select_index = query.index('SELECT')
            from_index = query.index('FROM')
            cols = query[select_index+1:from_index]
            
            for index, col in enumerate(cols):
                final_data[col.removesuffix(',')] = data[0][index]

            return render_template('Admin/admin_database_editor.html',
                                   long_data=final_data)  

    elif str(query_keywords[0]) == 'DELETE':
        _db = sqlite3.connect('Database/kiit_kp_canteen.db')
        _sql = _db.cursor()

        try: roll_no = int(query[-1])
        except Exception: roll_no = int(query[-1].split('=')[-1])

        try:
            _sql.execute(query)
            _db.commit()

            _sql.execute(f"DELETE FROM student_account WHERE id={roll_no}")
            _db.commit()
            
            _sql.close()
            _db.close()
            
            std_uid = get_student_details(_db, int(roll_no), 'usid')
            
            try: 
                os.remove(f'Database/logs/{std_uid}')
                return render_template('Admin/admin_database_editor.html',
                        query_result='Query successfully executed. Data deleted from database AWA Log Dir.')


            except Exception as E:
                website_error = ['database_editor deleted section', E]
                return render_template('Admin/admin_database_editor.html',
                        query_result='Query successfully executed. Data deleted from the database only.')

        except Exception as E:
            website_error = ['database_editor web method', E]
            return render_template('Admin/admin_database_editor.html', 
                                   page_error='[ Unable to execute the query. ]')

    elif str(query_keywords[0]) == 'UPDATE':
        _db = sqlite3.connect('Database/kiit_kp_canteen.db')
        _sql = _db.cursor()

        try:
            _sql.execute(query)
            db.commit()
            
            _sql.close()
            _db.close()

            return render_template('Admin/admin_database_editor.html',
                                   query_result='Data successfully updated.')

        except Exception as E:
            website_error = ['database_editor web method', E]
            return render_template('Admin/admin_database_editor.html', 
                                   page_error='[ Error updating database. ]')

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
    global admin_login_status

    if admin_login_status is True:
        log_names = [name[:16] for name in os.listdir('Database/logs')]

        return render_template('Admin/admin_STlog_viewer.html', 
                                web_page_msg=greeting(),
                                logs=log_names)

    else: return redirect(url_for('admin_login'))
    
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
    global admin_login_status

    if admin_login_status is True:
        return render_template('Admin/log_context_viewer.html', 
                                web_page_msg=greeting(),
                                std_name=str(std_name),
                                log_details=str(std_log_details))
    
    else: return redirect(url_for('admin_login'))


# ******************************************************** #
@http.route('/admin/developer/backend/error')
def developer_error_page():
    global admin_login_status
    
    if admin_login_status is True:
        try:
            error_message = f'Error in {website_error[0]} function.\nError: {website_error[1]}'
            return render_template('Admin/admin_developer_error.html', dev_error_message=error_message)
        
        except Exception:
            return render_template('Admin/admin_developer_error.html', dev_error_message='No Error Found Yet')

    else: return redirect(url_for('admin_login'))


# ******************************************************** #
@http.route('/server_shutdown')
def server_shutdown():
    global admin_2FA_code, admin_login_status
    global website_error

    if admin_login_status is True:
        admin_2FA_code = create_2FA_code(16, 'hy')
        try:
            send_2FA_2_admin(MASTER_2FA_EMAIL, admin_2FA_code, 'shutting down the server')
            return redirect(url_for('server_shutdown_2FA'))
        
        except Exception as E:
            website_error = ['sending 2FA for server shutdown', E]
            return '''<h1 align="center">Oops!! Something went wrong 😬
<br><a href="/admin/dashboard">Go Back</a></h1>'''

    else: return redirect(url_for('admin_login'))


# ******************************************************** #
@http.route('/admin/developer/server_shutdown/2FA')
def server_shutdown_2FA():
    global admin_login_status
    
    if admin_login_status is True: return render_template('Admin/admin_2FA.html')
    else: return redirect(url_for('admin_login'))

@http.route('/admin/developer/server_shutdown/2FA', methods=['POST'])
def server_shutdown_2FA_form():
    global admin_2FA_code
    global website_error
    
    code = request.form['admin_2FA_code']
    if str(code) == admin_2FA_code:
        
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