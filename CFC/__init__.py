import os
import string
import random
import pandas
import datetime

try: import smtplib
except ImportError: os.system('pip install smtplib')

try: from termcolor import cprint, colored
except ImportError: os.system('pip install termcolor')

try: from dotenv import load_dotenv
except ImportError: os.system('pip install python-dotenv')

from email import encoders
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from sqlalchemy.ext.automap import automap_base

from .models import *


# Create tables
Base.metadata.create_all(engine)

# Reflect the database tables
Base_ = automap_base()
Base_.prepare(engine, reflect=True)

# env_file_path = os.path.join('../', )
load_dotenv('website_info.env')

SMTP_SERVER = os.getenv('SMTP_SERVER')
SERVER_PORT = os.getenv('SERVER_PORT')
HOST_SSID = os.getenv("HOST_SSID")
HOST_PSWD = os.getenv("HOST_PSWD")


def greeting():
    greeting_message = str()

    hour = int(datetime.datetime.now().hour)
    if hour >= 0 and hour < 12:
        greeting_message = 'Good Morning!'

    elif hour >= 12 and hour < 18:
        greeting_message = 'Good Afternoon!'

    else:
        greeting_message = 'Good Evening!'

    return str(greeting_message)


def create_id(id_len: int=16, only_int: bool=False):
    r_file = os.path.join('Database', 'log_file_names.txt')

    with open(r_file, 'r') as log_file:
        available_logs = log_file.readlines()

    for i in available_logs:
        available_logs[available_logs.index(i)] = i[:-1]

    while True:
        if only_int is False:
            uid = ''.join(
                random.choice(string.ascii_letters + string.digits) 
                for _ in range(id_len))
        
        elif only_int is True:
            uid = ''.join(
                random.choice(string.digits) 
                for _ in range(id_len))
        
        if uid in available_logs: continue
        else: 
            with open(r_file, 'a') as log_file: log_file.write(f'{uid}\n')
            break
    
    return uid


def create_2FA_code(code_len: int=6, code_type: str='numeric'):
    if code_type in 'numeric':
        code = ''.join(
            random.choice(string.digits) 
            for _ in range(code_len))
    
    elif code_type in 'alphabetic':
        code = ''.join(
            random.choice(string.ascii_letters) 
            for _ in range(code_len))
    
    elif code_type in 'hybrid':
        code = ''.join(
            random.choice(string.ascii_letters + string.digits + string.punctuation) 
            for _ in range(code_len))        

    return code


def scan_ids(user_sid: int):
    user_ids = db_session.query(Student.usid).all()
    if user_sid in [user_id for (user_id,) in user_ids]: return True
    else: False


def get_student_details(user_sid: int, give: str):
    user_data = db_session.query(Student).filter_by(usid=user_sid).first()
    data_map = {
        'usid': int(user_data.usid),
        'pin': int(user_data.pin),
        'email': user_data.email,
        'amount': int(user_data.amount),
        'name': user_data.name
    }

    return data_map[give]


def register_student(new_usid: int, pin: int, init_amount: int, **kwargs):
    date = datetime.datetime.now().strftime('%d-%m-%Y')

    try:
        existing_user = db_session.query(Student).filter_by(usid=new_usid).first()
        if existing_user: return 'existing_user'
        else:
            new_user = Student(usid=new_usid, pin=pin, amount=init_amount, 
                            name=kwargs['name'], email=kwargs['email'])
            db_session.add(new_user)
            db_session.commit()

            log_file = f'Database/logs/{new_usid}.txt'
            try:
                open(log_file, 'x').close()
                with open(log_file, 'a') as file:
                    file.write(f'Account Log of: {kwargs["name"]}\n')
                    file.write(f'Registerd on: {date}\n')
                    file.write(f'Personal Email: {kwargs["email"]}\n')
                    file.write(f'Initial/Opening Balance: Rs.{str(init_amount)}\n\n')
                    file.write('*'*26 + '\n\n')

                    send_mail(new_usid, get_student_details(new_usid, 'email'), 'register')

            except FileNotFoundError as FNE: cprint(f'Failed to register student: {FNE}', 'red', attrs=['bold'])

    except: cprint(f'Student already registered!', 'red', attrs=['bold'])


def register_admin(uid: int, ssid: str, password: str, email: str):
    try:
        existing_user = db_session.query(Admin).filter_by(uid=uid).first()
        if existing_user: return 'existing_user'
        else:
            new_user = Admin(uid=uid, ssid=ssid, pswd=password, email=email)
            db_session.add(new_user)
            db_session.commit()

            return True

    except Exception as E:
        cprint(f"Unable to register admin: {E}", 'red', attrs=['bold'])
        return E


