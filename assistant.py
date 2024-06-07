import time
import openai
from threading import Thread, current_thread

# Terminate the process
from pyaudio import PyAudio, paInt16
import pyscreenshot as ImageGrab
import google.generativeai as genai
from RealtimeSTT import AudioToTextRecorder

# Configurações do Gemini
generation_config = {
  "temperature": 0.7,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 512,
  "response_mime_type": "text/plain",
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
    def __init__(self):
        self.sys_prompt = """
Você é um assistente inteligente que usará o histórico da conversa e a imagem fornecida pelo usuário para responder às suas perguntas.
Responda de forma concisa e direta. Não use emoticons ou emojis. Não faça perguntas ao usuário.
Seja amigável e prestativo. Mostre alguma personalidade e evite ser muito formal.
        """
        self.history = []
        self.model = genai.GenerativeModel(
          model_name="gemini-1.5-flash-latest",
          safety_settings=safety_settings,
          generation_config=generation_config,
          system_instruction=self.sys_prompt
        )
        self.recorder = AudioToTextRecorder(language='pt', spinner=False)
        self.talking = False
        self.running = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.recorder.shutdown()
        if self.talking:
            self.talking = False
            self.talk_thread.alive = False
            self.talk_thread.join()

    def run(self):
        while self.running:
            self.listen()

    def handle_command(self, input_text):
        if self.talking:
            self.talking = False
            self.talk_thread.alive = False
            self.talk_thread.join()

        # Se for um comando em linguagem natural
        self.answer(input_text)

        # Continua a rodar
        self.run()

    def answer(self, prompt):
        # Adiciona a pergunta ao histórico
        self.history.append({ "role": "user", "content": prompt })

        # Obtém a imagem atual da tela
        image = ImageGrab.grab()

        # Gera uma resposta
        result = self.generate(self.make_prompt(), image)
        # Exibe e gera audio da resposta
        print(f'Assistente: {result}')
        self.talking = True
        self.talk_thread = Thread(target=self._tts, args=(result,))
        self.talk_thread.start()

        # Adiciona a resposta ao histórico
        self.history.append({ "role": "assistant", "content": result })

    def generate(self, text, image):
        while True:
            try:
                return self.model.generate_content([text, image]).text
            except Exception as e:
                print(f'Erro ao gerar resposta: {e}')
                time.sleep(2)

    def make_prompt(self):
        prompt = ""
        for message in self.history:
            prompt += f"{message['role']}: {message['content']}\n"
        return prompt
    
    def listen(self):
            self.handle_command(self.recorder.text())

    def _tts(self, response):
        player = PyAudio().open(format=paInt16, channels=1, rate=24000, output=True)

        local_thread = current_thread()
        local_thread.alive = True

        with openai.audio.speech.with_streaming_response.create(
            model="tts-1",
            voice="nova",
            response_format="pcm",
            input=response,
            speed=1.25
        ) as stream:
            for chunk in stream.iter_bytes(chunk_size=1024):
                if local_thread.alive:
                    player.write(chunk)
                else:
                    break
            player.close()