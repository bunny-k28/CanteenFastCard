import os

from flask import Blueprint
from flask import request, session
from flask_login import LoginManager
from flask_login import login_user, logout_user, login_required
from flask import render_template as render, url_for as to, redirect

from ..models import db
from ..models.errors import Error
from ..models.students import Student
from ..models.feedbacks import Feedback

from . import *
from ..scanner import scan_barcode


load_dotenv(
    os.path.join(
        os.path.abspath(
            os.path.dirname('.')), 
            'site_settings.env')
)
MASTER_PRODUCT_KEY = os.environ.get('MASTER_PRODUCT_KEY')


student = Blueprint('student', __name__, 
                    url_prefix='/student', 
                    template_folder='../site/templates/Student')


# **********************Student Routes********************** #
@student.route('/home', methods=['GET', 'POST'])
@student.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render('index.html')

    if request.method == 'POST':
        session["active_student_id"] = int(request.form['std_id'])
        
        try:
            if scan_ids(int(session["active_student_id"])):
                if get_student_details(int(session["active_student_id"]), 'pin') == int(request.form['std_id_pin']):
                    user = db.query(Student).filter_by(usid=session["active_student_id"]).first()
                    login_user(user)

                    return redirect(to('dashboard', user=str(session["active_student_id"])))

                else: return render('index.html', alert_message='[ Invalid Pin Code ]')
            else: return redirect(to('autoIdRegistration'))

        except Exception as E:
            try:
                new_error = Error(
                    eid=create_error_id(), 
                    emsg=str(E), 
                    etime=datetime.datetime.now(), 
                    earea='Std. Home page post function')

                db.add(new_error)
                db.commit()
            except Exception as E: cprint(f'\nError filing the route error\nError: {E}', 'red')

            return render('index.html', alert_message='[ Unable to verify ]')


@student.route('/id/scan')
def login_by_scan():
    try: 
        session["active_student_id"] = int(scan_barcode())
        if scan_ids(int(session["active_student_id"])):
            user = db.query(Student).filter_by(usid=session["active_student_id"]).first()
            login_user(user)

            return redirect(to('dashboard', user=str(session["active_student_id"])))

        else: return redirect(to('autoIdRegistration'))

    except Exception as E:
        try:
            new_error = Error(
                eid=create_error_id(), 
                emsg=str(E), 
                etime=datetime.datetime.now(), 
                earea='Std. ID Scanner')

            db.add(new_error)
            db.commit()
        except Exception as E: cprint(f'\nError filing the route error\nError: {E}', 'red')

        return render('index.html', alert_message="Unable to scan the ID Card")


@student.route('/dashboard/logout')
def logout():
    session.clear()

    try: logout_user()
    except Exception: pass

    return redirect(to('index', status='logged-out'))


@student.route('/id/auto_registration', methods=['GET', 'POST'])
def autoIdRegistration():
    if request.method == 'GET':
        return render('auto_id_registration.html', 
                        alert_message='[ Not Register! Register your ID here ]')

    if request.method == 'POST':
        name = request.form['std_name'] #.replace(' ', '_')
        email = request.form['email']
        pin = request.form['pin_code']
        init_amount = request.form['initial_amount']
        master_key = int(request.form['master_product_key'])
        
        if master_key != int(MASTER_PRODUCT_KEY):
            return render('auto_id_registration.html', 
                          alert_message='Invalid Master Product Key.')

        else:
            if len(pin) < 4:
                return render('auto_id_registration.html', 
                              alert_message='[ Pin Code too short! ]')

            elif int(init_amount) < 30:
                return render('auto_id_registration.html', 
                              alert_message='[ Minimum amount required is Rs.30]')

            else:
                try:
                    register_student(int(session["active_student_id"]), pin,
                                    int(init_amount), name=name, email=email)

                    user = db.query(Student).filter_by(usid=session["active_student_id"]).first()
                    login_user(user)

                    return redirect(to('dashboard', user=str(session["active_student_id"])))

                except Exception as E:
                    try:
                        new_error = Error(
                            eid=create_error_id(), 
                            emsg=str(E), 
                            etime=datetime.datetime.now(), 
                            earea='Std. Auto registration')

                        db.add(new_error)
                        db.commit()
                    except Exception as E: cprint(f'\nError filing the route error\nError: {E}', 'red')

                    return render('auto_id_registration.html', 
                                    alert_message='[ Unable to register this ID ]')


