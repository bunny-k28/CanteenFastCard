import os
import pyotp
import pandas
import CFC.scanner as scanner

from flask import Flask
from pyparsing import Any
from dotenv import load_dotenv
from datetime import timedelta
from flask import request, session
from flask_login import LoginManager
from flask_login import login_user, logout_user, login_required
from flask import render_template as render, url_for as to, redirect

from CFC import *


# Web App Settings
cfc = Flask(__name__, static_folder="/site/static", template_folder="./site/templates/")
cfc.permanent_session_lifetime = timedelta(minutes=10)
cfc.secret_key = '3d9efc4wa651728'

cfc.config['WEBSITE_ERRORS'] =  list()
cfc.config['ADMIN_2FA_CODE'] = Any

login_manager = LoginManager()
login_manager.init_app(cfc)


# website parameters (variables from env file)
load_dotenv('site_settings.env')
PORT = os.environ.get('PORT')
HOST = os.environ.get('HOST')
DEBUG = os.environ.get('DEBUG')

MASTER_2FA_EMAIL = os.environ.get('MASTER_2FA_EMAIL')
MASTER_PRODUCT_KEY = os.environ.get('MASTER_PRODUCT_KEY')
MASTER_PROCESS_KEY = os.environ.get('MASTER_PROCESS_KEY')


@login_manager.user_loader
def load_user(user_id):
    return db_session.query(Student).get(user_id)


# **********************Student Routes********************** #
@cfc.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render('students/index.html')

    if request.method == 'POST':
        session["active_student_id"] = int(request.form['std_id'])
        
        try:
            if scan_ids(int(session["active_student_id"])):
                if get_student_details(int(session["active_student_id"]), 'pin') == int(request.form['std_id_pin']):
                    user = db_session.query(Student).filter_by(usid=session["active_student_id"]).first()
                    login_user(user)

                    return redirect(to('dashboard', user=str(session["active_student_id"])))

                else: return render('students/index.html', alert_message='[ Invalid Pin Code ]')
            else: return redirect(to('autoIdRegistration'))

        except Exception as E:
            cfc.config['WEBSITE_ERRORS'] += ('Home page post function', E)
            return render('students/index.html', alert_message='[ Unable to verify ]')


@cfc.route('/id/scan')
def login_by_scan():
    try: 
        session["active_student_id"] = scanner.scan()
        if scan_ids(int(session["active_student_id"])):
            user = db_session.query(Student).filter_by(usid=session["active_student_id"]).first()
            login_user(user)

            return redirect(to('dashboard', user=str(session["active_student_id"])))

        else: return redirect(to('autoIdRegistration'))

    except Exception as E:
        cfc.config['WEBSITE_ERRORS'] += ('scanning ID', E)
        return render('students/index.html', alert_message="Unable to scan the ID Card")


@cfc.route('/dashboard/logout')
def logout():
    session.clear()

    try: logout_user()
    except Exception: pass

    return redirect(to('index', status='logged-out'))


@cfc.route('/id/auto_registration', methods=['GET', 'POST'])
def autoIdRegistration():
    if request.method == 'GET':
        return render('students/auto_id_registration.html', 
                        alert_message='[ Not Register! Register your ID here ]')

    if request.method == 'POST':
        name = request.form['std_name'] #.replace(' ', '_')
        email = request.form['email']
        pin = request.form['pin_code']
        init_amount = request.form['initial_amount']
        master_key = int(request.form['master_product_key'])
        
        if master_key != int(MASTER_PRODUCT_KEY):
            return render('students/auto_id_registration.html', 
                          alert_message='Invalid Master Product Key.')

        else:
            if len(pin) < 4:
                return render('students/auto_id_registration.html', 
                              alert_message='[ Pin Code too short! ]')

            elif int(init_amount) < 30:
                return render('students/auto_id_registration.html', 
                              alert_message='[ Minimum amount required is Rs.30]')

            else:
                try:
                    register_student(int(session["active_student_id"]), pin,
                                    int(init_amount), name=name, email=email)

                    user = db_session.query(Student).filter_by(usid=session["active_student_id"]).first()
                    login_user(user)

                    return redirect(to('dashboard', user=str(session["active_student_id"])))

                except Exception as E:
                    
                    cfc.config['WEBSITE_ERRORS'] += ('register', E)
                    return render('students/auto_id_registration.html', 
                                    alert_message='[ Unable to register this ID ]')


