import pygame, sys, pyaudio, wave, threading, librosa, datetime, json, requests, pickle
from openai import OpenAI
from settings import *
from keys import OPENAI_API_KEY, WEATHER_API_KEY
pygame.init()
p = pyaudio.PyAudio()
client = OpenAI(api_key=OPENAI_API_KEY)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Bob - Your Virtual Assistant")
pygame.display.set_icon(ICON)

press_btn_msg = FONT.render("Press the button to speak!", True, "white")
press_btn_msg_rect = press_btn_msg.get_rect(center=(SCREEN_WIDTH/2, 150))

too_short_msg = FONT.render("Too Short! Please try again", True, "white")
too_short_msg_rect = press_btn_msg.get_rect(center=(SCREEN_WIDTH/2, 150))

listening_msg = FONT.render("Listening...", True, "white")
listening_msg_rect = listening_msg.get_rect(center=(SCREEN_WIDTH/2, 150))

processing_msg = FONT.render("Thinking...", True, "white")
processing_msg_rect = processing_msg.get_rect(center=(SCREEN_WIDTH/2, 150))

speaking_msg = FONT.render("Speaking", True, "white")
speaking_msg_rect = processing_msg.get_rect(center=(SCREEN_WIDTH/2, 150))

music_playing_msg = FONT.render("Music Playing", True, "white")
music_playing_msg_rect = music_playing_msg.get_rect(center=(SCREEN_WIDTH/2, 150))

mic = pygame.transform.scale(pygame.image.load(os.path.join(LOCAL_DIR, "Assets/mic.png")), (300, 300))
mic_rect = mic.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2+100))
mic_btn = pygame.Rect(220, 320, 360, 360)

def getTime():
    weekday = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return str(datetime.datetime.now()) + weekday[datetime.datetime.today().weekday()]

def get_ip():
    response = requests.get('https://api64.ipify.org?format=json').json()
    return response["ip"]


def getLocation():
    ip_address = get_ip()
    response = requests.get(f'https://ipapi.co/{ip_address}/json/').json()
    response_text = f"city:{response.get('city')}, region:{response.get('region')}, country:{response.get('country')}, latitude:{response.get('latitude')}, longitude:{response.get('longitude')}"
    
    if response.get("error"):
        try:
            with open("prev_location.pkl", "rb") as f:
                prev_location = pickle.load(f)
            return "An error occured, but the system found previous location history: " + prev_location
        except:
            return "An error occured, the system try searching for previous location history but none was found. Please try again later"  
    else:
        with open("prev_location.pkl", "wb") as f:
            pickle.dump(response_text, f)

        return response_text
    
def getWeather(lat, lon):
    response = requests.get(f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}").json()
    return f"The current temperature is {round(response['current']['temp']-273.16, 2)}. Weather: {response['current']['weather'][0]['main']}, Description: {response['current']['weather'][0]['description']}"

def musicPlayingThread(filename):
    global state
    try:
        pygame.mixer.music.load(os.path.join(LOCAL_DIR, "music/" + filename))
        pygame.mixer.music.play()
        state = "music"
    except:
        return
    
    while True:
        if not pygame.mixer.music.get_busy():
            return


def play(filename):
    global state
    music_thread = threading.Thread(target=musicPlayingThread, args=[filename])
    music_thread.start()
    music_thread.join()
    if state == "music":
        return "The song has finished playing"
    return "The song is not in the playlist, please add it in and restart the program."

def playMusic(request):
    current_conversation = [{"role": "system", "content": MUSIC_PROMPT}]

    tools = [
            {
                "type": "function",
                "function": {
                    "name": "play",
                    "description": "Pass in the filename of the song and it was start playing automatically.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filename": {
                                "type": "string",
                                "description": "filename of the song"
                            }
                        },
                        "required": ["filename"]
                    }
                }
            }]

    current_conversation.append({"role": "user", "content": request})
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=current_conversation,
        tools=tools,
        tool_choice="auto"
    )

    tool_calls = response.choices[0].message.tool_calls

    if tool_calls:
        available_functions = {
            "play": play,
        } 

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            return function_to_call(filename=function_args.get("filename"))

