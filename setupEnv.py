import os
import pathlib

try: from dotenv import set_key
except ImportError: os.system('pip install python-dotenv'); from dotenv import set_key;

databaseDirDirs = ['cache', 'logs']
databaseDirFiles = ['cfc_userDatabase.db',
                    'log_file_names.txt',]

siteEnvKeys = [
    "MASTER_PROCESS_KEY",
    "MASTER_EMAIL",
    "HOST_SSID",
    "HOST_PSWD",
    "SERVER_PORT",
    "SMTP_SERVER",
    "DEBUG",
    "PORT",
    "HOST"
]

# code to make `Database` file in the Root directory
try: os.mkdir('./Database')
except OSError: pass

# for-loop to create sub-directories in the database directory
for dir in databaseDirDirs:
    try: os.mkdir(f'Database/{dir}')
    except OSError: pass

# for-loop to create files in the database directory
for file in databaseDirFiles:
    try: open(f'Database/{file}', 'x').close()
    except OSError: pass

# for-loop to create `.env` and setting up the env variables
open('site_settings.env', 'x').close()
for key in siteEnvKeys[::-1]:
    try: set_key('site_settings.env', key, 'VALUE')
    except KeyError: pass