@cfc.route('/id/manual_registration', methods=['GET', 'POST'])
def manualIdRegistration():
    if request.method == 'GET':
        return render('students/manual_id_registration.html')

    if request.method == 'POST':
        session["active_student_id"] = request.form['std_roll_no']
        name = request.form['std_name']#.replace(' ', '_')
        email = request.form['email']
        pin = request.form['pin_code']
        init_amount = request.form['initial_amount']
        master_key = int(request.form['master_product_key'])
        
        if master_key != int(MASTER_PRODUCT_KEY):
            return render('students/manual_id_registration.html', 
                                alert_message='Invalid Master Product Key.')

        else:
            if len(pin  ) < 4:
                return render('students/manual_id_registration.html', 
                                    alert_message='[ Pin Code too short! ]')
            
            elif int(init_amount) < 30:
                return render('students/manual_id_registration.html', 
                                        alert_message='[ Minimum amount required is Rs.30]')
            
            else:
                try:
                    register_student(int(session["active_student_id"]), int(pin),
                                    int(init_amount), name=name, email=email)

                    user = db_session.query(Student).filter_by(usid=session["active_student_id"]).first()
                    login_user(user)
                    
                    return redirect(to('dashboard', user=str(session["active_student_id"])))

                except Exception as E:
                    cfc.config['WEBSITE_ERRORS'] += ('register', E)
                    return render('students/manual_id_registration.html', 
                                        alert_message='[ Unable to register this ID ]')


@cfc.route('/dashboard/<user>')
@login_required
def dashboard(user):
    return render('students/dashboard.html', 
                web_page_msg=f'Hey there: {user}. Welcome!', 
                student_roll_no=user)


@cfc.route('/account/payment', methods=['GET', 'POST'])
@login_required
def payment():
    if request.method == 'GET':
        return render('students/payment.html', 
            web_page_msg=f'Hey there: {str(session["active_student_id"])}. Welcome!', 
            student_roll_no=str(session["active_student_id"]))

    if request.method == 'POST':
        amount_to_pay = request.form['amount_to_pay']
        master_product_key = int(request.form['master_product_key'])
        amount = get_student_details(int(session["active_student_id"]), 'amount')

        if int(MASTER_PRODUCT_KEY) != int(master_product_key):
            return render('students/payment.html',
                            debit_status='❌Invalid Master Product Key.')

        else:
            if int(amount_to_pay) > int(amount):
                return render('students/payment.html', 
                                web_page_msg=f'Hey there: {str(session["active_student_id"])}. Welcome!',
                                student_roll_no=str(session["active_student_id"]),
                                debit_status=f'⚠️Amount in account is less: ₹{amount}')

            else:
                try:
                    debit_balance(int(amount_to_pay), int(session["active_student_id"]))
                    return render('students/payment.html', 
                                        web_page_msg=f'Hey there: {str(session["active_student_id"])}. Welcome!',
                                        student_roll_no=str(session["active_student_id"]),
                                        debit_status='✅')

                except Exception as E:
                    cfc.config['WEBSITE_ERRORS'] += ('payment form', E)
                    return render('students/payment.html', 
                                    web_page_msg=f'Hey there: {str(session["active_student_id"])}. Welcome!',
                                    student_roll_no=str(session["active_student_id"]), 
                                    debit_status='❌Failed to do the payment process.')


