import torch
import os
import torchaudio

device = torch.device('cpu')
torch.set_num_threads(4)
local_file = 'v4_uz.pt'

if not os.path.isfile(local_file):
    print("Downloading Silero v4_uz.pt...")
    torch.hub.download_url_to_file('https://models.silero.ai/models/tts/uz/v4_uz.pt', local_file)

print("Loading model...")
model = torch.package.PackageImporter(local_file).load_pickle('tts_models', 'model')
model.to(device)

print("Generating audio...")
audio = model.apply_tts(text="Salom, men Asalman, sizga qanday yordam bera olaman?", speaker='dilnavoz', sample_rate=48000)

torchaudio.save('test.wav', audio.unsqueeze(0), 48000)
print("Done!")
