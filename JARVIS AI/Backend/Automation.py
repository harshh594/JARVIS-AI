# Import required libraries
from AppOpener import close, open as appopen  # Import functions to open and close apps.
from webbrowser import open as webopen  # Import web browser functionality.
from pywhatkit import search, playonyt  # Import functions for Google search and YouTube playback.
from dotenv import dotenv_values  # Import dotenv to manage environment variables.
from bs4 import BeautifulSoup  # Import BeautifulSoup for parsing HTML content.
from rich import print  # Import rich for styled console output.
from groq import Groq  # Import Groq for AI chat functionalities.
import webbrowser  # Import webbrowser for opening URLs.
import subprocess  # Import subprocess for interacting with the system.
import requests  # Import requests for making HTTP requests.
import keyboard  # Import keyboard for keyboard-related actions.
import asyncio  # Import asyncio for asynchronous programming.
import os  # Import os for operating system functionalities.

# Load environment variables from the .env file
env_vars = dotenv_values(".env")
GroqAPIKey = env_vars.get("GroqAPIKey")  # Retrieve the Groq API key.

# Define a user-agent for making web requests
useragent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36'

# Initialize the Groq client with the API key
client = Groq(api_key=GroqAPIKey)

# Predefined professional responses for user interactions
professional_responses = [
    "Your satisfaction is my top priority; feel free to reach out if there's anything else I can help you with.",
    "I'm at your service for any additional questions or support you may need—don't hesitate to ask."
]

# List to store chatbot messages
messages = []

# System message to provide context to the chatbot
SystemChatBot = [{"role": "system", "content": f"Hello, I am {os.environ.get('Username', 'Assistant')}, You're a content writer.You have to write content like letters,code,applications,essays,notes,songs,poem etc"}]


# Function to perform a Google search
def GoogleSearch(Topic):
    search(Topic)  # Use pywhatkit's search function to perform a Google search.
    return True  # Indicate success.


# Function to generate content using AI and save it to a file
def Content(Topic):

    def OpenNotepad(File):
        default_text_editor = 'notepad.exe'
        subprocess.Popen([default_text_editor, File])  # Open the file in Notepad.

    def ContentWriterAI(prompt):
        messages.append({"role": "user", "content": f"{prompt}"})
        completion = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=SystemChatBot + messages,
            max_tokens=2048,
            temperature=0.7,
            top_p=1,
            stream=True
        )
        Answer = ""
        for chunk in completion:
            if chunk.choices[0].delta.content:
                Answer += chunk.choices[0].delta.content
        Answer = Answer.replace("</s>", "")
        messages.append({"role": "assistant", "content": Answer})
        return Answer

    Topic = Topic.replace("Content", "").strip()
    ContentByAI = ContentWriterAI(Topic)

    file_path = rf"Data\{Topic.lower().replace(' ', '')}.txt"
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(ContentByAI)

    OpenNotepad(file_path)
    return True



# Function to search for a topic on YouTube
def YouTubeSearch(Topic):
    Url4Search = f"https://www.youtube.com/results?search_query={Topic}"
    webbrowser.open(Url4Search)
    return True



# Function to play a video on YouTube
def PlayYoutube(query):
    playonyt(query)
    return True




# Function to open an application or a relevant webpage
def OpenApp(app):
    try:
        appopen(app, match_closest=True, output=True, throw_error=True)
        return True
    except:
        return False


# Function to close an application
def CloseApp(app):
    try:
        close(app, match_closest=True, output=True, throw_error=True)
        return True
    except:
        return False


# Function to execute system-level commands
def System(command):
    def mute():
        keyboard.press_and_release("volume mute")

    def unmute():
        keyboard.press_and_release("volume mute")

    def volume_up():
        keyboard.press_and_release("volume up")

    def volume_down():
        keyboard.press_and_release("volume down")

    if command == "mute":
        mute()
    elif command == "unmute":
        unmute()
    elif command == "volume up":
        volume_up()
    elif command == "volume down":
        volume_down()

    return True


# Asynchronous function to translate and execute user commands
async def TranslateAndExecute(commands: list[str]):
    funcs = []

    for command in commands:
        if command.startswith("open"):
            funcs.append(asyncio.to_thread(OpenApp, command.removeprefix("open").strip()))
        elif command.startswith("close"):
            funcs.append(asyncio.to_thread(CloseApp, command.removeprefix("close").strip()))
        elif command.startswith("play"):
            funcs.append(asyncio.to_thread(PlayYoutube, command.removeprefix("play").strip()))
        elif command.startswith("content"):
            funcs.append(asyncio.to_thread(Content, command.removeprefix("content").strip()))
        elif command.startswith("google search"):
            funcs.append(asyncio.to_thread(GoogleSearch, command.removeprefix("google search").strip()))
        elif command.startswith("youtube search"):
            funcs.append(asyncio.to_thread(YouTubeSearch, command.removeprefix("youtube search").strip()))
        elif command.startswith("system"):
            funcs.append(asyncio.to_thread(System, command.removeprefix("system").strip()))
        else:
            print(f"No Function Found for ({command})")

    results = await asyncio.gather(*funcs)
    for result in results:
        yield result


# Asynchronous function to automate command execution
async def Automation(commands: list[str]):
    async for result in TranslateAndExecute(commands):
        pass
    return True