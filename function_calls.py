import os
import json
import openai
import requests
from openai import OpenAI
from datetime import datetime, timedelta
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, ChatMessage

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
weather_api_key = os.getenv("WEATHER_API_KEY")

client = OpenAI()

# SHOW EXAMPLE WITHOUT FUNCTION CALLS

completion = client.chat.completions.create(
    model="gpt-3.5-turbo-0613",
    messages=[
        {
            "role": "user",
            "content": "What is the weather in Bristol?",
        },
    ],
)

output = completion.choices[0].message.content
print(output)

# EXAMPLE WITH FUNCTION CALLS

function_descriptions = [
    {
        "name": "create_folder",
        "description": "Create folder in the correct directory",
        "parameters": {
            "type": "object",
            "properties": {
                "directory_name": {
                    "type": "string",
                    "description": "The name of the directory to be created",
                },
                "parent_directory": {
                    "type": "string",
                    "description": "The path of the parent directory",
                },
            },
            "required": ["directory_name", "parent_directory"],
        },
    },
    {
        "name": "get_weather",
        "description": "Get the current weather for a specific location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The location that the weather is required",
                },
            },
            "required": ["location"],
        },
    }
]

print(function_descriptions)

system_message = """
    You are a conversational and friendly bot able to do 2 things, 
    create directories where a folder name is provided and get the 
    current weather for a specific location. 
    
    The parent directory path is 'C:/Dev/ai/make-folder/' when 
    creating directories. 
    
    If the boolean 'is_created' is false you should say that you 
    were unable to create the directory. 
    
    If the 'exists_already' boolean is true, you can determine 
    that the reason the directory was not able to be created 
    was due to it already existing. 
    
    If the task is to do something other 
    than create directories or getting the current weather 
    reply saying that you are not able to do so.
"""


# CHANGE PROMPT HERE
user_prompt = "What is 1 + 1"

completion = client.chat.completions.create(
    model="gpt-3.5-turbo-0613",
    messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_prompt}
        ],
    functions=function_descriptions,
    function_call="auto",
)

output = completion.choices[0].message
print(output)

def create_folder(directory_name, parent_directory):
    is_created = False
    exists_already = False
    try:
        path = os.path.join(parent_directory, directory_name)
        
        os.mkdir(path)
        
        is_created = True
        
    except FileExistsError:
        exists_already = True
    
    new_directory = {
            "directory_name": directory_name,
            "file_path": path,
            "is_created": is_created,
            "exists_already": exists_already
        }
        
    return json.dumps(new_directory, indent=4)


def get_weather(location):
    base_url = "http://api.weatherapi.com/v1/current.json"
    
    complete_url = base_url + "?key=" + weather_api_key + "&q=" + location
    
    try: 
        response = requests.get(complete_url)
        json_response = response.json()
        
        weather_info = {
            "location": json_response["location"]["name"],
            "temperature": json_response["current"]["temp_c"]
        }
        
        return json.dumps(weather_info, indent=4)
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)


try:
    params = json.loads(output.function_call.arguments)
        
    chosen_function = eval(output.function_call.name)
    outcome = chosen_function(**params)
    
    second_completion = client.chat.completions.create(
        model="gpt-3.5-turbo-0613",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_prompt},
            {"role": "function", "name": output.function_call.name, "content": outcome},
        ],
        functions=function_descriptions,
    )  

    final_response = second_completion.choices[0].message.content
    print(final_response)
except AttributeError: 
    print(output.content)
    
    