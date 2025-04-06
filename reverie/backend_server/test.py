"""
Author: Joon Sung Park (joonspk@stanford.edu)

File: test.py
Description: Test file for Ollama or OpenAI integration.
"""
import json
import random
import time
import requests

from utils import *

# Configuration
USE_OLLAMA = use_ollama  # Use the setting from utils.py
OLLAMA_BASE_URL = ollama_base_url  # Use the URL from utils.py
OLLAMA_MODEL = ollama_model  # Use the model from utils.py

# Only import OpenAI if needed
if not USE_OLLAMA:
    import openai
    openai.api_key = openai_api_key

def ollama_chat_request(prompt, model=None):
    """
    Make a request to Ollama API with proper streaming response handling
    """
    # Use the model from utils.py if not specified
    if model is None:
        model = OLLAMA_MODEL

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": True
            },
            stream=True
        )

        if response.status_code != 200:
            print(f"Ollama Error: {response.status_code}")
            return "Ollama Error"

        # Initialize an empty string to store the complete response
        full_response = ""

        # Process the streaming response
        for line in response.iter_lines():
            if line:
                try:
                    json_response = json.loads(line)
                    if 'message' in json_response and 'content' in json_response['message']:
                        content = json_response['message']['content']
                        full_response += content
                except json.JSONDecodeError:
                    continue

        return full_response.strip()

    except Exception as e:
        print(f"Ollama Error: {str(e)}")
        return "Ollama Error"

def ChatGPT_request(prompt):
    """
    Given a prompt and a dictionary of GPT parameters, make a request to OpenAI
    or Ollama server and returns the response.
    ARGS:
      prompt: a str prompt
    RETURNS:
      a str response from the language model
    """
    if USE_OLLAMA:
        return ollama_chat_request(prompt)

    try:
        completion = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
        )
        return completion["choices"][0]["message"]["content"]

    except:
        print ("ChatGPT ERROR")
        return "ChatGPT ERROR"

prompt = """
---
Character 1: Maria Lopez is working on her physics degree and streaming games on Twitch to make some extra money. She visits Hobbs Cafe for studying and eating just about everyday.
Character 2: Klaus Mueller is writing a research paper on the effects of gentrification in low-income communities.

Past Context:
138 minutes ago, Maria Lopez and Klaus Mueller were already conversing about conversing about Maria's research paper mentioned by Klaus This context takes place after that conversation.

Current Context: Maria Lopez was attending her Physics class (preparing for the next lecture) when Maria Lopez saw Klaus Mueller in the middle of working on his research paper at the library (writing the introduction).
Maria Lopez is thinking of initating a conversation with Klaus Mueller.
Current Location: library in Oak Hill College

(This is what is in Maria Lopez's head: Maria Lopez should remember to follow up with Klaus Mueller about his thoughts on her research paper. Beyond this, Maria Lopez doesn't necessarily know anything more about Klaus Mueller)

(This is what is in Klaus Mueller's head: Klaus Mueller should remember to ask Maria Lopez about her research paper, as she found it interesting that he mentioned it. Beyond this, Klaus Mueller doesn't necessarily know anything more about Maria Lopez)

Here is their conversation.

Maria Lopez: "
---
Output the response to the prompt above in json. The output should be a list of list where the inner lists are in the form of ["<Name>", "<Utterance>"]. Output multiple utterances in ther conversation until the conversation comes to a natural conclusion.
Example output json:
{"output": "[["Jane Doe", "Hi!"], ["John Doe", "Hello there!"] ... ]"}
"""

print (ChatGPT_request(prompt))
