import base64
from model_interface import ModelInterface
from diffusers import StableDiffusionPipeline
import torch
import tkinter.font as tkFont
import tkinter as tk
import matplotlib.pyplot as plt


class SMPLitexModel(ModelInterface):
    def __init__(self):
        # Fonts and formats
        self.input_text = None
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
        print("Loading SMPLitex model...")
        pipe = StableDiffusionPipeline.from_pretrained("simplitex-trained-model", safety_checker=None)
        pipe.to("cuda")
        prompt = "empty"
        image = pipe(prompt,guidance_scale=2,num_inference_steps=200,).images[0]

    async def run_model(self, input_data):
        pipe = StableDiffusionPipeline.from_pretrained("simplitex-trained-model", safety_checker=None)
        pipe.to("cuda")
        complete_prompt = "a sks texturemap of " + input_data
        image = pipe(
            complete_prompt,
            guidance_scale=2,
            num_inference_steps=200,
        ).images[0]

        image.save("output.png")
        encoded_image = await load_image("output.png")
        response = encoded_image

        return response

    def remove_model(self):
        print("Removing SMPLitex model...")
        torch.cuda.empty_cache()

    def display_interface(self, root):
        label = tk.Label(root, text="[SMPLitex]", font=self.sub_font,
                         bg=self.background_color, fg=self.h3_color)
        label.pack(anchor="w")

        label = tk.Label(root, text="Enter Avatar TEXTURE Description", font=self.h3_font,
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

        pipe = StableDiffusionPipeline.from_pretrained("simplitex-trained-model", safety_checker=None)
        pipe.to("cuda")
        complete_prompt = "a sks texturemap of " + desc
        img = pipe(
            complete_prompt,
            guidance_scale=2,
            num_inference_steps=200,
        ).images[0]

        show_image(img)


async def load_image(image_path):
    with open(image_path, 'rb') as image_file:
        image_data = image_file.read()
        encoded_image = base64.b64encode(image_data).decode('utf-8')
        return encoded_image


def show_image(image):
    plt.imshow(image)
    plt.axis('off')
    plt.show()