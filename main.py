from dotenv import load_dotenv
from assistant import Assistant

if __name__ == '__main__':
    # Carrega as variáveis de ambiente
    load_dotenv()

    # Inicializa o assistente
    with Assistant() as assistant:
        assistant.run()