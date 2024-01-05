import os
from dotenv import set_key

databaseDirDirs = ['cache', 'logs']
databaseDirFiles = ['cfc_userDatabase.db',
                    'feedback.txt',
                    'log_file_names.txt',]

siteEnvKeys = [
    "MASTER_PROCESS_KEY",
    "MASTER_PRODUCT_KEY",
    "MASTER_2FA_EMAIL",
    "HOST_SSID",
    "HOST_PSWD",
    "SERVER_PORT",
    "SMTP_SERVER",
    "DEBUG",
    "PORT",
    "HOST"
]


os.mkdir('Database')
for dir in databaseDirDirs:
    os.mkdir(dir)

for file in databaseDirFiles:
    open(f'Database/{file}', 'x').close()

open('site_settings.env', 'x').close()
for key in siteEnvKeys[::-1]:
    set_key('site_settings.env', key, 'VALUE')