@student.route('/id/manual_registration', methods=['GET', 'POST'])
def manualIdRegistration():
    if request.method == 'GET':
        return render('manual_id_registration.html')

    if request.method == 'POST':
        session["active_student_id"] = request.form['std_roll_no']
        name = request.form['std_name']#.replace(' ', '_')
        email = request.form['email']
        pin = request.form['pin_code']
        init_amount = request.form['initial_amount']
        master_key = int(request.form['master_product_key'])
        
        if master_key != int(MASTER_PRODUCT_KEY):
            return render('manual_id_registration.html', 
                                alert_message='Invalid Master Product Key.')

        else:
            if len(pin  ) < 4:
                return render('manual_id_registration.html', 
                                    alert_message='[ Pin Code too short! ]')
            
            elif int(init_amount) < 30:
                return render('manual_id_registration.html', 
                                        alert_message='[ Minimum amount required is Rs.30]')
            
            else:
                try:
                    register_student(int(session["active_student_id"]), int(pin),
                                    int(init_amount), name=name, email=email)

                    user = db.query(Student).filter_by(usid=session["active_student_id"]).first()
                    login_user(user)
                    
                    return redirect(to('dashboard', user=str(session["active_student_id"])))

                except Exception as E:
                    try:
                        new_error = Error(
                            eid=create_error_id(), 
                            emsg=str(E), 
                            etime=datetime.datetime.now(), 
                            earea='Std. Manual registration')

                        db.add(new_error)
                        db.commit()
                    except Exception as E: cprint(f'\nError filing the route error\nError: {E}', 'red')

                    return render('manual_id_registration.html', 
                                        alert_message='[ Unable to register this ID ]')


@student.route('/dashboard/<user>')
@login_required
def dashboard(user):
    return render('dashboard.html', 
                web_page_msg=f'Hey there: {user}. Welcome!', 
                student_roll_no=user)


@student.route('/account/payment', methods=['GET', 'POST'])
@login_required
def payment():
    if request.method == 'GET':
        return render('payment.html', 
            web_page_msg=f'Hey there: {str(session["active_student_id"])}. Welcome!', 
            student_roll_no=str(session["active_student_id"]))

    if request.method == 'POST':
        amount_to_pay = request.form['amount_to_pay']
        master_product_key = int(request.form['master_product_key'])
        amount = get_student_details(int(session["active_student_id"]), 'amount')

        if int(MASTER_PRODUCT_KEY) != int(master_product_key):
            return render('payment.html',
                            debit_status='❌Invalid Master Product Key.')

        else:
            if int(amount_to_pay) > int(amount):
                return render('payment.html', 
                                web_page_msg=f'Hey there: {str(session["active_student_id"])}. Welcome!',
                                student_roll_no=str(session["active_student_id"]),
                                debit_status=f'⚠️Amount in account is less: ₹{amount}')

            else:
                try:
                    debit_balance(int(amount_to_pay), int(session["active_student_id"]))
                    return render('payment.html', 
                                        web_page_msg=f'Hey there: {str(session["active_student_id"])}. Welcome!',
                                        student_roll_no=str(session["active_student_id"]),
                                        debit_status='✅')

                except Exception as E:
                    try:
                        new_error = Error(
                            eid=create_error_id(), 
                            emsg=str(E), 
                            etime=datetime.datetime.now(), 
                            earea='Std. Payment Form')

                        db.add(new_error)
                        db.commit()
                    except Exception as E: cprint(f'\nError filing the route error\nError: {E}', 'red')

                    return render('payment.html', 
                                    web_page_msg=f'Hey there: {str(session["active_student_id"])}. Welcome!',
                                    student_roll_no=str(session["active_student_id"]), 
                                    debit_status='❌Failed to do the payment process.')


