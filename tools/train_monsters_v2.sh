#!/usr/bin/env bash
# ToE_Monsters_v2 LoRA training (2026-07-16) — run AFTER prep_training.py.
# NoobAI XL is a vpred model: --v_parameterization + zero-terminal-SNR flags
# are load-bearing, do not remove. ~2500 steps @ batch 2 ≈ 1.5-2.5h on the
# 5070 Ti. Output lands directly in ComfyUI's lora folder as v2.
set -e
cd "$(dirname "$0")/sd-scripts"
venv/Scripts/python.exe sdxl_train_network.py \
  --pretrained_model_name_or_path "C:/Users/liamh/ComfyUI/models/checkpoints/noobaiXLNAIXL_vPred10Version.safetensors" \
  --v_parameterization --zero_terminal_snr \
  --train_data_dir "../training_data" \
  --output_dir "C:/Users/liamh/ComfyUI/models/loras" \
  --output_name "ToE_Monsters_v2" \
  --resolution 1024 --enable_bucket --min_bucket_reso 512 --max_bucket_reso 1536 \
  --network_module networks.lora --network_dim 32 --network_alpha 16 \
  --learning_rate 1e-4 --text_encoder_lr 5e-5 --lr_scheduler cosine --lr_warmup_steps 100 \
  --train_batch_size 2 --max_train_steps 2500 --save_every_n_steps 500 \
  --mixed_precision bf16 --save_precision bf16 --sdpa \
  --cache_latents --cache_latents_to_disk --gradient_checkpointing \
  --min_snr_gamma 5 --noise_offset 0.0357 \
  --optimizer_type AdamW8bit --max_data_loader_n_workers 2 \
  --caption_extension .txt --shuffle_caption --keep_tokens 1
