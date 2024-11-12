import librosa
import keyboard
import sys
import numpy as np

def check_time(start, end):
    if start is not None or end is not None:
        if start < 0 or end < 0 or start >= end:
            return False
        else:
            return True
        
def get_args(args):
    args = args.split(' ')
    path = args[0]
    if len(args) == 4:
        start_ms = int(args[1])
        end_ms = int(args[2])
        state = check_time(start_ms, end_ms)
        if state: pass
        else: raise ValueError('Время имеет неправильное значение')

        if args[3].lower() == 'cuda': device = 'cuda'
        elif args[3].lower() == 'cpu': device = 'cpu'
        else: raise ValueError('device может быть CUDA или CPU')
        file = load_file(path, start_ms=start_ms, end_ms=end_ms)
        return (file, device)

    elif len(args) == 2:
        if args[1].lower() == 'cuda': device = 'cuda'
        elif args[1].lower() == 'cpu': device = 'cpu'
        else: raise ValueError('device может быть CUDA или CPU')
        file = load_file(path)
        return (file, device)

def load_file(path, start_ms=None, end_ms=None):
    file, _ = librosa.load(path, sr=16000, offset=((start_ms / 1000) if start_ms else None), duration=(((end_ms - start_ms) / 1000) if end_ms else None), mono=True)
    non_silent_intervals = librosa.effects.split(file, top_db=30)
    audio_without_silence = np.concatenate([file[start:end] for start, end in non_silent_intervals])
    return audio_without_silence

def save_file(result):
    with open('результат.txt', 'w', encoding='utf-8') as text_file:
        text_file.write(result["text"])

def exit():
    keyboard.add_hotkey('ctrl+c', lambda: sys.exit())