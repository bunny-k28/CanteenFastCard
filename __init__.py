import os
import pyotp
import qrcode
import string
import random
import pandas
import sqlite3
import datetime
import PIL

try: import smtplib, ssl
except ImportError: os.system('pip install smtplib, ssl')

try: from termcolor import cprint, colored
except ImportError: os.system('pip install termcolor')

try: from dotenv import load_dotenv
except ImportError: os.system('pip install python-dotenv')

from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText



env_file_path = os.path.join('Database', 'website_info.env')
load_dotenv(env_file_path)

SMTP_SERVER = os.getenv('SMTP_SERVER')
SERVER_PORT = int(os.getenv('SERVER_PORT'))
HOST_SSID = os.getenv("HOST_SSID")
HOST_KEY = os.getenv("HOST_KEY")


# General Functions
def cls():
    os.system('cls')


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


def create_id(id_len: int=16, include_puntuations: bool=False):
    r_file = os.path.join('Database', 'log_file_names.txt')

    with open(r_file, 'r') as log_file:
        available_logs = log_file.readlines()

    for i in available_logs:
        available_logs[available_logs.index(i)] = i[:-1]

    while True:
        if include_puntuations is False:
            uid = ''.join(
                random.choice(string.ascii_letters + string.digits) 
                for _ in range(id_len))
        
        elif include_puntuations is True:
            uid = ''.join(
                random.choice(string.ascii_letters + string.digits + string.punctuation) 
                for _ in range(id_len))
        
        if uid in available_logs: continue
        else: 
            with open(r_file, 'a') as log_file: log_file.write(f'{uid}\n')
            break
    
    return uid


def google_authentication(OTP: pyotp.TOTP, userID: str):
    auth_det = OTP.provisioning_uri(name=f'{userID}', issuer_name=f'CanteenFastCard')
    auth_qr = qrcode.make(auth_det)

    auth_qr.save(f'static/auth/{userID}.jpg')


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


def close_db(connection: sqlite3.Connection, cursor: sqlite3.Cursor):
    cursor.close()
    connection.close()


def read_database_file(db: sqlite3.Connection, table_name_or_hint: str, _columns: list=...):
    sql = db.cursor()

    if table_name_or_hint == 'account': 
        sql.execute('SELECT * FROM student_account')
        data = sql.fetchall()

        return pandas.DataFrame(data, columns=['ID', 'Pin', 'Amount'])

    elif table_name_or_hint == 'info': 
        sql.execute('SELECT * FROM student_info')
        data = sql.fetchall()

        return pandas.DataFrame(data, columns=['ID', 'USID', 'Name', 'Email'])
        
    else:
        try:
            sql.execute(f"SELECT * FROM '{table_name_or_hint}'")
            data = sql.fetchall()

            return pandas.DataFrame(data, columns=_columns)

        except Exception as E:
            return E


def get_student_details(db: sqlite3.Connection, _id: int, give: str):
    sql = db.cursor()

    sql.execute(f'SELECT pin_code, amount FROM student_account WHERE id={_id}')
    std_bank_info = sql.fetchone()

    sql.execute(f'SELECT usid, student_name, email FROM student_info WHERE id={_id}')
    std_info = sql.fetchone()
    
    if give == 'usid': return std_info[0]
    elif give == 'name': return std_info[1]
    elif give == 'email': return std_info[2]
    elif give == 'amount': return int(std_bank_info[1])
    elif give == 'pin_code': return std_bank_info[0]
    elif give == 'std_info': return std_info
    elif give == 'std_bank_info': return std_bank_info


def scan_ids(db: sqlite3.Connection, _id: int):
    sql = db.cursor()
    exist = False

    try:
        sql.execute('SELECT id FROM student_account')
        ids = sql.fetchall()

    except sqlite3.IntegrityError: pass

    for id in ids:
        if int(_id) == int(id[0]): exist = True; break
        else: continue

    return exist