@cfc.route('/account/balance/update', methods=['GET', 'POST'])
@login_required
def updateAmount():
    if request.method == 'GET':
        return render('students/update_amount.html', 
                    web_page_msg=f'Hey there: {str(session["active_student_id"])}. Welcome!', 
                    student_roll_no=str(session["active_student_id"]))

    if request.method == 'POST':
        amount_to_credit = request.form['amount_to_update']
        master_product_key = int(request.form['master_product_key'])
        
        if int(MASTER_PRODUCT_KEY) != int(master_product_key):
            return render('students/update_amount.html', 
                        update_status='❌Invalid Master Product Key.')

        else:
            if int(amount_to_credit) < 0:
                return render('students/update_amount.html', 
                            web_page_msg=f'Hey there: {str(session["active_student_id"])}. Welcome!',
                            student_roll_no=str(session["active_student_id"]),
                            update_status='⚠️Invalid amount.')

            elif int(amount_to_credit) == 0:
                return render('students/update_amount.html', 
                            web_page_msg=f'Hey there: {str(session["active_student_id"])}. Welcome!',
                            student_roll_no=str(session["active_student_id"]))

            else:
                try:
                    credit_balance(int(amount_to_credit), int(session["active_student_id"]))
                    return render('students/update_amount.html', 
                                web_page_msg=f'Hey there: {str(session["active_student_id"])}. Welcome!',
                                student_roll_no=str(session["active_student_id"]),
                                update_status='✅')

                except Exception as E:
                    cfc.config['WEBSITE_ERRORS'] += ('payment form', E)
                    return render('students/update_amount.html', 
                                web_page_msg=f'Hey there: {str(session["active_student_id"])}. Welcome!',
                                student_roll_no=str(session["active_student_id"]),
                                update_status='❌Unable to update the account balance.')


@cfc.route('/account/balance/check')
@login_required
def checkBalance():
    balance = get_student_details(int(session["active_student_id"]), 'amount')
    
    return render('students/balance_check.html',
                    web_page_msg=f'Hey there: {str(session["active_student_id"])}. Welcome!',
                    student_roll_no=session["active_student_id"], 
                    amount=str(balance))


@cfc.route('/account/transaction/view')
@login_required
def viewLog():
    try:
        std_log_name = get_student_details(int(session["active_student_id"]), 'usid')

        with open(f'Database/logs/{std_log_name}.txt', 'r') as log_file:
            std_transaction_details = log_file.read()

        return render('students/log_viewer.html', 
                    web_page_msg=f'Hey there: {str(session["active_student_id"])}. Welcome!', 
                    student_roll_no=str(session["active_student_id"]), 
                    content=str(std_transaction_details))

    except Exception as E:
        cfc.config['WEBSITE_ERRORS'] += ('view_log web method', E)
        return render('students/dashboard.html', 
                    student_roll_no=str(session["active_student_id"]), 
                    error="Oops... Something went wrong 🤷🏼‍♂️")


@cfc.route('/account/transaction/send_log')
@login_required
def send_transaction_log():
    try:
        std_email = get_student_details(int(session["active_student_id"]), 'email')

        send_mail(to=std_email, mail_type='log')
        return render('students/transaction_log_sender.html', 
                        web_page_msg=f'Hey there: {str(session["active_student_id"])}. Welcome!', 
                        student_roll_no=str(session["active_student_id"]),
                        status=f"Log file Sent to {std_email}")
    
    except Exception as E:
        cfc.config['WEBSITE_ERRORS'] += ('Sending Log (send_transaction_log web method)', E)
        return render('students/dashboard.html', 
                                student_roll_no=str(session["active_student_id"]),
                                alert_message="Oops... Something went wrong 🤷🏼‍♂️")


@cfc.route('/account/update/pin_code/2FA', methods=['GET', 'POST'])
def twoFA():
    if request.method == 'GET':
        return render('students/2FA.html', validity='')

    if request.method == 'POST':
        session["active_student_id"] = int(request.form['std_roll_no_pcr'])
        
        if scan_ids(int(session["active_student_id"])) is True:
            session["2FA-code"] = create_2FA_code()
            
            try:
                send_mail(int(session["active_student_id"]), '2FA', twoFA=session["2FA-code"])
                return redirect(to('pin_code_reset'))
            
            except Exception as E:
                cfc.config['WEBSITE_ERRORS'] += ('2FA Form', E)
                return render('students/2FA.html', validity="Oops... Something went wrong 🤷🏼‍♂️")
        
        else:
            return render('students/2FA.html', validity='This ID is not registered')


