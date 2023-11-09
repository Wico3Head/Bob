import threading, pyttsx3, openai, pygame, json, random
import speech_recognition as sr
from sys import exit
from time import sleep
from keys import API_KEY

pygame.init()
engine = pyttsx3.init()
openai.api_key = API_KEY

SCREEN_HEIGHT, SCREEN_WIDTH = 600, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Bob")

BG_COLOUR = "#ffffff"
BLACK = "#000000"
mic_on_src = pygame.transform.scale(pygame.image.load("mic_on.png"), (300, 300))
mic_off_src = pygame.transform.scale(pygame.image.load("mic_off.png"), (300, 300))
mic_rect = mic_on_src.get_rect(center=(300, 400))

font = pygame.font.Font(None, 40)
greet_text = font.render('Welcome!', True, BLACK)
listening_text = font.render("Speak into the microphone", True, BLACK)
unknown_text = font.render("Try again", True, BLACK)
error_text = font.render("An error has occured", True, BLACK)
processing_text = font.render("Processing...", True, BLACK)
speaking_text = font.render("Speaking",True, BLACK)
finished_text = font.render("", True, BLACK)
terminate_text = font.render("Thank you, Bye!", True, BLACK)

texts = {
    "greet": greet_text,
    "listening": listening_text,
    "unknown": unknown_text,
    "error": error_text,
    "processing": processing_text,
    "speaking": speaking_text,
    "finished": finished_text,
    "terminate": terminate_text
}

promptText = """You are a virtual assistant named Bob which behaves like google assistant or alexa. Since you are a text to speech model, please convert the symbols of numbers into words in your response. After ask if the user requires any assistance, call the program terminate if the user answers no."""

question = ""
response = ""
state = "greet"
conversation = []
running = True

def greet():
    global state

    engine.say("Hi, I am Bob, Your virtual assistant. Is there anything I can help you with?")
    engine.runAndWait()
    state = "finished"

def listen():
    global question, state

    while True:
        state = "listening"

        r = sr.Recognizer()
        with sr.Microphone() as source:                                                                                                                                                       
            audio = r.listen(source)   

        try:
            question = r.recognize_google(audio)
            break
        except sr.UnknownValueError:
            state = "unknown"
            engine.say("Sorry, I did not catch that, please try again")
            engine.runAndWait() 
        except sr.RequestError as e:
            state = "error"
            engine.say("There seem to be an error, please to try again")
            engine.runAndWait()

def process():
    global response, conversation

    functions = [
        {
            "name": "terminate",
            "description": "This function will terminate the program after a few seconds",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    ]

    conversation.append(question)
    history = [{"role": "system", "content": promptText}, {"role": "assistant", "content": "Is there anything I can help you with?"},]
    for count, message in enumerate(conversation):
        history.append(
            {
                "role": "user" if count % 2 == 0 else "assistant",
                "content": message
            },
        )

    completion = openai.ChatCompletion.create(
                    model = "gpt-3.5-turbo",
                    messages = history,
                    functions=functions,
                    function_call="auto"
                    )

    first_response = completion.choices[0].message["content"]

    if first_response != None:
        response = first_response
        return
    
    response_message = completion['choices'][0]['message']
    available_functions = {
        "terminate": terminate
    } 
    function_name = response_message["function_call"]["name"]
    function_to_call = available_functions[function_name]
    function_args = json.loads(response_message["function_call"]["arguments"])
    if function_to_call == terminate:
        function_response = terminate()
        return

    history.append(response_message)
    history.append(
        {
            "role": "function",
            "name": function_name,
            "content": function_response,
        },
    )

    second_response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=history,
    ) 

    response = second_response.choices[0].message["content"]

def speak():
    global conversation, state, question, response

    engine.say(response)
    engine.runAndWait()

    if response[-1] == "?":
        conversation.append(response)
    else:
        conversationOverResponse = "Is there anything else I can help you with?"
        conversation = []

        engine.say(conversationOverResponse)
        engine.runAndWait()
        
    question = ""
    response = ""    
    state = "finished"
    
def terminate():
    global state

    engine.say("Thank you for using my services, I hope you have a great day! Bye bye.")
    engine.runAndWait()
    
    state = "terminate"
    return "program terminates soon"

def main():
    global state, running
    greeted = False

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or state == "terminate":
                pygame.quit()
                exit()

        if not greeted:
            greet_thread = threading.Thread(target=greet)
            greet_thread.start()
            greeted = True
        elif question == "" and state == "finished":
            state = "listening"
            listen_thread = threading.Thread(target=listen)
            listen_thread.start()
        elif question != "" and state == "listening":
            state = "processing"
            processing_thread = threading.Thread(target=process)
            processing_thread.start()
            running = False
        elif response != "" and state == "processing":
            state = "speaking"
            speaking_thread = threading.Thread(target=speak)
            speaking_thread.start()
        
        screen.fill(BG_COLOUR)
        screen.blit(mic_on_src if state == "listening" else mic_off_src, mic_rect)
        text = texts[state]
        text_rect = text.get_rect(center=(300, 100))
        screen.blit(text, text_rect)

        pygame.display.update()    

if __name__ == "__main__":
    main()