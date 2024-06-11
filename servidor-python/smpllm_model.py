from model_interface import ModelInterface
from transformers import BitsAndBytesConfig, AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import torch
import re
import tkinter as tk
import tkinter.font as tkFont
import smplx_utils as smplx


class SMPLLMModel(ModelInterface):
    def __init__(self):
        self.input_text = None
        self.tokenizer = None
        self.ft_model = None

        # Fonts and formats
        self.h1_font = tkFont.Font(family="Helvetica", size=28, weight="bold")
        self.h2_font = tkFont.Font(family="Helvetica", size=16, weight="bold")
        self.h3_font = tkFont.Font(family="Helvetica", size=14, weight="bold")
        self.sub_font = tkFont.Font(family="Helvetica", size=10)
        self.button_font = tkFont.Font(family="Helvetica", size=12, weight="bold")

        self.h1_color = "#e8deb5"
        self.h2_color = "#b9bdd2"
        self.h3_color = "#b9bdd2"

        self.background_color = "#070e2c"

        self.button_fg_color = "#1D1E18"
        self.button_bg_color = "#9197B3"
        self.button_fg_active_color = "#1D1E18"
        self.button_bg_active_color = "#e8deb5"
        self.button_bg_active_close_color = "#b34b53"

        self.button_style = {
            "font": self.button_font,
            "bg": self.button_bg_color,
            "fg": self.button_fg_color,
            "activebackground": self.button_bg_active_color,
            "activeforeground": self.button_fg_active_color,
            "bd": 0,
            "width": 20
        }

    def load_model(self, model_info):
        base_model_id = model_info['base_model_id']
        fine_tued_model = model_info['filepath']

        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16
        )

        base_model = AutoModelForCausalLM.from_pretrained(
            base_model_id,
            quantization_config=bnb_config,
            device_map="cuda",
            trust_remote_code=True,
        )

        self.tokenizer = AutoTokenizer.from_pretrained(base_model_id, add_bos_token=True, trust_remote_code=True)
        self.ft_model = PeftModel.from_pretrained(base_model, fine_tued_model)

    def run_model(self, input_data):
        description = input_data
        eval_prompt = "### Description: " + description + "\n ### Shape parameters: "
        model_input = self.tokenizer(eval_prompt, return_tensors="pt").to("cuda")
        self.ft_model.eval()
        with torch.no_grad():
            answer_raw = self.tokenizer.decode(self.ft_model.generate(**model_input, max_new_tokens=200)[0],
                                               skip_special_tokens=True)
        response = str(extract_betas(answer_raw))

        return response

    def remove_model(self):
        print("Removing SMPLLM model...")
        del self.ft_model
        del self.tokenizer

        torch.cuda.empty_cache()

    def display_interface(self, root):
        label = tk.Label(root, text="[SMPLLM]", font=self.sub_font,
                         bg=self.background_color, fg=self.h3_color)
        label.pack(anchor="w")

        label = tk.Label(root, text="Enter Avatar SHAPE Description", font=self.h3_font,
                         bg=self.background_color, fg=self.h3_color)
        label.pack(pady=10)

        self.input_text = tk.Text(root, height=5, width=50)
        self.input_text.pack(pady=5)

        send_button = tk.Button(root, text="Send",
                                command=self.send_description_button_clicked, **self.button_style)
        send_button.pack(pady=2)

        return root

    def send_description_button_clicked(self):
        desc = self.input_text.get("1.0", tk.END).strip()
        betas = self.run_model(input_data=desc)
        betas_vector = extract_betas(betas)
        model, output, vertices, joints = smplx.generate_avatar_from_betas(betas_vector)
        smplx.render_avatar(vertices, model)


def extract_betas(text):
    # Buscar todos los números decimales del texto usando regex
    decimal_numbers = re.findall(r'-?\d+\.\d+', text)
    decimal_numbers = [float(num) for num in decimal_numbers]
    # Devolver los 10 primeros números
    return decimal_numbers[:10]