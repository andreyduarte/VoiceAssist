import random
import time
import openai
import json
from threading import Thread, current_thread

# Terminate the process
from pyaudio import PyAudio, paInt16
import pyscreenshot as ImageGrab
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
    def __init__(self):
        self.sys_prompt = """
Você é uma assistente de voz inteligente que usa o histórico da conversa e a screenshot atual do usuário para responder às suas perguntas.

REGRAS:
    Use apenas ferramentas listadas acima.
    Use ferramentas apenas quando necessário.
    Responda de forma concisa e direta. 
    Seja amigável e prestativa. 
    Mostre alguma personalidade e evite ser muito formal.

Use o seguinte formato de resposta:
{
    'imagem_relevante': Boolean, # Se o conteúdo da imagem é relevante para responder à mensagem
    'fala': String, # Texto a ser transformada em audio e enviado para o usuário.
}
        """
        self.history = []
        self.model = genai.GenerativeModel(
          model_name="gemini-1.5-flash-latest",
          safety_settings=safety_settings,
          generation_config=generation_config,
          system_instruction=self.sys_prompt
        )
        self.talking = False
        self.running = True

    def __enter__(self):
        self.recorder = AudioToTextRecorder(model = 'base', language='pt')
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
    
    # Funções de Geração
    def generate(self, text, image):
        while True:
            try:
                phrase_start = random.choice(['Ahmmmmm......', 'Vejamos......', 'Hmmmmm......', 'Certo......', 'Deixa eu ver......'])
                self.talking = True
                self.talk_thread = Thread(target=self.talk, args=(phrase_start,1,))
                self.talk_thread.start()
                self.talk_thread.join()
                return json.loads(self.model.generate_content([image, text]).text)
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
        self.answer(input_text, ImageGrab.grab())

        # Continua a rodar
        self.run()

    def answer(self, prompt, imagem):
        # Evita mensagens em branco
        if len(prompt) < 0:
            return 
        
        # Adiciona a pergunta ao histórico
        self.history.append({ "role": "user", "content": prompt })
        print(f'Usuário: {prompt}')

        # Gera uma resposta
        result = self.generate(self.make_prompt(), imagem)

        # Exibe texto e gera audio da resposta
        print(f'Assistente: {result["fala"]}')
        self.talking = True
        self.talk_thread = Thread(target=self.talk, args=(result["fala"],))
        self.talk_thread.start()

        # Adiciona a resposta ao histórico
        self.history.append({ "role": "assistant", "content": result["fala"] })

    def listen(self):
            print('Ouvindo...')
            self.handle_command(self.recorder.text())

    # Funções de Fala
    def talk(self, response, speed = 1.10):
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