def register_student(db: sqlite3.Connection, _id: int, pin_code: str, init_amount: int, student_info: list=['student name', 'student email']):
    
    sql = db.cursor()

    date = datetime.datetime.now().strftime('%d-%m-%Y')
    usid = create_id()
    name = student_info[0]
    email = student_info[1]

    try:
        sql.execute(f'''INSERT INTO student_account (id, pin_code, amount) 
                    VALUES (?, ?, ?)''', (int(_id), pin_code, init_amount,))
        
        sql.execute(f'''INSERT INTO student_info (id, usid, student_name, email) 
                    VALUES (?, ?, ?, ?)''', (int(_id), usid, name, email,))


        try:
            log_file = f'Database/logs/{usid}.txt'

            with open(log_file, 'a') as file:
                file.write(f'Account Log of: {name}\n')
                file.write(f'Registerd on: {date}\n')
                file.write(f'Personal Email: {email}\n')
                file.write(f'Initial/Opening Balance: Rs.{str(init_amount)}\n\n')
                file.write('*'*26 + '\n\n')

                send_mail(db, _id, 'register')

        except FileNotFoundError as FNE: cprint(f'Failed to register student: {FNE}', 'red', attrs=['bold'])

    except sqlite3.IntegrityError as IE: cprint(f'Student already registered!', 'red', attrs=['bold'])
    finally: db.commit()


def register_admin(db: sqlite3.Connection, ssid: int, password: str, email: str):
    sql = db.cursor()

    try:
        sql.execute('''INSERT INTO admin_logins(SSID, Password, Email) 
                    VALUES (?, ?, ?)''', (ssid, password, email))
        db.commit()
        
        return True

    except Exception as E:
        return E


def debit_balance(db: sqlite3.Connection, debit_amount: int, _id: int):
    sql = db.cursor()

    date = datetime.datetime.now().strftime('%d-%m-%Y')

    try:
        # sql.execute(f'SELECT amount FROM bank WHERE id={_id}')
        std_amount = get_student_details(db, _id, 'amount')
        
        if std_amount < debit_amount:
            cprint('\nLow balance!', 'red', attrs=['bold'])
            print(f"Amount left in account: {colored(f'Rs.{std_amount}', 'red', attrs=['bold'])}")
        
        if std_amount <= 10:
            send_mail(db, _id, 'low-balance', std_amount)
        
        else:

            final_amount = std_amount - debit_amount
            
            if final_amount <= 10:
                send_mail(db, _id, 'low-balance', final_amount)

            sql.execute(f'UPDATE student_account SET amount={final_amount} WHERE id={_id}')

            w_file = os.path.join('Database\\logs\\', str(get_student_details(db, _id, 'usid')) + '.txt')

            with open(w_file, 'a') as file:
                file.write(f'Date: {date}\n')
                file.write(f'Bought item(s) of amount: Rs.{debit_amount}\n')
                file.write(f'Amount left in amount: Rs.{final_amount}\n\n')
            
            send_mail(db, _id, 'debit', (debit_amount, final_amount))
    
    except sqlite3.IntegrityError as IE: cprint(f'Failed to debit balance: {IE}', 'red', attrs=['bold'])
    finally: db.commit()


def update_balance(db: sqlite3.Connection, update_amount: int, _id: int):
    sql = db.cursor()

    date = datetime.datetime.now().strftime('%d-%m-%Y')

    std_amount = get_student_details(db, _id, 'amount')

    final_amount = std_amount + update_amount

    sql.execute(f'UPDATE student_account SET amount={final_amount} WHERE id={_id}')

    w_file = 'Database/logs/' + str(get_student_details(db, _id, 'usid')) + '.txt'

    with open(w_file, 'a') as file:
        file.write(f'Date: {date}\n')
        file.write(f'Amount deposited: Rs.{update_amount}\n')
        file.write(f'Total amount in account: Rs.{final_amount}\n\n')

    send_mail(db, _id, 'update', (update_amount, final_amount))

    db.commit()

    return final_amount