@student.route('/account/balance/update', methods=['GET', 'POST'])
@login_required
def updateAmount():
    if request.method == 'GET':
        return render('update_amount.html', 
                    web_page_msg=f'Hey there: {str(session["active_student_id"])}. Welcome!', 
                    student_roll_no=str(session["active_student_id"]))

    if request.method == 'POST':
        amount_to_credit = request.form['amount_to_update']
        master_product_key = int(request.form['master_product_key'])
        
        if int(MASTER_PRODUCT_KEY) != int(master_product_key):
            return render('update_amount.html', 
                        update_status='❌Invalid Master Product Key.')

        else:
            if int(amount_to_credit) < 0:
                return render('update_amount.html', 
                            web_page_msg=f'Hey there: {str(session["active_student_id"])}. Welcome!',
                            student_roll_no=str(session["active_student_id"]),
                            update_status='⚠️Invalid amount.')

            elif int(amount_to_credit) == 0:
                return render('update_amount.html', 
                            web_page_msg=f'Hey there: {str(session["active_student_id"])}. Welcome!',
                            student_roll_no=str(session["active_student_id"]))

            else:
                try:
                    credit_balance(int(amount_to_credit), int(session["active_student_id"]))
                    return render('update_amount.html', 
                                web_page_msg=f'Hey there: {str(session["active_student_id"])}. Welcome!',
                                student_roll_no=str(session["active_student_id"]),
                                update_status='✅')

                except Exception as E:
                    try:
                        new_error = Error(
                            eid=create_error_id(), 
                            emsg=str(E), 
                            etime=datetime.datetime.now(), 
                            earea='Std. Update amount form')

                        db.add(new_error)
                        db.commit()
                    except Exception as E: cprint(f'\nError filing the route error\nError: {E}', 'red')

                    return render('update_amount.html', 
                                web_page_msg=f'Hey there: {str(session["active_student_id"])}. Welcome!',
                                student_roll_no=str(session["active_student_id"]),
                                update_status='❌Unable to update the account balance.')


@student.route('/account/balance/check')
@login_required
def checkBalance():
    balance = get_student_details(int(session["active_student_id"]), 'amount')
    
    return render('balance_check.html',
                    web_page_msg=f'Hey there: {str(session["active_student_id"])}. Welcome!',
                    student_roll_no=session["active_student_id"], 
                    amount=str(balance))


@student.route('/account/transaction/view')
@login_required
def viewLog():
    try:
        std_log_name = get_student_details(int(session["active_student_id"]), 'usid')

        with open(f'Database/logs/{std_log_name}.txt', 'r') as log_file:
            std_transaction_details = log_file.read()

        return render('log_viewer.html', 
                    web_page_msg=f'Hey there: {str(session["active_student_id"])}. Welcome!', 
                    student_roll_no=str(session["active_student_id"]), 
                    content=str(std_transaction_details))

    except Exception as E:
        try:
            new_error = Error(
                eid=create_error_id(), 
                emsg=str(E), 
                etime=datetime.datetime.now(), 
                earea='Std. viewLog route')

            db.add(new_error)
            db.commit()
        except Exception as E: cprint(f'\nError filing the route error\nError: {E}', 'red')

        return render('dashboard.html', 
                    student_roll_no=str(session["active_student_id"]), 
                    error="Oops... Something went wrong 🤷🏼‍♂️")


@student.route('/account/transaction/send_log')
@login_required
def sendTransactionLog():
    try:
        std_email = get_student_details(int(session["active_student_id"]), 'email')

        send_mail(to=std_email, mail_type='log')
        return render('transaction_log_sender.html', 
                        web_page_msg=f'Hey there: {str(session["active_student_id"])}. Welcome!', 
                        student_roll_no=str(session["active_student_id"]),
                        status=f"Log file Sent to {std_email}")
    
    except Exception as E:
        try:
            new_error = Error(
                eid=create_error_id(), 
                emsg=str(E), 
                etime=datetime.datetime.now(), 
                earea='Std. sendTransactionLog route')

            db.add(new_error)
            db.commit()
        except Exception as E: cprint(f'\nError filing the route error\nError: {E}', 'red')

        return render('dashboard.html', 
                                student_roll_no=str(session["active_student_id"]),
                                alert_message="Oops... Something went wrong 🤷🏼‍♂️")


