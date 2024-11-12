import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
import librosa
import time

torchdType = torch.float32
running = True

def check_time(start, end):
    if start is not None or end is not None:
        if start < 0 or end < 0:
            raise ValueError('Время должно быть больше 0.')
        elif start >= end:
            raise ValueError('Конечное время должно быть больше начального.')
        else:
            return True

while running:
    '''parser = argparse.ArgumentParser()
    parser.add_argument('--file', type=str, help='Путь к вашему mp3-файлу', required=True)
    parser.add_argument('--start_ms', type=int, help='Время начала фрагмента в миллисекундах', required=False)
    parser.add_argument('--end_ms', type=int, help='Время окончания фрагмента в миллисекундах', required=False)
    parser.add_argument('--device', type=str, help='CPU/CUDA', required=True)

    args = parser.parse_args()'''
    args = input('file, start_ms, end_ms, device\n').split(' ')
    filepath = args[0]
    if len(args) == 4:
        start_ms = int(args[1])
        end_ms = int(args[2])
        state = check_time(start_ms, end_ms)
        if args[3].lower() == 'cuda': device = 'cuda'
        elif args[3].lower() == 'cpu': device = 'cpu'
        else: raise ValueError('device может быть CUDA или CPU')
    elif len(args) == 2:
        if args[1].lower() == 'cuda': device = 'cuda'
        elif args[1].lower() == 'cpu': device = 'cpu'
        else: raise ValueError('device может быть CUDA или CPU')

    start_time = time.time()
    
    file, sr = librosa.load(args[0], sr=16000, offset=((start_ms / 1000) if len(args) == 4 and state else None), duration=(((end_ms - start_ms) / 1000) if len(args) == 4 and state else None), mono=True)

    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        'openai/whisper-large', torch_dtype=torchdType, low_cpu_mem_usage=True, use_safetensors=True
    )

    model.to(device)
    processor = AutoProcessor.from_pretrained('openai/whisper-medium')

    pipe = pipeline(
        'automatic-speech-recognition',
        model='openai/whisper-large',
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        max_new_tokens=128,
        return_timestamps=True,
        batch_size=16,
        torch_dtype=torchdType,
        device=device
    )


    result = pipe(file)

    with open('результат.txt', 'w', encoding='utf-8') as text_file:
        text_file.write(result['text'])

    print('Successful')
    print(time.time() - start_time)