@cfc.route('/account/update/pin_code/reset', methods=['GET', 'POST'])
def pin_code_reset():
    if session['2FA-code']:
        if request.method == 'GET':
            std_email = get_student_details(int(session["active_student_id"]), 'email')
            msg = f'The 2FA code has been sent to {std_email}'

            return render('students/pin_code_reset.html', 
                    web_page_msg=msg, 
                    student_roll_no=str(session["active_student_id"]))

        if request.method == 'POST':
            user_2FA = request.form['user_2FA']
            new_pin_code = request.form['new_pin_code']
            confirm_pin_code = request.form['confirm_pin_code']
            
            if str(user_2FA) != str(session["2FA-code"]):
                return render('pin_code_reset.html', 
                            student_roll_no=str(session["active_student_id"]),
                            error='Incorrect 2FA Code')
                
            if str(new_pin_code) != str(confirm_pin_code):
                return render('students/pin_code_reset.html', 
                            student_roll_no=str(session["active_student_id"]),
                            error='Incorrect Pin Confirmation')

            if ((str(new_pin_code).__len__() < 4) == True) and ((str(confirm_pin_code).__len__() < 4) == True):
                return render('students/pin_code_reset.html', 
                            student_roll_no=str(session["active_student_id"]),
                            error='Pin Code too short. Min 4 char')

            else:
                try:
                    student = db_session.query(Student).filter_by(usid=str(session["active_student_id"])).first()
                    if student:
                        student.pin = confirm_pin_code
                        db_session.commit()

                        send_mail(int(session["active_student_id"]), 'pin_code_update', new_pin=confirm_pin_code)
                        
                        return render('students/pin_code_reset.html', 
                                                student_roll_no=str(session["active_student_id"]),
                                                web_page_msg='Pin-Code successfully changed. Now you can login.')
                    
                except Exception as E:
                    std_email = get_student_details(int(session["active_student_id"]), 'email')
                    msg = f'The 2FA code has been sent to {std_email}'
                    cfc.config['WEBSITE_ERRORS'] += ('Resetting user PIN code', E)

                    return render('students/pin_code_reset.html', 
                            web_page_msg=msg, 
                            student_roll_no=str(session["active_student_id"]),
                            status='❌')

    else: return redirect(to('twoFA'))


