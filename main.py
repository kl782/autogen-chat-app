import autogen
from autogen.agentchat.contrib.capabilities.generate_images import ImageGeneration
from dotenv import load_dotenv
import os
import base64
from PIL import Image
import io
import webbrowser
import http.server
import socketserver
import threading
import subprocess
import platform
import openai
import time
from gtts import gTTS

# Load environment variables
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

# Create necessary directories
IMAGES_DIR = 'generated_images'
AUDIO_DIR = 'generated_audio'
for dir_path in [IMAGES_DIR, AUDIO_DIR]:
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

# Enhanced HTML template with audio player
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Generated Content</title>
    <style>
        body { 
            display: flex; 
            flex-direction: column;
            align-items: center; 
            min-height: 100vh; 
            margin: 0;
            background: #f0f0f0;
            font-family: Arial, sans-serif;
        }
        .content {
            max-width: 800px;
            padding: 20px;
            text-align: center;
        }
        img { 
            max-width: 90%; 
            max-height: 70vh; 
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
            margin: 20px 0;
        }
        .audio-player {
            width: 100%;
            max-width: 500px;
            margin: 20px 0;
            padding: 20px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        audio {
            width: 100%;
        }
    </style>
</head>
<body>
    <div class="content">
        {image_html}
        <div class="audio-player">
            <h3>Audio Response</h3>
            <audio controls>
                <source src="/generated_audio/{audio_filename}" type="audio/mpeg">
                Your browser does not support the audio element.
            </audio>
        </div>
    </div>
</body>
</html>
"""

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

def start_server():
    PORT = 8000
    Handler = CustomHandler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Server running at http://localhost:{PORT}")
        httpd.serve_forever()

# Start the server in a separate thread
server_thread = threading.Thread(target=start_server, daemon=True)
server_thread.start()

def text_to_speech(text, filename):
    """Convert text to speech and save locally"""
    try:
        # First try OpenAI's TTS (better quality)
        try:
            response = openai.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=text
            )
            audio_path = os.path.join(AUDIO_DIR, filename)
            response.stream_to_file(audio_path)
        except:
            # Fallback to gTTS if OpenAI fails
            tts = gTTS(text=text, lang='en')
            audio_path = os.path.join(AUDIO_DIR, filename)
            tts.save(audio_path)
        
        return audio_path
    except Exception as e:
        print(f"Error generating speech: {e}")
        return None

def save_and_show_content(text, base64_image=None):
    """Save and display both image and audio content"""
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    
    # Generate and save audio
    audio_filename = f"response_{timestamp}.mp3"
    text_to_speech(text, audio_filename)
    
    # Handle image if provided
    image_html = ""
    if base64_image:
        image_filename = f"image_{timestamp}.png"
        img_data = base64.b64decode(base64_image)
        img = Image.open(io.BytesIO(img_data))
        filepath = os.path.join(IMAGES_DIR, image_filename)
        img.save(filepath)
        image_html = f'<img src="/generated_images/{image_filename}" alt="Generated Image">'

    # Create HTML file
    html_path = os.path.join(IMAGES_DIR, "viewer.html")
    with open(html_path, "w") as f:
        f.write(HTML_TEMPLATE.format(
            image_html=image_html,
            audio_filename=audio_filename
        ))
    
    # Open in browser
    webbrowser.open(f'http://localhost:8000/generated_images/viewer.html')

# Configure the assistant
config_list = [
    {
        'model': 'gpt-4',
        'api_key': os.getenv('OPENAI_API_KEY')
    }
]

class CustomAssistant(autogen.AssistantAgent):
    def send(self, message, recipient, request_reply=None, silent=False):
        response = super().send(message, recipient, request_reply, silent)
        if not silent and isinstance(message, str):
            save_and_show_content(message)
        return response

# Create the assistant agent with image generation capability
assistant = CustomAssistant(
    name="assistant",
    llm_config={
        "config_list": config_list,
        "temperature": 0.7,
    },
    system_message="""You are a helpful assistant who can generate images and speak.
    Your responses will be converted to speech automatically."""
)

# Add image generation capability
image_gen = ImageGeneration(
    image_model="dall-e-3",
    save_dir=IMAGES_DIR,
    api_key=os.getenv('OPENAI_API_KEY')
)
assistant.register_capability('image_generation', image_gen)

# Create the user proxy agent
user_proxy = autogen.UserProxyAgent(
    name="user_proxy",
    human_input_mode="ALWAYS",
    max_consecutive_auto_reply=0,
    code_execution_config={"work_dir": "coding"}
)

# Initialize the chat
def start_chat():
    print("\n=== MultiModal Chatbot ===")
    print("Features:")
    print("1. Chat with text responses")
    print("2. Generate images")
    print("3. Text-to-speech for all responses")
    print("\nAll content will be:")
    print("- Saved locally in respective folders")
    print("- Displayed in your web browser")
    print("- Include audio playback controls")
    print("\nStarting chat...\n")
    
    user_proxy.initiate_chat(
        assistant,
        message="Hello! I'm ready to help you. I can chat, generate images, and my responses will be spoken. What would you like to do?"
    )

if __name__ == "__main__":
    start_chat()