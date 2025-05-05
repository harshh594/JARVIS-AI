from Frontend.GUI import (
    GraphicalUserInterface,
    SetAssistantStatus,
    ShowTextToScreen,
    TempDirectoryPath,
    SetMicrophoneStatus,
    AnswerModifier,
    QueryModifier,
    GetMicrophoneStatus,
    GetAssistantStatus
)

from Backend.Model import FirstLayerDMM
from Backend.RealtimeSearchEngine import RealtimeSearchEngine, send_to_arduino   # ✅ ADDED
from Backend.Automation import Automation
from Backend.SpeechToText import SpeechRecognition
from Backend.Chatbot import ChatBot
from Backend.TextToSpeech import TextToSpeech
from dotenv import dotenv_values
from asyncio import run
from time import sleep
import subprocess
import threading
import json
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

# Constants for file paths
CHATLOG_PATH = r'Data\ChatLog.json'
DATABASE_PATH = TempDirectoryPath('Database.data')
RESPONSES_PATH = TempDirectoryPath('Responses.data')
IMAGE_GEN_PATH = r"Frontend\Files\ImageGeneration.data"

# Load environment variables
env_vars = dotenv_values(".env")
Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "Assistant")
InputLanguage = env_vars.get("InputLanguage", "en-US")

DefaultMessage = f"""{Username}: Hello {Assistantname}, How are you?

{Assistantname}: Welcome {Username}. I am doing well. How may I help you?"""

subprocesses = []
Functions = ["open", "close", "play", "system", "content", "google search", "youtube search"]

def ShowDefaultChatIfNoChats():
    if not os.path.exists(CHATLOG_PATH) or os.stat(CHATLOG_PATH).st_size < 5:
        with open(DATABASE_PATH, 'w', encoding='utf-8') as db_file:
            db_file.write("")
        with open(RESPONSES_PATH, 'w', encoding='utf-8') as resp_file:
            resp_file.write(DefaultMessage)

def ReadChatLogJson():
    with open(CHATLOG_PATH, 'r', encoding='utf-8') as file:
        return json.load(file)

def ChatLogIntegration():
    json_data = ReadChatLogJson()
    formatted_chatlog = "\n".join(
        f"{Username if entry['role'] == 'user' else Assistantname}: {entry['content']}"
        for entry in json_data
    )
    with open(DATABASE_PATH, 'w', encoding='utf-8') as file:
        file.write(AnswerModifier(formatted_chatlog))

def ShowChatsOnGUI():
    with open(DATABASE_PATH, "r", encoding='utf-8') as file:
        data = file.read()
        if data:
            with open(RESPONSES_PATH, "w", encoding='utf-8') as resp_file:
                resp_file.write(data)

def InitialExecution():
    SetMicrophoneStatus("True")
    ShowTextToScreen("")
    ShowDefaultChatIfNoChats()
    ChatLogIntegration()
    ShowChatsOnGUI()

InitialExecution()

# ✅ FIX 1: TextToSpeech ko timeout ke saath run karna
def speak_with_timeout(answer):
    def speak():
        TextToSpeech(answer)
    
    tts_thread = threading.Thread(target=speak)
    tts_thread.start()
    
    # Wait for a maximum of 5 seconds
    tts_thread.join(timeout=5)

    if tts_thread.is_alive():
        logging.warning("TextToSpeech taking too long, skipping to next task.")

def MainExecution():
    """Main execution logic."""
    TaskExecution = False
    ImageExecution = False
    ImageGenerationQuery = ""

    SetAssistantStatus("Listening...")

    current_dir = os.getcwd()
    Link = f"{current_dir}/Data/Voice.html"

    Query = SpeechRecognition(Link, InputLanguage)

    ShowTextToScreen(f"{Username}: {Query}")
    SetAssistantStatus("Thinking...")

    # ✅ CHECK FOR ARDUINO LIGHT COMMANDS
    lower_query = Query.lower()
    if "turn on light" in lower_query or "light on" in lower_query:
        send_to_arduino("turn_on")
        ShowTextToScreen(f"{Assistantname}: Turning on the light.")
        speak_with_timeout("Turning on the light")
        SetAssistantStatus("Available...")
        return
    elif "turn off light" in lower_query or "light off" in lower_query:
        send_to_arduino("turn_off")
        ShowTextToScreen(f"{Assistantname}: Turning off the light.")
        speak_with_timeout("Turning off the light")
        SetAssistantStatus("Available...")
        return

    Decision = FirstLayerDMM(Query)
    logging.info(f"Decision: {Decision}")

    G = [i for i in Decision if i.startswith("general")]
    R = [i for i in Decision if i.startswith("realtime")]
    Merged_query = " and ".join(
        " ".join(i.split()[1:]) for i in Decision if i.startswith("general") or i.startswith("realtime")
    )
    
    for queries in Decision:
        if "generate" in queries:
            ImageGenerationQuery = queries
            ImageExecution = True
    
    for queries in Decision:
        if not TaskExecution and any(queries.startswith(func) for func in Functions):
            run(Automation(list(Decision)))
            TaskExecution = True
    
    if ImageExecution:
        with open(IMAGE_GEN_PATH, "w") as file:
            file.write(f"{ImageGenerationQuery}, True")
        try:
            p1 = subprocess.Popen(['python', r'Backend\ImageGeneration.py'], stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, stdin=subprocess.PIPE, shell=False)
            subprocesses.append(p1)
        except Exception as e:
            logging.error(f"Error starting ImageGeneration.py: {e}")
    
    if G and R or R:
        SetAssistantStatus("Searching...")
        Answer = RealtimeSearchEngine(QueryModifier(Merged_query))
        ShowTextToScreen(f"{Assistantname}: {Answer}")
        SetAssistantStatus("Answering...")
        speak_with_timeout(Answer)
    else:
        for Queries in Decision:
            QueryFinal = Queries.replace("general", "").replace("realtime", "")
            if "general" in Queries:
                SetAssistantStatus("Thinking...")
                Answer = ChatBot(QueryModifier(QueryFinal))
            elif "realtime" in Queries:
                SetAssistantStatus("Searching...")
                Answer = RealtimeSearchEngine(QueryModifier(QueryFinal))
            elif "exit" in Queries:
                Answer = ChatBot(QueryModifier("Okay, Bye!"))
                os._exit(1)
            else:
                continue
            
            ShowTextToScreen(f"{Assistantname}: {Answer}")
            SetAssistantStatus("Answering...")
            speak_with_timeout(Answer)

    SetAssistantStatus("Available...")
    logging.info("Assistant is now available...")

def FirstThread():
    while True:
        mic_status = GetMicrophoneStatus()
        ai_status = GetAssistantStatus()

        if mic_status == "True":  
            SetAssistantStatus("Listening...")
            MainExecution()
        else:
            if ai_status != "Available...":
                SetAssistantStatus("Available...")

        sleep(0.1)

def SecondThread():
    GraphicalUserInterface()

if __name__ == "__main__":
    thread2 = threading.Thread(target=FirstThread, daemon=True)
    thread2.start()
    SecondThread()