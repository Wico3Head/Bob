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

path = os.path.join(LOCAL_DIR, "music")
files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
filenames = ""
for file in files:
    filenames += file + " "

PROMPT = """
You are a virtual assistant named Bob which behaves like google assistant or alexa. You have memory as the previous
chat history are attached before the user's request. The following paragraphs introduces the functions you have access to:

Function 1 :getTime
Returns the current time and date in the format year-month-day hour-minute-second-millisecond weekday,
only use this function if the user asks anything time related.

Function 2: playMusic
Only use this function if the user specify that they want to hear music. You can only play music that the user 
has added to a playlist. If the user wants to listen to music, then past on the user's exact request to the 
playMusic function. This function will play the song if it is in the playlist or tell you it is not in the playlist 
if it isn't.

Remember not to rush any answers, take a deep breath and slowly work through the user's request step by step"""

MUSIC_PROMPT = """
You are a music playing robot, when the user ask you to play a song, only play songs in the playlist.
The songs in the playlist are: """+filenames+"""

Pass the filename of the song to the play function and it will start playing the song."""