def process_speech():
    global state, history, calls_num
    current_conversation = [{"role": "system", "content": PROMPT}, {"role": "system", "content": f"the chat history between you and the user are included here\n{history}"}]

    tools = [{
                "type": "function",
                "function": {
                    "name": "getTime",
                    "description": "get the current date and time in the form of year-month-day hour-minute-second-millisecond weekday, only call the function if the user ask for the time",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "getLocation",
                    "description": "return the user's location including the latitude and longitude or tell you if an error occured and any previous location history was found, please be aware that this function doesn't give you any weather information",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "playMusic",
                    "description": "Pass in the user's request and it will automatically detect the song title and play the song if it is in a playlist, it also returns whether a song is played or not",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "request": {
                                "type": "string",
                                "description": "The request from the user"
                            }
                        },
                        "required": ["request"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "getWeather",
                    "description": "Pass in the latitude and longitude and it will return the weather related data like temperature, etc",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "lat": {
                                "type": "number",
                                "description": "The latitude of the user's location"
                            },
                            "lon": {
                                "type": "number",
                                "description": "The longitude of the user's location"
                            }
                        },
                        "required": ["lat", "lon"]
                    }
                }
            }]

    audio_file = open(os.path.join(LOCAL_DIR, "output.mp3"), "rb")
    transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file, response_format="text")
    history += f"user: {transcript}\n"  
    current_conversation.append({"role": "user", "content": transcript})

    response = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=current_conversation,
        tools=tools,
        tool_choice="auto"
    )
    response_text = response.choices[0].message
    tool_calls = response_text.tool_calls

    if tool_calls:
        available_functions = {
            "getTime": getTime,
            "playMusic": playMusic,
            "getLocation": getLocation,
            "getWeather": getWeather
        } 
        
        current_conversation.append(response_text)
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            print(function_name)
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)

            if function_to_call == getTime:
                function_response = function_to_call()
            elif function_to_call == playMusic:
                function_response = function_to_call(request=function_args.get("request"))
            elif function_to_call == getLocation:
                function_response = function_to_call()
            elif function_to_call == getWeather:
                function_response = function_to_call(lat=function_args.get("lat"), lon=function_args.get("lon"))

            current_conversation.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                }
            ) 

        new_response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=current_conversation,
        )   

        response_text = new_response.choices[0].message
        if state == "music":
            state = "speaking"

    history += f"assistant: {response_text.content}\n"
    speech_filepath = os.path.join(LOCAL_DIR, f"speech{calls_num}.mp3")
    response = client.audio.speech.create(
        model="tts-1",
        voice="fable",
        input=response_text.content
    )

    response.stream_to_file(speech_filepath)
    pygame.mixer.music.load(os.path.join(LOCAL_DIR, f"speech{calls_num}.mp3"))
    pygame.mixer.music.play()
    state = "speaking"
    calls_num += 1

state = "idle"
show_too_short_msg = False
calls_num = 0
history = ""
def main():
    global state, show_too_short_msg, history
    frames = []
    stream = None

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                
                try:
                    os.remove(os.path.join(LOCAL_DIR, "output.mp3"))
                except:
                    print("output.mp3 was not found")
                
                for num in range(calls_num):
                    try:
                        os.remove(os.path.join(LOCAL_DIR, f"speech{num}.mp3"))
                    except:
                        print(f"speech{num}.mp3 was not found.")
                    
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                if mic_btn.collidepoint(pos) and state == "idle":
                    state = "recording"
                    stream = p.open(format=FORMAT, channels=CHANNELS, rate=FS, input=True, frames_per_buffer=CHUNK)
            elif event.type == pygame.MOUSEBUTTONUP:
                if state == "recording":
                    stream.close()
                    wf = wave.open(FILENAME, 'wb')
                    wf.setnchannels(CHANNELS)
                    wf.setsampwidth(p.get_sample_size(FORMAT))
                    wf.setframerate(FS)
                    wf.writeframes(b''.join(frames))
                    wf.close()
                    frames.clear()

                    length = librosa.get_duration(path=FILENAME)
                    if length <= 0.5:
                        state = "idle"
                        show_too_short_msg = True
                    else:
                        process_thread = threading.Thread(target=process_speech)
                        process_thread.start()
                        state = "processing"
                        show_too_short_msg = False

        screen.fill(BG_COLOR)

        if state == "idle":
            if show_too_short_msg:
                screen.blit(too_short_msg, too_short_msg_rect)
            else:
                screen.blit(press_btn_msg, press_btn_msg_rect)
        elif state == "recording":
            screen.blit(listening_msg, listening_msg_rect)
        elif state == "processing":
            screen.blit(processing_msg, processing_msg_rect)
        elif state == "speaking":
            screen.blit(speaking_msg, speaking_msg_rect)
        elif state == "music":
            screen.blit(music_playing_msg, music_playing_msg_rect)
        
        mouse = pygame.mouse.get_pos()
        current_mic_colour = BTN_COLOR
        if state == "idle" or state == "recording":
            if mic_btn.collidepoint(mouse):
                current_mic_colour = BTN_HOVER_COLOR
        elif state != "recording":
            current_mic_colour = BTN_DISABLED_COLOR

        if state == "recording":
            data = stream.read(CHUNK)
            frames.append(data) 
        elif state == "speaking":
            if not pygame.mixer.music.get_busy():
                state = "idle"

        pygame.draw.rect(screen, current_mic_colour, mic_btn, border_radius=50)
        screen.blit(mic, mic_rect)
        pygame.display.update()

if __name__ == "__main__":
    main()