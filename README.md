# Crear el entorno virtual
```
python -m venv nllb-env
```
# Python3

```
python3 -m venv nllb-env
```

# Activarlo
# En Windows:
```
nllb-env\Scripts\activate
```
# En Linux/Mac:
```
source nllb-env/bin/activate
```

# Instalar las librerías necesarias
``` bash
pip install -r requirements.txt
```

# Convertir el modelo
# Tienes que transformar el modelo de Meta al formato de alta velocidad de CTranslate2. Ejecuta este comando en tu terminal (estando dentro del entorno virtual):
```bash
ct2-transformers-converter --model facebook/nllb-200-distilled-600M --output_dir nllb_ct2_600m --quantization int8
```
---

```bash
~/Documents/Proyectos/AItranslator main* 7s                                                                                                                             10:50:59
nllb-env ❯ ct2-transformers-converter --model facebook/nllb-200-distilled-600M --output_dir nllb_ct2_600m --quantization int8
config.json: 100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 846/846 [00:00<00:00, 1.15MB/s]
pytorch_model.bin: 100%|████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 2.46G/2.46G [00:43<00:00, 56.6MB/s]
Loading weights: 100%|██████████████████████████████████████████████████████████████████████████████| 512/512 [00:00<00:00, 7281.43it/s, Materializing param=model.shared.weight]
The tied weights mapping and config for this model specifies to tie model.shared.weight to lm_head.weight, but both are present in the checkpoints, so we will NOT tie them. You should update the config with `tie_word_embeddings=False` to silence this warning
The tied weights mapping and config for this model specifies to tie model.shared.weight to model.decoder.embed_tokens.weight, but both are present in the checkpoints, so we will NOT tie them. You should update the config with `tie_word_embeddings=False` to silence this warning
The tied weights mapping and config for this model specifies to tie model.shared.weight to model.encoder.embed_tokens.weight, but both are present in the checkpoints, so we will NOT tie them. You should update the config with `tie_word_embeddings=False` to silence this warning
generation_config.json: 100%|████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 189/189 [00:00<00:00, 872kB/s]
tokenizer_config.json: 100%|█████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 564/564 [00:00<00:00, 826kB/s]
tokenizer.json: 100%|███████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 17.3M/17.3M [00:03<00:00, 4.78MB/s]
special_tokens_map.json: 3.55kB [00:00, 5.78MB/s]███████████████████████████████████████████████████████████████████████████████████████████| 17.3M/17.3M [00:03<00:00, 4.78MB/s]
model.safetensors: 100%|████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 2.46G/2.46G [00:43<00:00, 56.9MB/s]
```




uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4


# Test
``` bash
curl -X 'POST' \
  'http://localhost:8000/translate' \
  -H 'Content-Type: application/json' \
  -d '{
  "text": "Buenos días, ¿qué tal estás?",
  "source_lang": "spa_Latn",
  "target_lang": "ary_Arab"
}'
```