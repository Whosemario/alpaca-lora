# -*- coding:utf-8 -*-

import fire
import sys
import time
from sys import stdin
import torch
import transformers
from peft import PeftModel
from transformers import GenerationConfig, LlamaForCausalLM, LlamaTokenizer

from utils.callbacks import Iteratorize, Stream
from utils.prompter import Prompter

if torch.cuda.is_available():
    device = "cuda"
else:
    device = "cpu"

try:
    if torch.backends.mps.is_available():
        device = "mps"
except:  # noqa: E722
    pass

def main(
    load_8bit: bool = True,
    base_model: str = "decapoda-research/llama-7b-hf",
    lora_weights: str = "./my-lora-alpaca",
    prompt_template: str = "",  # The prompt template to use, will default to alpaca.
):
    prompter = Prompter(prompt_template)
    tokenizer = LlamaTokenizer.from_pretrained(base_model)
    if device == "cuda":
        model = LlamaForCausalLM.from_pretrained(
            base_model,
            load_in_8bit=load_8bit,
            torch_dtype=torch.float16,
            device_map={'': 0}, #"auto",
        )
        model = PeftModel.from_pretrained(
            model,
            lora_weights,
            torch_dtype=torch.float16,
            device_map={'': 0}, 
        )
    elif device == "mps":
        model = LlamaForCausalLM.from_pretrained(
            base_model,
            device_map={"": device},
            torch_dtype=torch.float16,
        )
        model = PeftModel.from_pretrained(
            model,
            lora_weights,
            device_map={"": device},
            torch_dtype=torch.float16,
        )
    else:
        model = LlamaForCausalLM.from_pretrained(
            base_model, device_map={"": device}, low_cpu_mem_usage=True
        )
        model = PeftModel.from_pretrained(
            model,
            lora_weights,
            device_map={"": device},
        )

    # unwind broken decapoda-research config
    model.config.pad_token_id = tokenizer.pad_token_id = 0  # unk
    model.config.bos_token_id = 1
    model.config.eos_token_id = 2

    if not load_8bit:
        model.half()  # seems to fix bugs for some users.

    model.eval()
    if torch.__version__ >= "2" and sys.platform != "win32":
        model = torch.compile(model)

    def evaluate(
        instruction,
        input=None,
        temperature=0.1,
        top_p=0.75,
        top_k=40,
        num_beams=4,
        max_new_tokens=128,
        stream_output=False,
        **kwargs,
    ):
        prompt = prompter.generate_prompt(instruction, input)
        inputs = tokenizer(prompt, return_tensors="pt")
        input_ids = inputs["input_ids"].to(device)
        generation_config = GenerationConfig(
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            num_beams=num_beams,
            **kwargs,
        )

        # generate_params = {
        #     "input_ids": input_ids,
        #     "generation_config": generation_config,
        #     "return_dict_in_generate": True,
        #     "output_scores": True,
        #     "max_new_tokens": max_new_tokens,
        # }

        # if stream_output:
        #     # Stream the reply 1 token at a time.
        #     # This is based on the trick of using 'stopping_criteria' to create an iterator,
        #     # from https://github.com/oobabooga/text-generation-webui/blob/ad37f396fc8bcbab90e11ecf17c56c97bfbd4a9c/modules/text_generation.py#L216-L243.

        #     def generate_with_callback(callback=None, **kwargs):
        #         kwargs.setdefault(
        #             "stopping_criteria", transformers.StoppingCriteriaList()
        #         )
        #         kwargs["stopping_criteria"].append(
        #             Stream(callback_func=callback)
        #         )
        #         with torch.no_grad():
        #             model.generate(**kwargs)

        #     def generate_with_streaming(**kwargs):
        #         return Iteratorize(
        #             generate_with_callback, kwargs, callback=None
        #         )

        #     with generate_with_streaming(**generate_params) as generator:
        #         for output in generator:
        #             # new_tokens = len(output) - len(input_ids[0])
        #             decoded_output = tokenizer.decode(output)

        #             if output[-1] in [tokenizer.eos_token_id]:
        #                 break

        #             yield prompter.get_response(decoded_output)
        #     return  # early return for stream_output

        # Without streaming
        with torch.no_grad():
            generation_output = model.generate(
                input_ids=input_ids,
                generation_config=generation_config,
                return_dict_in_generate=True,
                output_scores=True,
                max_new_tokens=max_new_tokens,
            )
        s = generation_output.sequences[0]
        output = tokenizer.decode(s)
        # print(output)
        return prompter.get_response(output)

    print(device)
    while True:
        print("Instruction:")
        inst = stdin.readline()
        if "<finish>" in inst:
            break
        print("Input:")
        ipt = ""
        # while True:
        #     line = stdin.readline()
        #     if "<end>" in line:
        #         break
        #     ipt += line
        print("------------------------------------")
        ts = time.time()
        print(evaluate(inst, ipt or None))
        print("(耗时:", int(time.time()-ts), "秒)")

if __name__ == "__main__":
    fire.Fire(main)

