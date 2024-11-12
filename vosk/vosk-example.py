from vosk import KaldiRecognizer, Model, GpuInit
from pyaudio import PyAudio, paInt16
import json

model = Model('small_model')
rec = KaldiRecognizer(model, 44100)
GpuInit()
audio = PyAudio()
stream = audio.open(rate=44100, channels=1, format=paInt16, input=True)
stream.start_stream()

def listen():
    while True:
        data = stream.read(4000, exception_on_overflow=False)
        if rec.AcceptWaveform(data) and len(data) > 0:
            result = json.loads(rec.Result())
            if result['text']:
                yield result['text']

def recog(file):
    #data = wave.open(file, 'rb')
    data = open(file, 'rb').read()
    #dataBytes = data.readframes(data.getframerate())
    if rec.AcceptWaveform(data):
        result = json.loads(rec.Result())
        if result['text']:
            return result['text']

print(recog('../sample1.wav'))
#print(recog('sample1.wav'))