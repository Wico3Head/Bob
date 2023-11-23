import pygame, os, pyaudio
pygame.init()

SCREEN_WIDTH, SCREEN_HEIGHT = 800, 800
LOCAL_DIR = os.path.dirname(__file__)
ICON = pygame.image.load(os.path.join(LOCAL_DIR, "Assets/circle-pepe.png"))
FONT = pygame.font.Font(os.path.join(LOCAL_DIR, "Assets/Montserrat-Regular.ttf"), 45)

BG_COLOR = "#3b3b3b"
BTN_COLOR = "#828282"
BTN_HOVER_COLOR = "#616160"
BTN_DISABLED_COLOR = "#505050"

CHUNK = 3024
FORMAT = pyaudio.paInt16
CHANNELS = 1
FS = 44100
FILENAME = "output.mp3"

PROMPT = """
You are a virtual assistant named Bob which behaves like google assistant or alexa. You have memory as the previous
chat history are attached before the user's request. The following introduces the functions you have access to:

getTime: returns the current time and date in the format year-month-day hour-minute-second-millisecond,
in any time related questions please use this function to check the current time before answering

Remember not to rush any answers, take a deep breath and slowly work through the user's request step by step"""