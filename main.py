import pygame, sys, pyaudio, wave, threading, librosa, datetime, json
from openai import OpenAI
from settings import *
from keys import API_KEY
pygame.init()
p = pyaudio.PyAudio()
client = OpenAI(api_key=API_KEY)

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

mic = pygame.transform.scale(pygame.image.load(os.path.join(LOCAL_DIR, "Assets/mic.png")), (300, 300))
mic_rect = mic.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2+100))
mic_btn = pygame.Rect(220, 320, 360, 360)

def getTime():
    return str(datetime.datetime.now()) + str(datetime.datetime.today().weekday())

def getHistory():
    return history

def process_speech():
    global state, history, calls_num
    current_conversation = [{"role": "system", "content": PROMPT}, {"role": "system", "content": f"the chat history between you and the user are included here\n{history}"}]

    functions = [
            {
                "name": "getTime",
                "description": "get the current date and time in the form of year-month-day hour-minute-second-millisecond weekday",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
    ]

    audio_file = open(os.path.join(LOCAL_DIR, "output.mp3"), "rb")
    transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file, response_format="text")
    history += f"user: {transcript}\n"
    current_conversation.append({"role": "user", "content": transcript})

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=current_conversation,
        functions=functions,
        function_call="auto"
    )
    response_text = response.choices[0].message.content

    while response_text == None:
        function_call = response.choices[0].message.function_call
        available_functions = {
            "getTime": getTime,
        } 
        function_name = function_call.name
        function_to_call = available_functions[function_name]
        function_args = function_call.arguments

        if function_to_call == getTime:
            function_response = getTime()

        current_conversation.append(
            {
                "role": "function",
                "name": function_name,
                "content": function_response,
            },
        )

        new_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=current_conversation,
            functions=functions,
            function_call="auto"
        ) 

        response_text = new_response.choices[0].message.content

    history += f"assistant: {response_text}\n"
    speech_filepath = os.path.join(LOCAL_DIR, f"speech{calls_num}.mp3")
    response = client.audio.speech.create(
        model="tts-1",
        voice="fable",
        input=response_text
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
                try:
                    os.remove(os.path.join(LOCAL_DIR, "output.mp3"))
                except:
                    print("output.mp3 was not found")
                
                for num in range(calls_num):
                    try:
                        os.remove(os.path.join(LOCAL_DIR, f"speech{num}.mp3"))
                    except:
                        print(f"speech{num}.mp3 was not found.")
                    
                pygame.quit()
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