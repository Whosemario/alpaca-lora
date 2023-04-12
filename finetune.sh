python finetune.py \
    --base_model 'decapoda-research/llama-7b-hf' \
    --data_path './input/py_code_1.json' \
    --output_dir './python-lora-1'  \
    --num_epochs=5 \
    --cutoff_len=512 \
    --group_by_length \
    --lora_target_modules='[q_proj,k_proj,v_proj,o_proj]' \
    --lora_r=16 \
    --micro_batch_size=8