import sys
import json
import requests
import zipfile
import os
from io import BytesIO
from PIL import Image
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QTextEdit, QMessageBox, QProgressBar, QInputDialog
from PyQt5.QtCore import QThread, pyqtSignal

# OpenAI and DALL-E setup

CHAT_API_URL = "https://api.openai.com/v1/chat/completions"
DALLE_API_URL = "https://api.openai.com/v1/images/generations"
API_KEY_FILE = "api_key.json"

HEADERS = {
    "Authorization": "",
    "Content-Type": "application/json"
}

class QuickActionThread(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bytes, str)

    def __init__(self, action, prompt, parent=None):
        super().__init__(parent)
        self.action = action
        self.prompt = prompt

    def run(self):
        try:
            if self.action == "game plan":
                result = self.generate_game_plan()
            else:
                result = self.generate_content(self.prompt)

            if isinstance(result, dict):
                zip_data = self.create_zip(result)
                self.finished.emit(zip_data, f"{self.action}.zip")
            else:
                self.finished.emit(None, result)
        except Exception as e:
            self.finished.emit(None, f"Error: {str(e)}")

    def generate_content(self, prompt):
        data = {
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": f"You are a helpful assistant specializing in {self.action}."},
                {"role": "user", "content": prompt}
            ]
        }

        try:
            response = requests.post(CHAT_API_URL, headers=HEADERS, json=data)
            response.raise_for_status()
            response_data = response.json()
            if "choices" not in response_data:
                error_message = response_data.get("error", {}).get("message", "Unknown error")
                return f"Error: {error_message}"

            content_text = response_data["choices"][0]["message"]["content"]
            return content_text

        except requests.RequestException as e:
            return f"Error: Unable to communicate with the OpenAI API."

    def generate_game_plan(self):
        game_plan = {}
        user_prompt = self.prompt
        try:
            self.progress.emit(10, "Generating game concept...")
            game_concept = self.generate_content(f"Invent a new 2D game concept with a detailed theme, setting, and unique features based on the following prompt: {user_prompt}. Ensure the game has WASD controls.")
            game_plan['game_concept'] = game_concept

            self.progress.emit(20, "Generating world concept...")
            game_plan['world_concept'] = self.generate_content(f"Create a detailed world concept for the 2D game: {game_concept}")

            self.progress.emit(30, "Generating character concepts...")
            game_plan['character_concepts'] = self.generate_content(f"Create detailed character concepts for the player and enemies in the 2D game: {game_concept}")

            self.progress.emit(40, "Generating plot...")
            game_plan['plot'] = self.generate_content(f"Create a plot for the 2D game based on the world and characters of the game: {game_concept}")

            self.progress.emit(50, "Generating dialogue...")
            game_plan['dialogue'] = self.generate_content(f"Write some dialogue for the 2D game based on the plot of the game: {game_concept}")

            self.progress.emit(60, "Generating images...")
            game_plan['images'] = self.generate_images(game_concept, game_plan['character_concepts'], game_plan['world_concept'])

            self.progress.emit(70, "Generating Unity scripts...")
            game_plan['unity_scripts'] = self.generate_unity_scripts(game_concept, game_plan['character_concepts'], game_plan['world_concept'])

            self.progress.emit(80, "Generating recap...")
            game_plan['recap'] = self.generate_content(f"Recap the game plan for the 2D game: {game_concept}")

            self.progress.emit(85, "Generating master document...")
            game_plan['master_document'] = self.create_master_document(game_plan)

            self.progress.emit(90, "Packaging into ZIP...")
            return game_plan

        except Exception as e:
            return f"Error during game plan generation: {str(e)}"

    def generate_images(self, game_concept, character_concepts, world_concept):
        images = {}
        descriptions = [
            f"Full-body, hyper-realistic character for a 2D game, with no background, in Unreal Engine style, based on the character descriptions: {character_concepts}",
            f"Full-body, hyper-realistic enemy character for a 2D game, with no background, in Unreal Engine style, based on the character descriptions: {character_concepts}",
            f"High-quality game object for the 2D game, with no background, in Unreal Engine style, based on the world concept: {world_concept}",
            f"High-quality game object for the 2D game, with no background, in Unreal Engine style, based on the world concept: {world_concept}",
            f"High-quality game object for the 2D game, with no background, in Unreal Engine style, based on the world concept: {world_concept}",
            f"High-quality level background for the 2D game, in Unreal Engine style, based on the world concept: {world_concept}"
        ]
        for i, desc in enumerate(descriptions, start=1):
            self.progress.emit(60 + i * 5, f"Generating image {i}...")
            image_content = self.generate_image(desc)
            if image_content:
                images[f"image_{i}.png"] = image_content
            else:
                images[f"image_{i}.png"] = b""
        return images

    def generate_image(prompt, size="1024x1024"):
        response = openai.Image.create(
            prompt=prompt,
            n=1,
            size=size,
            response_format="url"
        )
        image_url = response['data'][0]['url']
        return image_url

    def save_image(image_url, save_path):
        image_response = requests.get(image_url)
        image = Image.open(BytesIO(image_response.content))
        image.save(save_path)
        return save_path

    def generate_unity_scripts(self, game_concept, character_concepts, world_concept):
        scripts = {}
        descriptions = [
            f"Unity script for the player character in a 2D game with WASD controls and space bar to jump or shoot, based on the character descriptions: {character_concepts}",
            f"Unity script for an enemy character in a 2D game with basic AI behavior, based on the character descriptions: {character_concepts}",
            f"Unity script for a game object in a 2D game, based on the world concept: {world_concept}",
            f"Unity script for a second game object in a 2D game, based on the world concept: {world_concept}",
            f"Unity script for a third game object in a 2D game, based on the world concept: {world_concept}",
            f"Unity script for the level background in a 2D game, based on the world concept: {world_concept}"
        ]
        for i, desc in enumerate(descriptions, start=1):
            scripts[f"script_{i}.cs"] = self.generate_content(desc)
        return scripts

    def create_master_document(self, game_plan):
        master_doc = "Game Plan Master Document\n\n"
        for key, value in game_plan.items():
            if key == "images":
                master_doc += f"{key.capitalize()}:\n"
                for img_key in value:
                    master_doc += f" - {img_key}: See attached image.\n"
            elif key == "unity_scripts":
                master_doc += f"{key.replace('_', ' ').capitalize()}:\n"
                for script_key in value:
                    master_doc += f" - {script_key}: See attached script.\n"
            else:
                master_doc += f"{key.replace('_', ' ').capitalize()}: See attached document.\n"
        return master_doc

    def create_zip(self, content_dict):
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for key, value in content_dict.items():
                if isinstance(value, str):
                    zip_file.writestr(f"{key}.txt", value)
                elif isinstance(value, bytes):
                    zip_file.writestr(key, value)
                elif isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        if isinstance(sub_value, str):
                            zip_file.writestr(f"{key}/{sub_key}.txt", sub_value)
                        elif isinstance(sub_value, bytes):
                            zip_file.writestr(f"{key}/{sub_key}", sub_value)

        zip_buffer.seek(0)
        self.progress.emit(100, "ZIP package created.")
        return zip_buffer.read()

class QuickActionsApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Quick Actions")

        self.api_key = self.load_api_key()
        if not self.api_key:
            self.api_key = self.ask_api_key()
            if not self.api_key:
                QMessageBox.critical(self, "Error", "API key is required to proceed.")
                sys.exit()

        global HEADERS
        HEADERS = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Main layout
        self.main_widget = QWidget()
        self.main_layout = QVBoxLayout()
        self.main_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.main_widget)

        self.prompt_label = QLabel("Enter topic/keywords:")
        self.prompt_entry = QLineEdit()
        self.main_layout.addWidget(self.prompt_label)
        self.main_layout.addWidget(self.prompt_entry)

        self.result_box = QTextEdit()
        self.result_box.setReadOnly(True)
        self.main_layout.addWidget(self.result_box)

        self.progress_bar = QProgressBar()
        self.main_layout.addWidget(self.progress_bar)

        self.actions = [
            "game plan"
        ]

        for action in self.actions:
            button = QPushButton(f"Generate {action.capitalize()}")
            button.clicked.connect(lambda checked, a=action: self.handle_action(a))
            self.main_layout.addWidget(button)

    def load_api_key(self):
        if os.path.exists(API_KEY_FILE):
            with open(API_KEY_FILE, 'r') as file:
                data = json.load(file)
                return data.get('api_key')
        return None

    def ask_api_key(self):
        api_key, ok = QInputDialog.getText(self, "API Key", "Please enter your OpenAI API key:", QLineEdit.Password)
        if ok:
            with open(API_KEY_FILE, 'w') as file:
                json.dump({"api_key": api_key}, file)
            return api_key
        return None

    def handle_action(self, action):
        prompt = self.prompt_entry.text()
        self.result_box.append(f"Generating {action}...")
        self.progress_bar.setValue(0)
        self.quick_action_thread = QuickActionThread(action, prompt)
        self.quick_action_thread.progress.connect(self.update_progress)
        self.quick_action_thread.finished.connect(self.handle_finished)
        self.quick_action_thread.start()

    def update_progress(self, value, message):
        self.progress_bar.setValue(value)
        self.result_box.append(message)

    def handle_finished(self, zip_data, filename_or_error):
        if zip_data:
            options = QFileDialog.Options()
            file_path, _ = QFileDialog.getSaveFileName(self, "Save ZIP", "", "Zip Files (*.zip);;All Files (*)", options=options)
            if file_path:
                with open(file_path, 'wb') as file:
                    file.write(zip_data)
            self.result_box.append(f"{filename_or_error} generated and saved.")
        else:
            self.result_box.append(filename_or_error)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QuickActionsApp()
    window.show()
    sys.exit(app.exec_())
