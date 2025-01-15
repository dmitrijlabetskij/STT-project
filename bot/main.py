import os
import subprocess

class Diarization:
    def __init__(self):
        self.script_path = 'bot/whisper-diarization/diarize.py'
        self.command = f"python {self.script_path} --whisper-model medium --device cuda --no-stem -a "

    def run(self, audio):
        self.command += audio
        subprocess.run(self.command, shell=True)

        # Формируем имя для текстового файла
        base_name = os.path.splitext(os.path.basename(audio))[0]  # Имя файла без расширения
        srt_file = f"{base_name}.srt"
        output_file = f"{base_name}.txt"

        # Проверяем существование результатов и записываем их в файл
        with open(output_file, "w", encoding="utf-8") as outfile:
            if os.path.exists(srt_file):
                
                with open(srt_file, "r", encoding="utf-8") as srt:
                    outfile.write(srt.read())
                    
            else:
                outfile.write("Файл SRT не найден.")

        # Удаляем временные файлы, если нужно
        os.remove(srt_file) if os.path.exists(srt_file) else None

        print(f"Результаты сохранены в файл: {output_file}")
        
        self.command = f"python {self.script_path} --whisper-model medium --device cuda --no-stem -a "
        