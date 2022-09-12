import os
from os import system as cle


def files():
    files_and_dir = ['Database/logs', 
                     'Database/kiit_kp_canteen.db',  
                     'Database/log_file_names.txt', 
                     'Database/preparing_errors.txt', 
                     'Database/website_info.env']

    os.mkdir('Database')
    
    for file in files_and_dir:
        try: open(file, 'x').close()
        except Exception: open(file, 'w').close()
    
    with open('Database/website_info.env', 'a') as env_file:
        env_file.write("# VARIABLES FOR RUNNING THE WEBSITE\n")
        env_file.write("HOST='1.1.1.1'\n")
        env_file.write("PORT=2468\n")
        env_file.write("DEBUG=False\n\n")

        env_file.write("# VARIABLES FOR E-MAIL SERVICE\n")
        env_file.write('SMTP_SERVER = "smtp.gmail.com"\n')
        env_file.write('SERVER_PORT = "465"\n')
        env_file.write("HOST_KEY = 'app password'\n")
        env_file.write("HOST_SSID = 'service email'\n")

        env_file.write("# ADMIN EMAIL\n")
        env_file.write('MASTER_2FA_EMAIL = "master email ID"\n')


def libs():
    with open('requirements.txt', 'r') as module_file:
        modules = module_file.readlines()


    for index, element in enumerate(modules):
        if '\n' in element:
            modules[index] = element.replace('\n', '')


    for module in modules:
        try: cle(f'pip install {module}')
        except Exception as E: 
            with open('Database/prepareing_errors.txt', 'a') as error_file:
                error_file.write(f'{E}\n')


input = input('Prepare: ')
if input in ('dir', 'files'): files()
elif input in ('env', 'libs', 'modules'): libs()
elif input == 'dir, libs': dir(); libs()