def check_password_validity(pswd: str, cnf_pswd: str):
    if pswd == cnf_pswd:
        if len(pswd) and len(cnf_pswd) >= 4:
            return True
        else: return (False, '[ Password too short. ]')
    else: return (False, '[ Password does not match. ]')


def debit_balance(debit_amount: int, _id: int):
    date = datetime.datetime.now().strftime('%d-%m-%Y')

    try:
        std_amount = get_student_details(_id, 'amount')
        
        if std_amount < debit_amount:
            cprint('\nLow balance!', 'red', attrs=['bold'])
            print(f"Amount left in account: {colored(f'Rs.{std_amount}', 'red', attrs=['bold'])}")
        
        if std_amount <= 10:
            send_mail(_id, 'low-balance', balance=std_amount)

        else:

            final_amount = std_amount - debit_amount
            
            if final_amount <= 10:
                send_mail(_id, get_student_details(_id, 'email'), 'low-balance', balance=final_amount)

            student = db_session.query(Student).filter_by(usid=_id).first()
            if student:
                student.amount = final_amount
                db_session.commit()

            w_file = os.path.join('Database/logs', str(get_student_details(_id, 'usid')) + '.txt')

            with open(w_file, 'a') as file:
                file.write(f'Date: {date}\n')
                file.write(f'Bought item(s) of amount: Rs.{debit_amount}\n')
                file.write(f'Amount left in amount: Rs.{final_amount}\n\n')
            
            send_mail(_id, 'debit', debit_amount=debit_amount, balance=final_amount)

    except Exception as IE: cprint(f'Failed to debit balance: {IE}', 'red', attrs=['bold'])


def credit_balance(update_amount: int, _id: int):
    date = datetime.datetime.now().strftime('%d-%m-%Y')

    std_amount = get_student_details(_id, 'amount')

    final_amount = std_amount + update_amount

    student = db_session.query(Student).filter_by(usid=_id).first()
    if student:
        student.amount = final_amount
        db_session.commit()

    w_file = 'Database/logs/' + str(get_student_details(_id, 'usid')) + '.txt'

    with open(w_file, 'a') as file:
        file.write(f'Date: {date}\n')
        file.write(f'Amount credited: Rs.{update_amount}\n')
        file.write(f'Total amount in account: Rs.{final_amount}\n\n')

    send_mail(_id, get_student_details(_id, 'email'), 'credit', credit_amnt=update_amount, balance=final_amount)

    return final_amount


def read_database_file(database: str):
    try:
        data = []
        TableClass = Base_.classes.get(database)
        if TableClass:
            records = db_session.query(TableClass).all()
            for record in records:
                data.append(
                    {
                        column.name: getattr(record, column.name) 
                        for column in record.__table__.columns
                    }
                )

        return pandas.DataFrame(data)

    except Exception as E: 
        cprint(f'Error reading database: {E}', 'red', attrs=['bold'])
        return False


