import openai
import json

question = "Is Alex Fenn a femboy?"

openai.api_key = "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"
response = ""
responseType = "first"

def isHeAFemboy(name):
    if "alex" in name.lower():
        return "Alex Fenn is currently a femboy."
    else:
        isFemboy = not sum(ord(char) for char in name)
        if isFemboy:
            return f"{name} is a femboy currently."
        return f"{name} is not a femboy currently"

def run_conversation():
    global response, responseType
    messages = [{"role": "user", "content": question}]
    functions = [
        {
            "name": "isHeAFemboy",
            "description": "A function that tells you if someone is a femboy by entering their name",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The name of a person. For example: Alex",
                    }
                },
                "required": ["name"],
            }
        }
    ]

    completion = openai.ChatCompletion.create(
                    model = "gpt-3.5-turbo-0613",
                    temperature = 0.8,
                    max_tokens = 2000,
                    messages = messages,
                    functions=functions,
                    function_call="auto"
                    )

    first_response = completion.choices[0].message["content"]

    if first_response != None:
        response = first_response
        return
    
    response_message = completion['choices'][0]['message']
    available_functions = {
        "isHeAFemboy": isHeAFemboy
    } 
    function_name = response_message["function_call"]["name"]
    function_to_call = available_functions[function_name]
    function_args = json.loads(response_message["function_call"]["arguments"])
    if function_to_call == isHeAFemboy:
        function_response = function_to_call(
            name=function_args.get("name")
        )

    messages.append(response_message)
    print(function_response)
    messages.append(
        {
            "role": "function",
            "name": function_name,
            "content": function_response,
        },
    )
    second_response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0613",
        messages=messages,
    ) 

    response = second_response.choices[0].message["content"]
    responseType = "second"

run_conversation()
print(response)
print(responseType)