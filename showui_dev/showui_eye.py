import torch
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info
from PIL import Image
import os

def run_showui_eye(image_path, query):
    model_id = "showlab/ShowUI-2B"
    
    print(f"Loading ShowUI model ({model_id})...")
    # Using bfloat16 for better CPU/GPU balance and reduced memory footprint
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        model_id, 
        torch_dtype=torch.bfloat16, 
        offload_folder=os.path.join(os.getenv("HF_HOME", "~/.cache/huggingface"), "offload"), # Use HF_HOME for offloading
        device_map="cpu" # Explicitly set to CPU
    )
    processor = AutoProcessor.from_pretrained(model_id)

    print(f"Processing image: {image_path}...")
    image = Image.open(image_path).convert("RGB")
    
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image},
                {"type": "text", "text": query},
            ],
        }
    ]

    # Preparation for inference
    text = processor.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    
    image_inputs, video_inputs = process_vision_info(messages)
    inputs = processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    )
    inputs = inputs.to(model.device)

    print("Generating vision-action response...")
    generated_ids = model.generate(**inputs, max_new_tokens=512)
    generated_ids_trimmed = [
        out_ids[len(in_ids) :] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
    ]
    output_text = processor.batch_decode(
        generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
    )[0]

    return output_text

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python showui_eye.py <image_path> <query>")
        sys.exit(1)
        
    img_path = sys.argv[1]
    prompt = sys.argv[2]
    
    if not os.path.exists(img_path):
        print(f"Error: {img_path} not found.")
    else:
        try:
            result = run_showui_eye(img_path, prompt)
            print("\n--- ShowUI Eye Report ---")
            print(result)
            print("--------------------------\n")
        except Exception as e:
            print(f"\n[ERROR] ShowUI Eye encountered a problem: {e}")
