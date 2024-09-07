from dotenv import load_dotenv
from assistant import Reacter
import keyboard

if __name__ == '__main__':
    # Carrega as variáveis de ambiente
    load_dotenv()

    # Inicializa o assistente
    with Reacter() as assistant:
        keyboard.add_hotkey('alt+\'', lambda: assistant.stop())
        assistant.react()