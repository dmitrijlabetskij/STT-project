import torch
from transformers import WhisperProcessor, WhisperForConditionalGeneration, pipeline
import time
from whisper_methods import get_args, save_file, exit

torchdType = torch.float32
running = True

while running:
    exit()

    file, device = get_args(input('\nfile, start_ms, end_ms, device\n'))

    processor = WhisperProcessor.from_pretrained('openai/whisper-medium')
    input_features = processor(file, sampling_rate=16000, return_tensors="pt").input_features
    attention_mask = torch.ones(input_features.shape, dtype=torch.long, device=device)
    forced_decoder_ids = processor.get_decoder_prompt_ids(language='ru', task="transcribe")

    model = WhisperForConditionalGeneration.from_pretrained(
        'openai/whisper-medium', use_safetensors=True
    )
    generated_ids = model.generate(input_features, forced_decoder_ids=forced_decoder_ids, attention_mask=attention_mask)

    model.to(device)
    
    start_time = time.time()

    '''pipe = pipeline(
        'automatic-speech-recognition',
        model='openai/whisper-medium',
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        max_new_tokens=128,
        return_timestamps=True,
        batch_size=16,
        torch_dtype=torchdType,
        device=device
    )'''

    transcription = processor.batch_decode(generated_ids, skip_special_tokens=True)

    result = transcription[0]

    save_file(result)

    print(time.time() - start_time)