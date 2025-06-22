
LOG_TYPES = {
    'info': '"\033[36mINFO:\033[0m"',
    'warning': "\033[WARNING:\033[0m",
    'error': '"\033[31mERROR:\033[0m"'
}

LOG_LEVEL = 3

def print_log(text, type = 'info', level = 3, title = ''):
    
    if level <= LOG_LEVEL:
        if title:
            print(f'---{title}---')
        print(f"{LOG_TYPES[type]} {text}\n")
    







# print("\033[31mTexto vermelho\033[0m")
# print("\033[32mTexto verde\033[0m")
# print("\033[33mTexto amarelo\033[0m")
# print("\033[34mTexto azul\033[0m")
# print("\033[35mTexto magenta\033[0m")
# print("\033[36mTexto ciano\033[0m")
# print("\033[1mTexto em negrito\033[0m")