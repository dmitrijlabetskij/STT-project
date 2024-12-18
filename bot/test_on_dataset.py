import pandas as pd
import jiwer
import librosa
import re
import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline


def whisper(path):
    path = f'dataset/clips/{path}.mp3'
    audio, _ = librosa.load(path, sr=16000, mono=True)
    result = pipe(audio)
    return result

def count_wer():
    wers = []
    for i in range(len(data)):
        path = path_data.at[i, 'path']
        hyp = whisper(path)['text']
        ref = sent_data.at[i, 'sentence']
        ref = re.sub(r'[^\w\s]', '', ref).strip().lower()
        hyp = re.sub(r'[^\w\s]', '', hyp).strip().lower()
        wer = jiwer.wer(ref, hyp)
        wers.append(wer)

    return sum(wers) / len(wers)

if __name__ == '__main__':
    data = pd.read_csv('dataset/validated.tsv', sep='\t')
    path_data = data[['path']]
    sent_data = data[['sentence']]

    torchdType = torch.float16
    device = 'cuda'

    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        'openai/whisper-large', torch_dtype=torchdType, use_safetensors=True
    )
    model.to(device)
    processor = AutoProcessor.from_pretrained('openai/whisper-large')
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
    wer = count_wer()
    print(round(wer, 3))