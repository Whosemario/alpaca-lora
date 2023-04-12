nohup python finetune.py \
    --base_model 'decapoda-research/llama-7b-hf' \
    --data_path './input/py_code_1.json' \
    --output_dir './python-lora-1'  \
    --num_epochs=3 \
    --cutoff_len=256 \
    --group_by_length \
    --lora_target_modules='[q_proj,k_proj,v_proj,o_proj]' \
    --lora_r=8 \
    --micro_batch_size=4 \
    1>./log.txt 2>&1 &
