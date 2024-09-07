import tkinter as tk
import time
from threading import Thread
import keyboard

BG_COLOR = "#000000"
WHITE = "#EAECEE"
BLACK = "#000000"

# Define font styles
FONT = "Roboto 12"

class ChatApp:
    def __init__(self, master, assistant):
        self.master = master
        self.assistant = assistant
        self.master.root.attributes("-alpha", 0.65)
        self.visible = True
        self.send_thread = None

        # Set window title
        self.master.root.title("Chat")

        # Create chat frame
        self.chat_frame = tk.Frame(self.master.root, bg=BG_COLOR)
        self.chat_frame.pack(fill="both", expand=True)

        # Create chat area
        self.chat_area = tk.Text(self.chat_frame, fg=WHITE, bg=BG_COLOR,
                                  font=FONT, state="disabled", wrap='word', height=10, width=50, padx=15, pady=15)
        self.chat_area.pack(fill="both", expand=True)

        # Create message input area
        self.msg_frame = tk.Frame(self.chat_frame)
        self.msg_frame.pack(fill="x")

        self.msg_entry = tk.Entry(self.msg_frame, fg=WHITE, bg=BG_COLOR,
                                  font=FONT)
        self.msg_entry.pack(side="left", fill="x", expand=True)

        # Bind Enter key to send message
        self.msg_entry.bind("<Return>", lambda event: self.send_async())

    def send_async(self):
        self.send_thread = Thread(target=self.send_message)
        self.send_thread.start()

    def update_chat(self):
        self.chat_area.config(state="normal")
        self.chat_area.delete(1.0, tk.END)
        for msg in self.assistant.history:
            if msg["role"] == "user":
                self.chat_area.insert(tk.END, f'[{time.strftime("%H:%M:%S", time.localtime())}] Eu:\n{msg["content"]}\n\n')
            else:
                self.chat_area.insert(tk.END, f'[{time.strftime("%H:%M:%S", time.localtime())}] Assistente:\n{msg["content"]}\n\n')
        self.chat_area.config(state="disabled")

    def send_message(self):
        message = self.msg_entry.get()
        if message:
            # Clear message input
            self.msg_entry.delete(0, tk.END)
            
            # Update chat area
            self.update_chat()

            self.assistant.answer(message)

            # Update chat area
            self.update_chat()

            # Scroll to bottom
            self.chat_area.see(tk.END)

    def clear_chat(self):
        self.assistant.history = []
        self.update_chat()

    def toggle_ui(self):
        if self.visible:
            self.master.hide()
            self.visible = False
        else:
            self.master.show()
            self.visible = True
            self.master.focus()
            self.msg_entry.focus_force()

    def hook_hotkeys(self):
        keyboard.add_hotkey('alt+\'', self.toggle_ui)
        keyboard.add_hotkey('alt+q', self.clear_chat)