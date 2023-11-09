import pyttsx3, openai
import speech_recognition as sr
from time import sleep

engine = pyttsx3.init()
openai.api_key = "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"

def main():
    engine.say("Hi, I am Bob, Your virtual assistant. What can I do for you today?")
    engine.runAndWait()

    while True:
        r = sr.Recognizer()
        with sr.Microphone() as source:                                                                                                                                                       
            audio = r.listen(source)   

        try:
            question = r.recognize_google(audio)
            print("processing...")
        except sr.UnknownValueError:
            engine.say("Sorry, I did not catch that, please try again")
            engine.runAndWait()
            continue
        except sr.RequestError as e:
            engine.say("There seem to be an error, please to try again")
            engine.runAndWait()
            continue


        conversationOver = False
        conversation = [question]
        while (not conversationOver):
            history = [{"role": "system", "content": "You are a virtual assistant named Bob which behaves like google assistant or alexa. Everytime you are asked a question, you only have one chance to respond, so there is no need to ask followup questions."},]
            for count, message in enumerate(conversation):
                history.append(
                    {
                        "role": "user" if count % 2 == 0 else "assistant",
                        "content": message
                    },
                )

            completion = openai.ChatCompletion.create(
                            model = "gpt-3.5-turbo",
                            temperature = 0.8,
                            max_tokens = 2000,
                            messages = history
                            )

            response = completion.choices[0].message["content"]
            engine.say(response)
            engine.runAndWait()
            conversation.append(response)

            if response[-1] != "?":
                conversationOver = True
            else:
                while True:
                    r = sr.Recognizer()
                    with sr.Microphone() as source:                                                                                                                                                       
                        audio = r.listen(source)   

                    try:
                        question = r.recognize_google(audio)
                        conversation.append(question)
                        break
                    except sr.UnknownValueError:
                        engine.say("Sorry, I did not catch that, please try again")
                        engine.runAndWait()
                    except sr.RequestError as e:
                        engine.say("There seem to be an error, please to try again")
                        engine.runAndWait()

        sleep(1)
        engine.say("Is there anything else you need help with?")
        engine.runAndWait()

if __name__ == "__main__":
    main()