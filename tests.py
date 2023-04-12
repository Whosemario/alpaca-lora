# -*- coding:utf-8 -*-

import json
import torch
from transformers import LlamaForCausalLM, LlamaTokenizer
from datasets import load_dataset

# model = LlamaForCausalLM.from_pretrained(
# 	"decapoda-research/llama-7b-hf",
# 	load_in_8bit=True,
# 	torch_dtype=torch.float16,
# 	device_map="auto",
# )

# data = load_dataset("kejian/codesearchnet-python-raw-457k", cache_dir="./datasets")
data = load_dataset("calum/the-stack-smol-python-docstrings", cache_dir="./datasets")
data = data["train"]
output = []
for i in range(data.num_rows):
    output.append(
		{
			"instruction": "Summarize the code:",
			"input": data[i]["body_without_docstring"],
			"output": data[i]["docstring"]
		}
	)
file_name = "./input/py_code_1.json"
with open(file_name, "w", encoding="utf-8") as fd:
	fd.write(json.dumps(output, ensure_ascii=False, indent=4))