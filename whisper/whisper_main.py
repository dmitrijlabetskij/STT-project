import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
import time
from whisper_methods import get_args, save_file, exit

torchdType = torch.float32
running = True

while running:
    exit()

    file, device = get_args(input('\nfile, [start_ms], [end_ms], device\n'))

    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        'openai/whisper-medium', torch_dtype=torchdType, low_cpu_mem_usage=True, use_safetensors=True
    )

    model.to(device)
    processor = AutoProcessor.from_pretrained('openai/whisper-medium')
    
    start_time = time.time()

    pipe = pipeline(
        'automatic-speech-recognition',
        model='openai/whisper-medium',
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        max_new_tokens=128,
        return_timestamps=True,
        batch_size=16,
        torch_dtype=torchdType,
        device=device
    )

    result = pipe(file)

    save_file(result)

    print(time.time() - start_time)