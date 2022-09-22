import os
from os import system as cle


def files():
    files_and_dir = ['static/auth',
                     'Database/logs', 
                     'Database/kiit_kp_canteen.db',  
                     'Database/log_file_names.txt', 
                     'Database/website_info.env']

    try: os.mkdir('Database')
    except OSError: pass
    
    for file in files_and_dir[0:2]:
        try: os.mkdir(file)
        except Exception: pass

    for file in files_and_dir[2:]:
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
        env_file.write("HOST_SSID = 'service email'\n\n")

        env_file.write("# MASTER VARIABLES\n")
        env_file.write('MASTER_2FA_EMAIL = "master email ID"\n')
        env_file.write('MASTER_PRODUCT_KEY = "master product key"\n')
        env_file.write('MASTER_PROCESS_KEY = "master process key"\n')


def libs():
    with open('requirements.txt', 'r') as module_file:
        modules = module_file.readlines()


    for index, element in enumerate(modules):
        if '\n' in element:
            modules[index] = element.replace('\n', '')


    for module in modules:
        try: cle(f'pip install {module}')
        except Exception: print(f'Could not install {module}')


input = input('Prepare: ')
if input in ('dir', 'files'): 
    print('Preparing all files and directories...', end='')
    files()
    print('✅')

elif input in ('libs', 'modules'): 
    print('Preparing all libraries and modules...', end='')
    libs()
    print('✅')

elif input == 'env': 
    print('Preparing your environment...', end='')
    files(); libs()
    print('✅')