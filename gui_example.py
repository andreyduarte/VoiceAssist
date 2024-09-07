from gui import ChatApp
from dotenv import load_dotenv
from assistant import Assistant
from overlay import Window
import keyboard

if __name__ == '__main__':
    # Carrega as variáveis de ambiente
    load_dotenv()
    
    # Create chat window
    win = Window(draggable=False)

    # Position the chat window in the right corner
    win.root.geometry("300x400")
    win.root.geometry("+1050+100")
    
    # Inicializa o assistente
    with Assistant(voice_control=False, tts=True) as assistant:
        # Create chat app instance
        chat = ChatApp(win, assistant)
        # Hook the Keypresses
        chat.hook_hotkeys()
        # Launch the overlay
        win.launch()