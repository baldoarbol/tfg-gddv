import importlib
import inspect
import os
import tkinter as tk
from tkinter import ttk
from tkinter import PhotoImage
from PIL import Image, ImageTk
import tkinter.font as tkFont
from tkinter import filedialog
import asyncio
import re
import uvloop
import aim4d_server as server
import threading
from datetime import datetime
import trimesh

import subprocess
import base64


def show_customized(mesh):
    if isinstance(mesh, trimesh.Trimesh):
        scene = trimesh.Scene(mesh)
    else:
        scene = mesh

    for geom in scene.geometry.values():
        geom.visual.face_colors = [90, 0, 150, 200]

    scene.show(
        viewer='gl',
        resolution=(600, 600),
        background=[0.7, 0.7, 0.7, 1.0],
        window_title='Model Render'
    )


def color_to_hex(color):
    if isinstance(color, (list, tuple)):
        return "#{:02x}{:02x}{:02x}".format(*color)
    else:
        return color


def parse_model_file(filepath):
    model_data = {}
    with open(filepath, 'r') as file:
        for line in file:
            line = line.strip()
            if '=' in line:
                key, value = line.split('=')
                key = key.strip()
                value = value.strip().strip('"')
                model_data[key] = value

    return model_data


async def load_image(image_path):
    with open(image_path, 'rb') as image_file:
        image_data = image_file.read()
        encoded_image = base64.b64encode(image_data).decode('utf-8')
        return encoded_image


def extract_betas(text):
    # Buscar todos los números decimales del texto usando regex
    decimal_numbers = re.findall(r'-?\d+\.\d+', text)
    decimal_numbers = [float(num) for num in decimal_numbers]
    # Devolver los 10 primeros números
    return decimal_numbers[:10]


def get_gpu_memory_usage():
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=memory.used,memory.total', '--format=csv,noheader,nounits'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        used, total = map(int, result.stdout.strip().split(','))
        used_gb = round(used / 1024, 2)
        total_gb = round(total / 1024, 2)
        return used_gb, total_gb
    except Exception as e:
        print(f"Error obteniendo uso de memoria GPU: {e}")
        return 0, 0