def send_mail(db: sqlite3.Connection, _id: int, mail_type: str, args=tuple):
    std_info = get_student_details(db, _id, 'std_info')
    pin_code = get_student_details(db, _id, 'pin_code')
    date = datetime.datetime.now().strftime('%d-%m-%Y')

    usid = std_info[0]
    name = std_info[1]
    std_email = std_info[2]

    message = MIMEMultipart()

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
        std_log_file = 'Database/logs/' + usid + '.txt'

        try:
            # Open PDF file in binary mode
            with open(std_log_file, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)

            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {std_log_file}",
            )

            message.attach(part)

        except smtplib.SMTPException: cprint(f'Failed to attach log file!\n', 'red', attrs=['bold'])

    elif mail_type == 'register':
        date = datetime.datetime.now().strftime('%d-%m-%Y')

        subject = "KIIT Polytechnic Canteen Registration"

        body = f"""This mail contains information about your canteen registration.
Please go through the details.
If you have any query(ies), please reply back your query(ies) to the following email address: {HOST_SSID}

===============================================================

Registerd on: {date}
Registered ID: {_id}
Pin Code: {pin_code}
Registered Name: {name}
Registered Email: {std_email}
Your Student UID (usid): {usid}

[NOTE: usid is used to create yout transaction log file. Keep your usid safe somewhere, 
you request your transaction log file by providing your usid. And do download and read 
the attached file. The file contains some frequently asked Questions.]


Thanks for registering.
KIIT KP Canteen
"""
        std_log_file = os.path.join('Database', 'readME.txt')

        try:
            # Open PDF file in binary mode
            with open(std_log_file, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)

            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {std_log_file}",
            )

            message.attach(part)

        except smtplib.SMTPException: cprint(f'Failed to attach log file!\n', 'red', attrs=['bold'])

    elif mail_type == 'low-balance':
        subject = "KIIT Polytechnic Canteen Low Balance"

        body = f"""This mail contains information about your canteen balance.
Please go through the details.
If you have any query(ies), please reply back your query(ies) to the following email address: {HOST_SSID}

===============================================================

Registered ID: {_id}
Registered Name: {name}
Registered Email: {std_email}

This mail is sent to imform you that, your canteen balance is low.
You have Rs.{args} left in your canteen account.

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
Registered Email: {std_email}

This mail is sent to imform you that, Rs. {args[0]} have been debited from your canteen account.
Amount left in your account is Rs. {args[1]}.

If you're not familiar with the transaction. Report this to any of the the canteen employee.

If you want your transaction log file, please email your usid to the following email address: {HOST_SSID}.
Your Log file will be sent to you within 24 Hours.

[NOTE: If you want your transaction log file ASAP, you can scan your id card at the canteen.]

Thank You!.
KIIT KP Canteen
"""

    elif mail_type == 'update':
        subject = "KIIT Polytechnic Canteen Deposite"

        body = f"""This mail contains information about your canteen balance.
Please go through the details.
If you have any query(ies), please reply back your query(ies) to the following email address: {HOST_SSID}

===============================================================

Registered ID: {_id}
Registered Name: {name}
Registered Email: {std_email}

This mail is sent to imform you that, Rs. {args[0]} has been deposited/updated into your canteen account.
Total amount in your canteen account is Rs. {args[1]}.

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
Your PIN-CODE reset 2FA code is: {args}.

[NOTE: If you didn't requested for PIN-CODE reset, please don't share this 2FA code with anyone.]
"""

    elif mail_type == 'pin_code_update':
        subject = "KIIT Polytechnic Canteen Pin-Code update"

        body = f"""Your canteen FastCard account PIN-CODE was reset on {date}.
Your new PIN-CODE is: {args}.

[NOTE: If you didn't reset the PIN-CODE, please inform this to any canteen employee.]
"""

    try:  
        message["From"] = HOST_SSID
        message["To"] = std_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))
        
        text = message.as_string()
        context = ssl.create_default_context()

        with smtplib.SMTP_SSL(SMTP_SERVER, int(SERVER_PORT), context=context) as server:
            server.login(HOST_SSID, HOST_KEY)
            server.sendmail(HOST_SSID, std_email, text)

        if mail_type == 'log': cprint("DONE!", 'green', attrs=['bold'])
        else: ...

    except smtplib.SMTPException as smtpe: cprint(f'Failed!\nDue: {smtpe}', 'red', attrs=['bold'])
    except TimeoutError as te: cprint(f'Failed!\nDue: {te}', 'red', attrs=['bold'])


def send_2FA_2_admin(admin_email: str, twoFA_code: str, mail_for: str='login'):
    try:
        message = MIMEMultipart()
        
        body = f"""Your 2FA Code for {mail_for} is: {twoFA_code}"""

        message["From"] = HOST_SSID
        message["To"] = admin_email
        
        if mail_for == 'login': message["Subject"] = '2FA Code-Canteen Admin Login'
        elif mail_for == 'pswd-reset': message["Subject"] = '2FA Code-Canteen Password Reset'
        else: message["Subject"] = '2FA Code-Canteen Server Shutdown'

        message.attach(MIMEText(body, "plain"))
        
        text = message.as_string()
        context = ssl.create_default_context()

        with smtplib.SMTP_SSL(SMTP_SERVER, int(SERVER_PORT), context=context) as server:
            server.login(HOST_SSID, HOST_KEY)
            server.sendmail(HOST_SSID, admin_email, text)

    except smtplib.SMTPException as smtpe: cprint(f'Failed!\nDue: {smtpe}', 'red', attrs=['bold'])
    except TimeoutError as te: cprint(f'Failed!\nDue: {te}', 'red', attrs=['bold'])