def send_mail(_id=int , to: str=None, mail_type: str=None, **kwargs):
    try:
        usid = get_student_details(_id, 'usid')
        name = get_student_details(_id, 'name')
        pin_code = get_student_details(_id, 'pin')
    except: pass

    date = datetime.datetime.now().strftime('%d-%m-%Y')

    mail = MIMEMultipart()

    mail["From"] = "CFC Student Support"
    mail["To"] = to

    if mail_type == 'log':
        subject = "KIIT Polytechnic Canteen Transaction Log"

        body = f"""This mail contains information about your canteen transaction through card.
Please go through the attached file and check the details.
If you have any query(ies), please reply back your query(ies) to the following email address: {HOST_SSID}

[NOTE: Instead of going to canteen and asking for transaction Log file, 
You can reply to this mail with your Log file request. You'll receive a mail with the transaction Log file within 24 Hours.]

Thank You
KIIT Polytechnic Canteen
"""
        std_log_file = f'Database/logs/{usid}.txt'

        try:
            with open(std_log_file, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)

            part.add_header(
                "Content-Disposition",
                f"attachment; filename= Transactions Log",
            )

            mail.attach(part)

        except smtplib.SMTPException: cprint(f'Failed to attach log file!\n', 'red', attrs=['bold'])

    elif mail_type == 'register':
        date = datetime.datetime.now().strftime('%d-%m-%Y')

        subject = "KIIT Polytechnic Canteen Registration"

        body = f"""This mail contains information about your canteen registration.
Please go through the details.
If you have any query(ies), please reply back your query(ies) to the following email address: {HOST_SSID}\n
\n\n
===============================================================
\n\n
Registerd on: {date}
Registered ID: {_id}
Pin Code: {pin_code}
Registered Name: {name}
Registered Email: {to}
Your Student UID (usid): {usid}
\n\n
[NOTE: usid is used to create yout transaction log file. Keep your usid safe somewhere, 
you request your transaction log file by providing your usid. And do download and read 
the attached file. The file contains some frequently asked Questions.]
\n\n
\n\n
Thanks for registering.
KIIT KP Canteen
"""

        try:
            with open("Database/readME.txt", "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
            
                encoders.encode_base64(part)

                part.add_header(
                    "Content-Disposition",
                    "attachment; filename= readME File",
                )

                mail.attach(part)

        except smtplib.SMTPException: cprint(f'Failed to attach log file!\n', 'red', attrs=['bold'])

    elif mail_type == 'low-balance':
        subject = "KIIT Polytechnic Canteen Low Balance"

        body = f"""This mail contains information about your canteen balance.
Please go through the details.
If you have any query(ies), please reply back your query(ies) to the following email address: {HOST_SSID}

===============================================================

Registered ID: {_id}
Registered Name: {name}
Registered Email: {to}

This mail is sent to imform you that, your canteen balance is low.
You have Rs.{kwargs['balance']} left in your canteen account.

If you want your transaction log file, please email your usid to the following email address: {HOST_SSID}.
Your Log file will be sent to you within 24 Hours.

[NOTE: If you want your transaction log file ASAP, you can scan your id card at the canteen.]

Thank You!.
KIIT KP Canteen
"""
    
    elif mail_type == 'debit':
        subject = "KIIT Polytechnic Canteen Purchase"

        body = f"""This mail contains information about your canteen balance.
Please go through the details.
If you have any query(ies), please reply back your query(ies) to the following email address: {HOST_SSID}

===============================================================

Registered ID: {_id}
Registered Name: {name}
Registered Email: {to}

This mail is sent to imform you that, Rs. {kwargs['debit_amount']} have been debited from your canteen account.
Amount left in your account is Rs. {kwargs['balance']}.

If you're not familiar with the transaction. Report this to any of the the canteen employee.

If you want your transaction log file, please email your usid to the following email address: {HOST_SSID}.
Your Log file will be sent to you within 24 Hours.

[NOTE: If you want your transaction log file ASAP, you can scan your id card at the canteen.]

Thank You!.
KIIT KP Canteen
"""

    elif mail_type == 'credit':
        subject = "KIIT Polytechnic Canteen Deposite"

        body = f"""This mail contains information about your canteen balance.
Please go through the details.
If you have any query(ies), please reply back your query(ies) to the following email address: {HOST_SSID}

===============================================================

Registered ID: {_id}
Registered Name: {name}
Registered Email: {to}

This mail is sent to imform you that, Rs. {kwargs['credit_amnt']} has been credited/updated into your canteen account.
Total amount in your canteen account is Rs. {kwargs['balance']}.

If you're not familiar with the deposite/update. Report this to any of the the canteen employee.

If you want your transaction log file, please email your usid to the following email address: {HOST_SSID}.
Your Log file will be sent to you within 24 Hours.

[NOTE: If you want your transaction log file ASAP, you can scan your id card at the canteen.]

Thank You!.
KIIT KP Canteen
"""

    elif mail_type == '2FA':
        subject = "KIIT Polytechnic Canteen Pin-Code Reset"

        body = f"""This is a 2FA mail to reset your Canteen FastCard Payment's PIN-CODE.
Your PIN-CODE reset 2FA code is: {kwargs['twoFA']}.

[NOTE: If you didn't requested for PIN-CODE reset, please don't share this 2FA code with anyone.]
"""

    elif mail_type == 'pin_code_update':
        subject = "KIIT Polytechnic Canteen Pin-Code update"

        body = f"""Your canteen FastCard account PIN-CODE was reset on {date}.
Your new PIN-CODE is: {kwargs['new_pin']}.

[NOTE: If you didn't reset the PIN-CODE, please inform this to any canteen employee.]
"""

    mail["Subject"] = subject

    try:
        mail.attach(MIMEText(body, "html"))
        
        server = smtplib.SMTP_SSL(host=SMTP_SERVER, port=SERVER_PORT)

        server.login(HOST_SSID, HOST_PSWD)
        server.sendmail(HOST_SSID, to, mail.as_string())

        server.quit()

        return True

    except Exception as E:
        cprint(f'Failed!\nDue: {E}', 'red', attrs=['bold'])
        return False