@student.route('/account/update/pin_code/2FA', methods=['GET', 'POST'])
def twoFA():
    if request.method == 'GET':
        return render('2FA.html', validity='')

    if request.method == 'POST':
        session["active_student_id"] = int(request.form['std_roll_no_pcr'])
        
        if scan_ids(int(session["active_student_id"])) is True:
            session["2FA-code"] = create_2FA_code()
            
            try:
                send_mail(int(session["active_student_id"]), '2FA', twoFA=session["2FA-code"])
                return redirect(to('pinCodeReset'))
            
            except Exception as E:
                try:
                    new_error = Error(
                        eid=create_error_id(), 
                        emsg=str(E), 
                        etime=datetime.datetime.now(), 
                        earea='Std. twoFA route')

                    db.add(new_error)
                    db.commit()
                except Exception as E: cprint(f'\nError filing the route error\nError: {E}', 'red')

                return render('2FA.html', validity="Oops... Something went wrong 🤷🏼‍♂️")
        
        else:
            return render('2FA.html', validity='This ID is not registered')


@student.route('/account/update/pin_code/reset', methods=['GET', 'POST'])
def pinCodeReset():
    if session['2FA-code']:
        if request.method == 'GET':
            std_email = get_student_details(int(session["active_student_id"]), 'email')
            msg = f'The 2FA code has been sent to {std_email}'

            return render('pin_code_reset.html', 
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
                return render('pin_code_reset.html', 
                            student_roll_no=str(session["active_student_id"]),
                            error='Incorrect Pin Confirmation')

            if ((str(new_pin_code).__len__() < 4) == True) and ((str(confirm_pin_code).__len__() < 4) == True):
                return render('pin_code_reset.html', 
                            student_roll_no=str(session["active_student_id"]),
                            error='Pin Code too short. Min 4 char')

            else:
                try:
                    student = db.query(Student).filter_by(usid=str(session["active_student_id"])).first()
                    if student:
                        student.pin = confirm_pin_code
                        db.commit()

                        send_mail(int(session["active_student_id"]), 'pin_code_update', new_pin=confirm_pin_code)
                        
                        return render('pin_code_reset.html', 
                                                student_roll_no=str(session["active_student_id"]),
                                                web_page_msg='Pin-Code successfully changed. Now you can login.')

                except Exception as E:
                    std_email = get_student_details(int(session["active_student_id"]), 'email')
                    msg = f'The 2FA code has been sent to {std_email}'

                    try:
                        new_error = Error(
                            eid=create_error_id(), 
                            emsg=str(E), 
                            etime=datetime.datetime.now(), 
                            earea='Std. pinCodeReset route')

                        db.add(new_error)
                        db.commit()
                    except Exception as E: cprint(f'\nError filing the route error\nError: {E}', 'red')

                    return render('pin_code_reset.html', 
                            web_page_msg=msg, 
                            student_roll_no=str(session["active_student_id"]),
                            status='❌')

    else: return redirect(to('twoFA'))


@student.route('/CFC/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'GET':
        return render('../feedback.html',
                    greet=greeting())

    if request.method == 'POST':
        fdb = request.form['fdb']

        try:
            new_feedback = Feedback(
                fid=create_id(id_len=5),
                feedback=fdb)

            db.add(new_feedback)
            db.commit()
        
        except Exception as E:
            try:
                new_error = Error(
                    eid=create_error_id(), 
                    emsg=str(E), 
                    etime=datetime.datetime.now(), 
                    earea='feedback route')

                db.add(new_error)
                db.commit()
            except Exception as E: cprint(f'\nError filing the route error\nError: {E}', 'red')

            return render('../feedback.html',
                            greet=greeting(), 
                            page_error='Unable to collect your feedback.')

        return render('../feedback.html',
                        greet=greeting(),
                        fdb_status=" -Collected✅")
