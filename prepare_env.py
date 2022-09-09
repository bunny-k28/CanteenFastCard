from os import system as cle

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