import os

from flask import Blueprint
from flask import request, session
from flask import render_template as render, url_for as to, redirect

from pandas.core.frame import DataFrame
from dotenv import load_dotenv

from ..models import db
from ..models.admin import Admin
from ..models.errors import Error

from . import *

load_dotenv(
    os.path.join(
        os.path.abspath(
            os.path.dirname('.')), 
            'site_settings.env')
)
MASTER_PROCESS_KEY = os.environ.get('MASTER_PROCESS_KEY')


admin = Blueprint('admin', __name__, 
                    url_prefix='/admin',
                    template_folder='../site/templates/Admin')


# ***********************Admin Routes*********************** #
@admin.route('/login', methods=['GET', 'POST'])
def adminLogin():
    if request.method == 'GET':
        return render('admin_login.html')

    if request.method == 'POST':
        session["active_admin_ssid"] = str(request.form['ssid'])

        try: 
            admin = db.query(Admin).filter_by(ssid=session["active_admin_ssid"]).first()
            if str(request.form['pswd']) == admin.pswd:
                return redirect(to('adminDashboard', admin=session["active_admin_ssid"]))

            else: return render('admin_login.html', 
                                alert_message='[ Wrong Password ]')

        except Exception as E:
            try:
                new_error = Error(
                    eid=create_error_id(), 
                    emsg=str(E), 
                    etime=datetime.datetime.now(), 
                    earea='adminLogin route')

                db.add(new_error)
                db.commit()
            except Exception as E:
                db.rollback()
                cprint(f'\nError filing the route error\nError: {E}', 'red')

            return render('admin_login.html', alert_message='[ Wrong SSID ]')


@admin.route('/dashboard/logout')
def adminLogout():
    try: session.pop("active_admin_ssid", None)
    except KeyError: return '<h3 align="center">Unable to logout!'

    return redirect(to('adminLogin', status='logged-out'))


@admin.route('/register', methods=['GET', 'POST'])
def adminRegister():
    if request.method == 'GET':
        return render('admin_registration.html', 
                        web_page_msg=greeting(),
                        next_bool=False)

    if request.method == 'POST':
        session["active_admin_ssid"] = request.form['ussid']
        session['active_admin_email'] = request.form['email']
        session['active_admin_pswd'] = request.form['new_password']
        CNF_PSWD = request.form['confirm_password']
        MASTER_KEY = request.form['master_key']
        
        if MASTER_KEY != MASTER_PROCESS_KEY:
            return render('admin_registration.html', 
                                error='Invalid Process Key')

        else:
            admin_ids = db.query(Admin.ssid).all()
            if request.form['ussid'] in [admin_id for (admin_id,) in admin_ids]:
                return render('admin_registration.html', 
                        error='[ SSID already in use. ]',
                        status="❌", next_bool=False)

            else:
                pswd_validity = check_password_validity(session['active_admin_pswd'], CNF_PSWD)
                if pswd_validity is True:
                    session['ADMIN_2FA_CODE'] = create_2FA_code()
                    if send_mail(to=session['active_admin_email'], 
                              mail_type='2FA', twoFA=session['ADMIN_2FA_CODE']):
                        return redirect(to('admin2FA'))

                    else: return render('admin_registration.html', 
                                error='[ Unable to send 2FA Code. ]',
                                status="❌", next_bool=False)

                else:
                    return render('admin_registration.html',
                                    error=pswd_validity[-1],
                                    next_bool=False)


@admin.route('/login/2FA', methods=['GET', 'POST'])
def admin2FA():
    if request.method == 'GET':
        return render('admin_2FA.html')

    if request.method == 'POST':
        if (str(request.form['admin_2FA_code']) == str(session['ADMIN_2FA_CODE'])):
            registration_status = register_admin(
                                    create_id(id_len=7, only_int=True), 
                                    session["active_admin_ssid"], 
                                    session['active_admin_pswd'], 
                                    session['active_admin_email'])

            if registration_status is True:
                return redirect(to('adminDashboard', admin=session["active_admin_ssid"]))

            else: return render('admin_2FA.html', validity=f'[Unable to register you]: {registration_status}')

        else: return render('admin_2FA.html', validity='[ Wrong 2FA Code given ]')


@admin.route('/dashboard/<admin>')
def adminDashboard(admin):
    if "active_admin_ssid" in session:
        return render('admin_dashboard.html',
                        web_page_msg=greeting(),
                        admin=admin)
    
    else: return redirect(to('adminLogin', status='logged-out'))


@admin.route('/developer/database/accounts/view/student')
def viewStudentDatabase():
    if "active_admin_ssid" in session:
        try:
            try: data = read_database_file('students')
            except Exception: data = 'No data found'

            return render('admin_STdatabase_viewer.html', 
                            data=data, admin=session["active_admin_ssid"])

        except Exception as E:
            try:
                new_error = Error(
                    eid=create_error_id(), 
                    emsg=str(E), 
                    etime=datetime.datetime.now(), 
                    earea='viewStudentDatabase route')

                db.add(new_error)
                db.commit()
            except Exception as E:
                db.rollback()
                cprint(f'\nError filing the route error\nError: {E}', 'red')
            
            return render('admin_STdatabase_viewer.html', 
                            page_error='Oops something went wrong 😬',
                            admin=session["active_admin_ssid"])

    else: return redirect(to('adminLogin', status='logged-out'))


@admin.route('/developer/database/accounts/view/admin')
def viewAdminDatabase():
    if "active_admin_ssid" in session:
        data = read_database_file('admin')
        if type(data) is DataFrame:
            return render('admin_ADdatabase_viewer.html',
                            admin_login_details=data,
                            admin=session["active_admin_ssid"])

        else:
            try:
                new_error = Error(
                    eid=create_error_id(), 
                    emsg=str(data), 
                    etime=datetime.datetime.now(),
                    earea='viewAdminDatabase')

                db.add(new_error)
                db.commit()
            except Exception as E:
                db.rollback()
                cprint(f'\nError filing the route error\nError: {E}', 'red')

            return render('admin_ADdatabase_viewer.html',
                            page_error='Unable to show admin database.',
                            admin=session["active_admin_ssid"])

    else: return redirect(to('adminLogin', status='logged-out'))