@cfc.route('/CFC/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'GET':
        return render('feedback.html',
                    greet=greeting())

    if request.method == 'POST':
        fdb = request.form['fdb']

        try:
            with open('Database/feedbacks.txt', 'a') as fdb_file:
                fdb_id = create_id(id_len=5)
                fdb_file.write(f'~Feedback ID: {fdb_id}\n-Feedback: {fdb}\n\n')
        
        except Exception as E:
            cfc.config['WEBSITE_ERRORS'] += ('Feedback system', E)
            return render('feedback.html',
                            greet=greeting(), 
                            page_error='Unable to collect your feedback.')

        return render('feedback.html',
                        greet=greeting(),
                        fdb_status=" -Collected✅")


# ***********************Admin Routes*********************** #
@cfc.route('/admin/login', methods=['GET', 'POST'])
def adminLogin():
    if request.method == 'GET':
        return render('Admin/admin_login.html')

    if request.method == 'POST':
        session["active_admin_ssid"] = str(request.form['ssid'])

        try: 
            admin = db_session.query(Admin).filter_by(ssid=session["active_admin_ssid"]).first()
            if str(request.form['pswd']) == admin.pswd:
                return redirect(to('adminDashboard', admin=session["active_admin_ssid"]))

            else: return render('Admin/admin_login.html', 
                                alert_message='[ Wrong Password ]')

        except Exception as E:
            cfc.config['WEBSITE_ERRORS'] += ('Admin login', E)
            return render('Admin/admin_login.html', alert_message='[ Wrong SSID ]')


@cfc.route('/admin/dashboard/logout')
def adminLogout():
    try: session.pop("active_admin_ssid", None)
    except KeyError: return '<h3 align="center">Unable to logout!'

    return redirect(to('adminLogin', status='logged-out'))


@cfc.route('/admin/register', methods=['GET', 'POST'])
def adminRegister():
    if request.method == 'GET':
        return render('Admin/admin_registration.html', 
                        web_page_msg=greeting(),
                        next_bool=False)

    if request.method == 'POST':
        session["active_admin_ssid"] = request.form['ussid']
        session['active_admin_email'] = request.form['email']
        session['active_admin_pswd'] = request.form['new_password']
        CNF_PSWD = request.form['confirm_password']
        MASTER_KEY = request.form['master_key']
        
        if MASTER_KEY != MASTER_PROCESS_KEY:
            return render('Admin/admin_registration.html', 
                                error='Invalid Process Key')

        else:
            admin_ids = db_session.query(Admin.ssid).all()
            if request.form['ussid'] in [admin_id for (admin_id,) in admin_ids]:
                return render('Admin/admin_registration.html', 
                        error='[ SSID already in use. ]',
                        status="❌", next_bool=False)

            else:
                pswd_validity = check_password_validity(session['active_admin_pswd'], CNF_PSWD)
                if pswd_validity is True:
                    cfc.config['ADMIN_2FA_CODE'] = create_2FA_code()
                    if send_mail(to=session['active_admin_email'], 
                              mail_type='2FA', twoFA=cfc.config['ADMIN_2FA_CODE']):
                        return redirect(to('admin2FA'))

                    else: return render('Admin/admin_registration.html', 
                                error='[ Unable to send 2FA Code. ]',
                                status="❌", next_bool=False)

                else:
                    return render('Admin/admin_registration.html',
                                    error=pswd_validity[-1],
                                    next_bool=False)


@cfc.route('/admin/login/2FA', methods=['GET', 'POST'])
def admin2FA():
    if request.method == 'GET':
        return render('Admin/admin_2FA.html')

    if request.method == 'POST':
        if (str(request.form['admin_2FA_code']) == str(cfc.config['ADMIN_2FA_CODE'])):
            registration_status = register_admin(
                                    create_id(id_len=7, only_int=True), 
                                    session["active_admin_ssid"], 
                                    session['active_admin_pswd'], 
                                    session['active_admin_email'])

            if registration_status is True:
                return redirect(to('adminDashboard', admin=session["active_admin_ssid"]))

            else: return render('Admin/admin_2FA.html', validity=f'[Unable to register you]: {registration_status}')

        else: return render('Admin/admin_2FA.html', validity='[ Wrong 2FA Code given ]')


@cfc.route('/admin/dashboard/<admin>')
def adminDashboard(admin):
    if "active_admin_ssid" in session:
        return render('Admin/admin_dashboard.html',
                        web_page_msg=greeting(),
                        admin=admin)
    
    else: return redirect(to('adminLogin', status='logged-out'))


@cfc.route('/admin/developer/database/accounts/view/student')
def view_student_database():
    if "active_admin_ssid" in session:
        try:
            try: data = read_database_file('students')
            except Exception: data = 'No data found'

            return render('Admin/admin_STdatabase_viewer.html', 
                            data=data, admin=session["active_admin_ssid"])

        except Exception as E:
            cfc.config['WEBSITE_ERRORS'] += ['reading the database (view_student_database web method)', E]
            
            return render('Admin/admin_STdatabase_viewer.html', 
                            page_error='Oops something went wrong 😬',
                            admin=session["active_admin_ssid"])

    else: return redirect(to('adminLogin', status='logged-out'))


@cfc.route('/admin/developer/database/accounts/view/admin')
def view_admin_database():
    if "active_admin_ssid" in session:
        data = read_database_file('admin')
        if type(data) is pandas.DataFrame:
            return render('Admin/admin_ADdatabase_viewer.html',
                            admin_login_details=data,
                            admin=session["active_admin_ssid"])
        
        elif type(data) is Exception:
            cfc.config['WEBSITE_ERRORS'] += ['view_admin_database web method', data]
            return render('Admin/admin_ADdatabase_viewer.html',
                            page_error='Unable to show admin database.',
                            admin=session["active_admin_ssid"])

    else: return redirect(to('adminLogin', status='logged-out'))


# main function for running server
if __name__ == '__main__':
    cfc.run(HOST, PORT, DEBUG)