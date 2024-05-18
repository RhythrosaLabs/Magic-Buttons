import sys
import json
import requests
import zipfile
import os
from io import BytesIO
from PIL import Image
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QTextEdit, QMessageBox, QProgressBar, QInputDialog
from PyQt5.QtCore import QThread, pyqtSignal
import pandas as pd

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
            if self.action in ["marketing campaign", "comic book", "game plan", "business plan"]:
                result = getattr(self, f"generate_{self.action.replace(' ', '_')}")()
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

    def generate_marketing_campaign(self):
        campaign_plan = {}
        user_prompt = self.prompt
        try:
            self.progress.emit(10, "Generating campaign concept...")
            campaign_concept = self.generate_content(f"Create a detailed marketing campaign concept based on the following prompt: {user_prompt}.")
            campaign_plan['campaign_concept'] = campaign_concept

            self.progress.emit(20, "Generating marketing plan...")
            campaign_plan['marketing_plan'] = self.generate_content(f"Create a detailed marketing plan for the campaign: {campaign_concept}")

            self.progress.emit(30, "Generating budget spreadsheet...")
            campaign_plan['budget_spreadsheet'] = self.generate_budget_spreadsheet()

            self.progress.emit(40, "Generating social media schedule spreadsheet...")
            campaign_plan['social_media_schedule'] = self.generate_social_media_schedule(campaign_concept)

            self.progress.emit(50, "Generating images...")
            campaign_plan['images'] = self.generate_images(campaign_concept)

            self.progress.emit(60, "Generating resources and tips...")
            campaign_plan['resources_tips'] = self.generate_content(f"List resources and tips for executing the marketing campaign: {campaign_concept}")

            self.progress.emit(70, "Generating recap...")
            campaign_plan['recap'] = self.generate_content(f"Recap the marketing campaign: {campaign_concept}")

            self.progress.emit(80, "Generating master document...")
            campaign_plan['master_document'] = self.create_master_document(campaign_plan)

            self.progress.emit(90, "Packaging into ZIP...")
            return campaign_plan

        except Exception as e:
            return f"Error during marketing campaign generation: {str(e)}"

    def generate_budget_spreadsheet(self):
        # Define the budget allocation
        budget_data = [
            {"Category": "Advertising", "Amount": 100, "Description": "Social media ads, Google ads"},
            {"Category": "Content Creation", "Amount": 50, "Description": "Graphics, videos, copywriting"},
            {"Category": "Social Media", "Amount": 30, "Description": "Scheduling tools, promotion"},
            {"Category": "Miscellaneous", "Amount": 20, "Description": "Unexpected expenses"}
        ]

        # Add a summary row for total budget
        budget_data.append({"Category": "Total", "Amount": sum(item["Amount"] for item in budget_data), "Description": ""})

        # Create a DataFrame from the budget data
        df = pd.DataFrame(budget_data)

        # Save the DataFrame to an Excel file in memory
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Budget')

        return excel_buffer.getvalue()

    def generate_social_media_schedule(self, campaign_concept):
        # Define a basic schedule template with placeholders
        schedule_data = [
            {"Platform": "Twitter", "Date": "2024-05-20", "Time": "10:00", "Post": f"Introducing our new campaign: {campaign_concept}", "Hashtags": "#launch #marketing"},
            {"Platform": "Facebook", "Date": "2024-05-20", "Time": "12:00", "Post": f"Don't miss out on our latest campaign: {campaign_concept}", "Hashtags": "#launch #marketing"},
            {"Platform": "Twitter", "Date": "2024-05-21", "Time": "09:00", "Post": f"Check out our campaign highlights: {campaign_concept}", "Hashtags": "#highlights #marketing"},
            {"Platform": "Facebook", "Date": "2024-05-21", "Time": "14:00", "Post": f"Join the discussion on our new campaign: {campaign_concept}", "Hashtags": "#discussion #marketing"},
            {"Platform": "Twitter", "Date": "2024-05-22", "Time": "08:00", "Post": f"Exclusive insights into our campaign: {campaign_concept}", "Hashtags": "#insights #marketing"},
            {"Platform": "Facebook", "Date": "2024-05-22", "Time": "16:00", "Post": f"Learn more about our campaign: {campaign_concept}", "Hashtags": "#learnmore #marketing"}
        ]

        # Create a DataFrame from the schedule data
        df = pd.DataFrame(schedule_data)

        # Save the DataFrame to an Excel file in memory
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Social Media Schedule')

        return excel_buffer.getvalue()

    def generate_images(self, campaign_concept):
        images = {}
        descriptions = {
            "banner": "Wide banner image in a modern and appealing style, with absolutely no font, no words, no text, no characters, no numbers, no letters in the image, matching the theme of: " + campaign_concept,
            "instagram_background": "Tall background image suitable, with absolutely no font, no words, no text, no characters, no numbers, no letters in the image, for Instagram video, matching the theme of: " + campaign_concept,
            "square_post_1": "Square background image for social media post, with absolutely no font, no words, no text, no characters, no numbers, no letters in the image, matching the theme of: " + campaign_concept,
            "square_post_2": "Square background image for social media post, with absolutely no font, no words, no text, no characters, no numbers, no letters in the image, matching the theme of: " + campaign_concept,
            "square_post_3": "Square background image for social media post, with absolutely no font, no words, no text, no characters, no numbers, no letters in the image, matching the theme of: " + campaign_concept,
        }

        sizes = {
            "banner": "1792x1024",
            "instagram_background": "1024x1792",
            "square_post_1": "1024x1024",
            "square_post_2": "1024x1024",
            "square_post_3": "1024x1024",
        }

        for key, desc in descriptions.items():
            self.progress.emit(50 + len(images) * 10, f"Generating {key.replace('_', ' ')}...")
            image_url = self.generate_image(desc, sizes[key])
            if image_url:
                try:
                    image_data = self.download_image(image_url)
                    if image_data:
                        images[f"{key}.png"] = image_data
                    else:
                        images[f"{key}.png"] = b""
                except Exception as e:
                    images[f"{key}.png"] = b""
                    self.progress.emit(50 + len(images) * 10, f"Error downloading {key.replace('_', ' ')}: {str(e)}")
            else:
                images[f"{key}.png"] = b""
        return images

    def generate_image(self, prompt, size="1024x1024"):
        data = {
            "model": "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": size,
            "quality": "hd",
            "style": "vivid",
            "response_format": "url"
        }
        try:
            response = requests.post(DALLE_API_URL, headers=HEADERS, json=data)
            response.raise_for_status()
            response_data = response.json()
            image_url = response_data['data'][0]['url']
            return image_url
        except requests.RequestException as e:
            print(f"RequestException generating image: {e}")
            return None

    def download_image(self, image_url):
        try:
            response = requests.get(image_url)
            response.raise_for_status()
            return response.content
        except requests.RequestException as e:
            print(f"RequestException downloading image: {e}")
            return None

    def create_master_document(self, campaign_plan):
        master_doc = "Marketing Campaign Master Document\n\n"
        for key, value in campaign_plan.items():
            if key == "images":
                master_doc += f"{key.capitalize()}:\n"
                for img_key in value:
                    master_doc += f" - {img_key}: See attached image.\n"
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
        self.setWindowTitle("Quick Actions - Marketing Campaign")

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
            "marketing campaign"
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
