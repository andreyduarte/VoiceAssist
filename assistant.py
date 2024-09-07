import random
import time
import openai
import json
from threading import Thread, current_thread

from vision import Vision
from pyaudio import PyAudio, paInt16
import google.generativeai as genai
from RealtimeSTT import AudioToTextRecorder

# Configurações do Gemini
generation_config = {
  "temperature": 0.8,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 1024,
  "response_mime_type": "application/json",
}
safety_settings = [
  {
    "category": "HARM_CATEGORY_HARASSMENT",
    "threshold": "BLOCK_NONE",
  },
  {
    "category": "HARM_CATEGORY_HATE_SPEECH",
    "threshold": "BLOCK_NONE",
  },
  {
    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
    "threshold": "BLOCK_NONE",
  },
  {
    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
    "threshold": "BLOCK_NONE",
  },
]

class Assistant:
    def __init__(self, voice_control = True, tts = True, vision_buffer = 5, vision_fps = 0.5):
        self.sys_prompt = """
These are frames of a videofeed of the user's screen, observe each frame with attention.
Você é uma assistente de voz inteligente que usa o feed de video para responder às suas perguntas do usuário.

REGRAS:
    Responda de forma concisa e direta, usando todo o videofeed como contexto. 
    Seja amigável e prestativa, mostre alguma personalidade e evite ser muito formal.

Use o seguinte formato de resposta:
{   
    'fala': String, # Texto a ser transformado em audio e reproduzido para o usuário.
}
        """
        self.history = []
        self.vision = Vision(fps=vision_fps, buffer = vision_buffer, width=1366, height=768)
        self.tts = tts
        self.voice_control = voice_control
        self.model = genai.GenerativeModel(
          model_name="gemini-1.5-flash-latest",
          safety_settings=safety_settings,
          generation_config=generation_config,
          system_instruction=self.sys_prompt
        )
        self.talking = False
        self.running = True

    def __enter__(self):
        self.vision.start()
        if self.voice_control: self.recorder = AudioToTextRecorder(model = 'tiny', language='pt', spinner=False)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.recorder.shutdown()
        self.vision.stop()
        if self.talking:
            self.talking = False
            self.talk_thread.alive = False
            self.talk_thread.join()

    def run(self):
        while self.running and self.voice_control:
            self.listen()
    
    # Funções de Geração
    def generate(self, text, image):
        while True:
            try:
                #if self.tts: self.say(random.choice(['Aaahmmmmm...', 'Hmmmmm......', 'Um momento, por favor...']), speed=0.8)
                return json.loads(self.model.generate_content([*image, text]).text)
            except Exception as e:
                print(f'Erro ao gerar resposta: {e}')
                time.sleep(2)

    def make_prompt(self):
        prompt = ""
        for message in self.history:
            prompt += f"{message['role']}: {message['content']}\n"
        return prompt

    # Funções de Interface
    def handle_command(self, input_text):
        # Se estiver falando, para
        if self.talking:
            self.stop_talk()
            
        # Se for encerrar, sai
        if input_text.lower().strip(' .') == "finalizar conversa":
            self.running = False
            return

        # Se for um comando em linguagem natural
        # Obtém a o texto transcrito e a imagem atual da tela
        self.answer(input_text)

        # Continua a rodar
        self.run()

    def answer(self, prompt):
        # Evita mensagens em branco
        if len(prompt) < 0:
            return 
        
        # Adiciona a pergunta ao histórico
        self.history.append({ "role": "user", "content": prompt })
        print(f'Usuário: {prompt}')

        # Gera uma resposta
        result = self.generate(self.make_prompt(), self.vision.get_imgs())

        # Exibe texto e gera audio da resposta
        print(f'Assistente: {result["fala"]}')
        if self.tts: self.say(result["fala"])

        # Adiciona a resposta ao histórico
        self.history.append({ "role": "assistant", "content": result["fala"] })

    def listen(self):
            print('Ouvindo...')
            self.handle_command(self.recorder.text())

    # Funções de Fala
    def say(self, text, speed = 1):
        self.talking = True
        self.talk_thread = Thread(target=self._tts, args=(text,speed,))
        self.talk_thread.start()
        self.talk_thread.join()

    def _tts(self, response, speed = 1):
        player = PyAudio().open(format=paInt16, channels=1, rate=24000, output=True)

        local_thread = current_thread()
        local_thread.alive = True

        with openai.audio.speech.with_streaming_response.create(
            model="tts-1",
            voice="nova",
            response_format="pcm",
            input=response,
            speed=speed
        ) as stream:
            for chunk in stream.iter_bytes(chunk_size=1024):
                if local_thread.alive:
                    player.write(chunk)
                else:
                    break
            player.close()

    def stop_talk(self):
        self.talking = False
        self.talk_thread.alive = False
        self.talk_thread.join()

class Reacter(Assistant):
    def __init__(self, delay_time = 5, voice_control = False, tts = True):
        self.delay_time = delay_time
        super().__init__(voice_control, tts, vision_buffer = delay_time, vision_fps=1)
        self.sys_prompt = """
These are frames of a videofeed of the user's screen.
You must observe and anotate in great detail the users actions in the videofeed.
You must also take note of the content of the videofeed.
You must never talk directly to the user, only make notes of his every move.
Use the following format:
{   
    ""
    "new_note": String, # Note describing the user's actions in great detail.
    "thoughts": String, # Thoughts on why the user is doing so.
}"""
        self.model = genai.GenerativeModel(
          model_name="gemini-1.5-flash-latest",
          safety_settings=safety_settings,
          generation_config=generation_config,
          system_instruction=self.sys_prompt
        )

    def react(self):
        print('Reacting...')
        while self.running:
            time.sleep(self.delay_time)
            comentary = self.generate(self.make_prompt(), self.vision.get_imgs())
            self.history.append({ "role": "assistant", "content": comentary['new_note'] })
            print(f'Assistente: {comentary["new_note"]}')
            self.say(comentary['new_note'])

    def stop(self):
        self.running = False

    def make_prompt(self):
        prompt = "Notes so far:\n"
        for message in self.history:
            prompt += f"* {message['content']}\n"
        return prompt