class AIM4D:
    def __init__(self, root):
        self.previous_state = None
        self.showing_status_button = None
        self.model = None
        self.server_logs = []
        self.server_thread = None
        self.ft_model = None
        self.tokenizer = None
        self.models_frame = None
        self.models_listbox = None
        self.input_text = None
        self.status_button = None
        self.status_frame = None
        self.status_text = None
        self.current_mesh = None
        self.current_mode = None
        self.models_list = []
        self.models_dictionary = {}
        self.model_frames = []

        self.gpu_frame = None
        self.gpu_label = None

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

        self.button_style_close = {
            "font": self.button_font,
            "bg": self.button_bg_color,
            "fg": self.button_fg_color,
            "activebackground": self.button_bg_active_close_color,
            "activeforeground": self.button_fg_active_color,
            "bd": 0,
            "width": 20
        }

        self.button_style_status = {
            "font": self.button_font,
            "bg": self.button_bg_color,
            "fg": self.button_fg_color,
            "activebackground": self.button_bg_active_color,
            "activeforeground": self.button_fg_active_color,
            "bd": 0,
            "width": 12
        }

        self.server_icon = PhotoImage(file="icons/server_icon.png")
        self.user_icon = PhotoImage(file="icons/user_icon.png")
        self.close_icon = PhotoImage(file="icons/close_icon.png")

        self.background_image = self.load_and_resize_image("icons/background.png", (1600, 900))

        self.root = root
        self.root.title("AIM4D")
        self.root.geometry("700x750")
        self.root.minsize(700, 750)

        self.main_frame = tk.Frame(self.root, bg=self.background_color)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.background_label = tk.Label(self.main_frame, image=self.background_image)
        self.background_label.place(relx=0.5, rely=0.5, anchor="center")

        self.container_label = tk.Label(self.main_frame, bg=self.background_color, bd=3, relief="solid")
        self.container_label.place(relx=0.5, rely=0.05, anchor="n")

        self.content_frame = tk.Frame(self.container_label, bg=self.background_color)
        self.content_frame.pack(fill="both", expand=True, padx=60, pady=10)

        self.setup_status_bar()
        self.update_status()
        self.enter_mode_selection()

    def setup_status_bar(self):
        if self.status_frame:
            self.status_frame.pack_forget()

        self.status_frame = tk.Frame(self.root, bg='green', height=30)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_frame.grid_columnconfigure(0, weight=1)
        self.status_frame.grid_columnconfigure(1, weight=0)

        self.status_text = tk.Label(self.status_frame, text="Status text", bg='green', fg='black', anchor='w')
        self.status_text.grid(row=0, column=0, sticky="ew", padx=10, pady=15)

        self.status_button = tk.Button(self.status_frame, text="Manage Models", command=self.enter_model_manager, **self.button_style_status)
        self.status_button.grid(row=0, column=1, padx=10, pady=00)

    def enter_mode_selection(self):
        self.current_mode = "mode_selection"
        self.clear_window()

        label = tk.Label(self.content_frame, text="AIM4D", font=self.h1_font, bg=self.background_color, fg=self.h1_color)
        label.pack(pady=10)

        subtitle = tk.Label(self.content_frame, text="AI Manager For Developers", font=self.h3_font, bg=self.background_color, fg=self.h3_color)
        subtitle.pack(pady=10)

        self.create_button_with_icon(self.content_frame, self.server_icon, "Server Mode", self.enter_server_mode, self.button_style)
        self.create_button_with_icon(self.content_frame, self.user_icon, "User Mode", self.enter_user_mode, self.button_style)
        self.create_button_with_icon(self.content_frame, self.close_icon, "Close", self.root.destroy, self.button_style_close)

        if not self.showing_status_button:
            self.status_button.grid(row=0, column=1, padx=10, pady=10)
            self.showing_status_button = True

    def enter_user_mode(self):
        self.current_mode = "user_mode"
        self.clear_window()
        label = tk.Label(self.content_frame, text="User Mode", font=self.h2_font, bg=self.background_color, fg=self.h2_color)
        label.pack(pady=(20, 10))

        for model_header in self.models_dictionary.keys():
            self.content_frame = self.models_dictionary[model_header].display_interface(self.content_frame)

        back_button = tk.Button(self.content_frame, text="Back", command=self.enter_mode_selection, **self.button_style)
        back_button.pack(pady=20)

        if not self.showing_status_button:
            self.status_button.grid(row=0, column=1, padx=10, pady=10)
            self.showing_status_button = True

    def enter_server_mode(self):
        self.current_mode = "server_mode"
        self.update_server_interface()

        if not self.showing_status_button:
            self.status_button.grid(row=0, column=1, padx=10, pady=10)
            self.showing_status_button = True

    def start_server_button_clicked(self):
        if self.server_thread is None:
            self.server_thread = threading.Thread(target=self.start_server, daemon=True)
            self.server_thread.start()
        else:
            self.show_message(text="Server already running")

    def stop_server_button_clicked(self):
        if self.server_thread is None:
            self.show_message(text="There is no server running")
        else:
            self.server_thread = threading.Thread(target=self.stop_server, daemon=True)
            self.server_thread.start()

    def create_button_with_icon(self, parent, icon, text, command, button_style):

        frame = tk.Frame(parent, bg=self.background_color)
        frame.pack(pady=2)

        label = tk.Label(frame, image=icon, bg=self.background_color)
        label.pack(side="left", padx=0, pady=0)

        button = tk.Button(frame, text=text, command=command, **button_style)
        button.pack(side="left", fill="x", expand=True, pady=0)

        return frame

    def load_and_resize_image(self, path, size):
        image = Image.open(path)
        image = image.resize(size)
        return ImageTk.PhotoImage(image)

    def start_server(self):
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(server.start_background_server(self))
        loop.run_forever()

    def stop_server(self):
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(server.stop_background_server())
        self.server_thread = None

    def enter_model_manager(self):
        if self.current_mode != "model_manager":
            self.previous_state = self.current_mode
        self.current_mode = "model_manager"
        self.clear_window()
        self.status_button.pack_forget()

        label = tk.Label(self.content_frame, text="Model Manager", font=self.h2_font, bg=self.background_color, fg=self.h2_color)
        label.pack(pady=(20, 10))

        if len(self.models_list) <= 0:
            no_models_label = tk.Label(self.content_frame, text="No model loaded!", font=self.h3_font, bg=self.background_color, fg=self.h3_color)
            no_models_label.pack(pady=10)
        else:
            for frame in self.model_frames:
                frame.destroy()
            self.model_frames.clear()
            self.display_models_list()

        add_model_button = tk.Button(self.content_frame, text="Add New Model", command=self.add_new_model, **self.button_style)
        add_model_button.pack(pady=10)

        self.gpu_frame = tk.Frame(self.content_frame, bg=self.background_color, padx=10, pady=10)
        self.gpu_frame.pack(pady=(10, 0))

        self.gpu_label = tk.Label(self.gpu_frame, text="", bg=self.background_color, fg=self.h2_color)
        self.gpu_label.pack(anchor='w')

        self.update_gpu_memory_usage()

        back_command = None
        if self.previous_state == "mode_selection":
            back_command = self.enter_mode_selection
        elif self.previous_state == "server_mode":
            back_command = self.enter_server_mode
        elif self.previous_state == "user_mode":
            back_command = self.enter_user_mode

        back_button = tk.Button(self.content_frame, text="Back", command=back_command, **self.button_style)
        back_button.pack(pady=10)

        self.status_button.grid_remove()
        self.showing_status_button = False

    def update_gpu_memory_usage(self):
        used, total = get_gpu_memory_usage()
        percent = (used / total) * 16
        bar = '|' + '█' * int(percent) + '░' * (16 - int(percent)) + '|'
        self.gpu_label.config(text=f"GPU Memory Usage: {used} GB / {total} GB - {bar}")

    def delete_model(self, model):
        if model in self.models_list:
            self.models_list.remove(model)
            del self.models_dictionary[model["model_header"]]
            self.remove_model(model["model_header"])
        self.enter_model_manager()
        self.update_status()
        self.update_gpu_memory_usage()

    def add_new_model(self):
        filepath = filedialog.askopenfilename(
            title="Select a Model File",
            filetypes=(("AIM4D files", "*.aim4d"), ("All files", "*.*"))
        )
        if filepath:
            model_info = parse_model_file(filepath)
            model_info['filepath'] = os.path.dirname(filepath)
            if self.load_model(model_info):
                self.models_list.append(model_info)
                self.enter_model_manager()
                print("Loaded model:", filepath)
        self.update_status()

    def load_model(self, model_info):
        model_loaded = False

        if "model_name" not in model_info:
            self.show_message(text="Error: AIM4D file must contain model_name")
            return model_loaded
        if "model_header" not in model_info:
            self.show_message(text="Error: AIM4D file must contain model_header")
            return model_loaded
        if "aim4d_logic" not in model_info:
            self.show_message(text="Error: AIM4D file must contain aim4d_logic")
            return model_loaded
        if model_info["model_header"] in self.models_dictionary.keys():
            self.show_message(text="Error: AIM4D file already loaded")
            return model_loaded

        aim4d_logic_name = model_info['aim4d_logic']
        module_name, class_name = aim4d_logic_name.rsplit('.', 1)

        try:
            module = importlib.import_module(module_name)
            module_class = getattr(module, class_name)
        except (ImportError, AttributeError) as e:
            print(f"Error importing {aim4d_logic_name}: {e}")
            return model_loaded

        try:
            self.models_dictionary[model_info["model_header"]] = module_class()
            self.models_dictionary[model_info["model_header"]].load_model(model_info)
            model_loaded = True
        except Exception as e:
            print("Failed to load model: ", e)
            self.show_message(text=f"Failed to load model: {e}")
            model_loaded = False
        finally:
            return model_loaded

    async def run_model(self, header, input_text):
        response = None

        if header in self.models_dictionary:
            if inspect.iscoroutinefunction(self.models_dictionary[header].run_model):
                response = await self.models_dictionary[header].run_model(input_text)
            else:
                response = self.models_dictionary[header].run_model(input_text)
        else:
            print(f"Error: Invalid header {header}")
            response = "INVALID_RESPONSE"

        return response

    def remove_model(self, header):
        if header in self.models_dictionary:
            self.models_dictionary[header].remove_model()
        else:
            print(f"Error: Invalid header {header}")

    def show_message(self, header="Error", text="Unknowk Error", background_color="#e8deb5", text_color="#1D1E18"):
        popup = tk.Toplevel(self.root)
        popup.title(header)
        popup.geometry("450x100")
        popup.configure(bg=background_color)

        label = tk.Label(popup, text=text, font=self.h3_font, bg=background_color, fg=text_color)
        label.pack(pady=20)

        close_button = tk.Button(popup, text="Close", command=popup.destroy, **self.button_style_close)
        close_button.pack()

    def push_log(self, text="Default log", color="black"):
        new_log = {
            "text": text,
            "color": color_to_hex(color),
            "time": datetime.now().strftime("%H:%M:%S")
        }
        self.server_logs.append(new_log)
        if self.current_mode == "server_mode":
            self.update_server_interface()

    def update_server_interface(self):
        self.clear_window()

        label = tk.Label(self.content_frame, text="Server Mode", font=self.h2_font, bg=self.background_color, fg=self.h2_color)
        label.pack(pady=(20, 10), padx=200)

        self.update_server_logs()

        start_server_button = tk.Button(self.content_frame, text="Start Server", command=self.start_server_button_clicked, **self.button_style)
        start_server_button.pack(pady=10)

        stop_server_button = tk.Button(self.content_frame, text="Stop Server",
                                        command=self.stop_server_button_clicked, **self.button_style)
        stop_server_button.pack(pady=10)

        back_button = tk.Button(self.content_frame, text="Back", command=self.enter_mode_selection, **self.button_style)
        back_button.pack(pady=10)

    def update_server_logs(self):

        log_frame_container = tk.Frame(self.content_frame, bg='gray')
        log_frame_container.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        canvas = tk.Canvas(log_frame_container, bg='gray')
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(log_frame_container, orient="vertical", command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill="y")

        scrollable_frame = tk.Frame(canvas, bg='gray')

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        for log in self.server_logs:
            log_text = f"{log['time']} - {log['text']}"
            log_label = tk.Label(scrollable_frame, text=log_text, fg=log['color'], bg='gray', anchor='w')
            log_label.pack(fill=tk.X, pady=2, padx=5)

        canvas.yview_moveto(1)

    def display_models_list(self):
        for frame in self.model_frames:
            frame.destroy()
        self.model_frames.clear()

        label = tk.Label(self.content_frame, text="Models list:", font=self.h3_font, fg=self.h3_color, bg=self.background_color)
        label.pack(pady=5)

        for idx, model in enumerate(self.models_list):
            frame = tk.Frame(self.content_frame, background=color_to_hex([110, 110, 250]))
            frame.pack(fill=tk.X, padx=50, pady=1, expand=False)
            frame.grid_columnconfigure(0, weight=1)
            frame.grid_columnconfigure(1, weight=0)

            model_text = tk.StringVar(value=str(model['model_name']) + " - " + str(model['model_description']))

            label = tk.Label(frame, textvariable=model_text, anchor='w', bg=color_to_hex([110, 110, 250]))
            label.grid(row=0, column=0, sticky='ew', padx=10)

            delete_button = tk.Button(frame, text="Delete", command=lambda m=model: self.delete_model(m), **self.button_style)
            delete_button.grid(row=0, column=1, sticky='e', padx=10)

            self.model_frames.append(frame)

    def clear_window(self):
        for widget in self.content_frame.winfo_children():
            widget.pack_forget()

    def update_status(self):
        if len(self.models_list) > 1:
            status_string = "Models loaded: "
            for idx, model in enumerate(self.models_list):
                status_string += str(model['model_name']) + ", "
            status_string = status_string[:-2]
            self.set_status(text=status_string, color="#4db34b")
        elif len(self.models_list) == 1:
            status_string = "Model loaded: "
            status_string += str(self.models_list[0]['model_name'])
            self.set_status(text=status_string, color="#4db34b")
        else:
            self.set_status(text="No model loaded!", color="#b34b53")

    def handle_key_press(self, event):
        if len(self.input_text.get("1.0", tk.END).split('\n')) > 5:
            if event.keysym in ("BackSpace", "Delete"):
                return
            else:
                return "break"

    def send_description_button_clicked(self):
        desc = self.input_text.get("1.0", tk.END).strip()
        self.run_model(header=None, input_text=desc)

    def render_mesh_button_clicked(self):
        print("METHOD NOT IMPLEMENTED YET")

    def set_status(self, text="Status Updated!", color="gray"):
        color_hex = color_to_hex(color)
        self.status_text.config(text=text, bg=color_hex)
        self.status_frame.config(bg=color_hex)


def main():
    root = tk.Tk()
    app = AIM4D(root)
    root.mainloop()


if __name__ == "__main__":
    main()
