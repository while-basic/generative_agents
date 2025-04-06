"""
Author: Joon Sung Park (joonspk@stanford.edu)

File: gpt_structure.py
Description: Wrapper functions for calling OpenAI and Ollama APIs.
"""
import json
import random
import time
import requests
import sys
import os
import numpy as np

# Only import OpenAI if needed
try:
    import openai
except ImportError:
    openai = None

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils import *

# Configuration
USE_OLLAMA = use_ollama  # Use the setting from utils.py
OLLAMA_BASE_URL = ollama_base_url  # Use the URL from utils.py
OLLAMA_MODEL = ollama_model  # Use the model from utils.py
if not USE_OLLAMA:
    openai.api_key = openai_api_key

def temp_sleep(seconds=0.1):
  time.sleep(seconds)

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

def ChatGPT_single_request(prompt):
    if USE_OLLAMA:
        return ollama_chat_request(prompt)

    temp_sleep()
    completion = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return completion["choices"][0]["message"]["content"]

def GPT4_request(prompt):
    """
    Given a prompt and a dictionary of GPT parameters, make a request to OpenAI
    or Ollama server and returns the response.
    """
    if USE_OLLAMA:
        return ollama_chat_request(prompt)

    temp_sleep()
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return completion["choices"][0]["message"]["content"]
    except:
        print("ChatGPT ERROR")
        return "ChatGPT ERROR"

def ChatGPT_request(prompt):
    """
    Given a prompt and a dictionary of GPT parameters, make a request to OpenAI
    or Ollama server and returns the response.
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
        print("ChatGPT ERROR")
        return "ChatGPT ERROR"

def GPT_request(prompt, gpt_parameter):
    """
    Legacy GPT-3 request function, modified to support both OpenAI and Ollama
    """
    if USE_OLLAMA:
        return ollama_chat_request(prompt)

    temp_sleep()
    try:
        # Convert legacy parameters to chat completion format
        messages = [{"role": "user", "content": prompt}]

        response = openai.ChatCompletion.create(
            model=gpt_parameter.get("model", "gpt-4o-mini"),
            messages=messages,
            max_tokens=gpt_parameter.get("max_tokens", 50),
            temperature=gpt_parameter.get("temperature", 0),
            top_p=gpt_parameter.get("top_p", 1),
            stream=gpt_parameter.get("stream", False),
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"GPT Error: {str(e)}")
        return "GPT Error"

def GPT4_safe_generate_response(prompt,
                                   example_output,
                                   special_instruction,
                                   repeat=3,
                                   fail_safe_response="error",
                                   func_validate=None,
                                   func_clean_up=None,
                                   verbose=False):
    prompt = 'GPT-4o-mini Prompt:\n"""\n' + prompt + '\n"""\n'
    prompt += f"Output the response to the prompt above in json. {special_instruction}\n"
    prompt += "Example output json:\n"
    prompt += '{"output": "' + str(example_output) + '"}'

    if verbose:
        print("CHAT GPT PROMPT")
        print(prompt)

    for i in range(repeat):

        try:
            curr_gpt_response = GPT4_request(prompt).strip()
            end_index = curr_gpt_response.rfind('}') + 1
            curr_gpt_response = curr_gpt_response[:end_index]
            curr_gpt_response = json.loads(curr_gpt_response)["output"]

            if func_validate(curr_gpt_response, prompt=prompt):
                return func_clean_up(curr_gpt_response, prompt=prompt)

            if verbose:
                print("---- repeat count: \n", i, curr_gpt_response)
                print(curr_gpt_response)
                print("~~~~")

        except:
            pass

    return False


def ChatGPT_safe_generate_response(prompt,
                                   example_output,
                                   special_instruction,
                                   repeat=3,
                                   fail_safe_response="error",
                                   func_validate=None,
                                   func_clean_up=None,
                                   verbose=False):
    # prompt = 'GPT-3 Prompt:\n"""\n' + prompt + '\n"""\n'
    prompt = '"""\n' + prompt + '\n"""\n'
    prompt += f"Output the response to the prompt above in json. {special_instruction}\n"
    prompt += "Example output json:\n"
    prompt += '{"output": "' + str(example_output) + '"}'

    if verbose:
        print("CHAT GPT PROMPT")
        print(prompt)

    for i in range(repeat):

        try:
            curr_gpt_response = ChatGPT_request(prompt).strip()
            end_index = curr_gpt_response.rfind('}') + 1
            curr_gpt_response = curr_gpt_response[:end_index]
            curr_gpt_response = json.loads(curr_gpt_response)["output"]

            # print("---ashdfaf")
            # print(curr_gpt_response)
            # print("000asdfhia")

            if func_validate(curr_gpt_response, prompt=prompt):
                return func_clean_up(curr_gpt_response, prompt=prompt)

            if verbose:
                print("---- repeat count: \n", i, curr_gpt_response)
                print(curr_gpt_response)
                print("~~~~")

        except:
            pass

    return False


def ChatGPT_safe_generate_response_OLD(prompt,
                                   repeat=3,
                                   fail_safe_response="error",
                                   func_validate=None,
                                   func_clean_up=None,
                                   verbose=False):
    if verbose:
        print("CHAT GPT PROMPT")
        print(prompt)

    for i in range(repeat):
        try:
            curr_gpt_response = ChatGPT_request(prompt).strip()
            if func_validate(curr_gpt_response, prompt=prompt):
                return func_clean_up(curr_gpt_response, prompt=prompt)
            if verbose:
                print(f"---- repeat count: {i}")
                print(curr_gpt_response)
                print("~~~~")

        except:
            pass
    print("FAIL SAFE TRIGGERED")
    return fail_safe_response


# ============================================================================
# ###################[SECTION 2: ORIGINAL GPT-3 STRUCTURE] ###################
# ============================================================================

def generate_prompt(curr_input, prompt_lib_file):
    """
    Takes in the current input (e.g. comment that you want to classifiy) and
    the path to a prompt file. The prompt file contains the raw str prompt that
    will be used, which contains the following substr: !<INPUT>! -- this
    function replaces this substr with the actual curr_input to produce the
    final promopt that will be sent to the GPT3 server.
    ARGS:
        curr_input: the input we want to feed in (IF THERE ARE MORE THAN ONE
                    INPUT, THIS CAN BE A LIST.)
        prompt_lib_file: the path to the promopt file.
    RETURNS:
        a str prompt that will be sent to OpenAI's GPT server.
    """
    if type(curr_input) == type("string"):
        curr_input = [curr_input]
    curr_input = [str(i) for i in curr_input]

    f = open(prompt_lib_file, "r")
    prompt = f.read()
    f.close()
    for count, i in enumerate(curr_input):
        prompt = prompt.replace(f"!<INPUT {count}>!", i)
    if "<commentblockmarker>###</commentblockmarker>" in prompt:
        prompt = prompt.split("<commentblockmarker>###</commentblockmarker>")[1]
    return prompt.strip()


def safe_generate_response(prompt,
                           gpt_parameter,
                           repeat=5,
                           fail_safe_response="error",
                           func_validate=None,
                           func_clean_up=None,
                           verbose=False):
    if verbose:
        print(prompt)

    for i in range(repeat):
        curr_gpt_response = GPT_request(prompt, gpt_parameter)
        if func_validate(curr_gpt_response, prompt=prompt):
            return func_clean_up(curr_gpt_response, prompt=prompt)
        if verbose:
            print("---- repeat count: ", i, curr_gpt_response)
            print(curr_gpt_response)
            print("~~~~")
    return fail_safe_response


def get_embedding(text, model=None):
    """
    Get embeddings for text using either OpenAI or Ollama
    """
    text = text.replace("\n", " ")
    if not text:
        text = "this is blank"

    if USE_OLLAMA:
        try:
            # Use Ollama for embeddings
            response = requests.post(
                f"{OLLAMA_BASE_URL}/api/embeddings",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": text
                }
            )

            if response.status_code == 200:
                return response.json().get('embedding', [])
            else:
                print(f"Ollama Embedding Error: {response.status_code}")
                # Return a simple random embedding as fallback
                return list(np.random.normal(0, 1, 1536))
        except Exception as e:
            print(f"Ollama Embedding Error: {str(e)}")
            # Return a simple random embedding as fallback
            return list(np.random.normal(0, 1, 1536))
    else:
        # Use OpenAI for embeddings
        return openai.Embedding.create(
                input=[text], model=model or "text-embedding-ada-002")['data'][0]['embedding']


if __name__ == '__main__':
    gpt_parameter = {"model": "gpt-4o-mini", "max_tokens": 50,
                     "temperature": 0, "top_p": 1, "stream": False,
                     "frequency_penalty": 0, "presence_penalty": 0}
    curr_input = ["driving to a friend's house"]
    prompt_lib_file = "prompt_template/test_prompt_July5.txt"
    prompt = generate_prompt(curr_input, prompt_lib_file)

    def __func_validate(gpt_response):
        if len(gpt_response.strip()) <= 1:
            return False
        if len(gpt_response.strip().split(" ")) > 1:
            return False
        return True

    def __func_clean_up(gpt_response, prompt=""):
        try:
            print("TOODOOOOOO")
            print(gpt_response)
            print("-==- -==- -==- ")

            temp = [i.strip() for i in gpt_response.split("\n") if i.strip()]
            _cr = []
            cr = []

            # More robust parsing
            for count, line in enumerate(temp):
                if not line: continue
                if ') ' not in line: continue

                # Extract the task description and duration
                try:
                    task_part = line.split(') ', 1)[1]  # Get everything after the number
                    if '(duration in minutes:' not in task_part:
                        continue

                    task, duration_part = task_part.split('(duration in minutes:', 1)
                    task = task.strip()
                    if task.endswith('.'):
                        task = task[:-1]

                    # Extract duration
                    duration = int(duration_part.split(',')[0].strip())
                    _cr.append(task)
                    cr.append([task, duration])
                except (IndexError, ValueError):
                    continue

            if not cr:  # If parsing failed, return a default
                return [["waiting", duration]]

            total_expected_min = int(prompt.split("(total duration in minutes")[-1]
                                       .split("):")[0].strip())

            # Adjust durations to match expected total
            curr_min_slot = [["dummy", -1],]  # (task_name, task_index)
            for count, i in enumerate(cr):
                i_task = i[0]
                i_duration = i[1]

                i_duration -= (i_duration % 5)
                if i_duration > 0:
                    for j in range(i_duration):
                        curr_min_slot += [(i_task, count)]
            curr_min_slot = curr_min_slot[1:]

            if len(curr_min_slot) > total_expected_min:
                last_task = curr_min_slot[total_expected_min-1]
                curr_min_slot = curr_min_slot[:total_expected_min]
            elif len(curr_min_slot) < total_expected_min:
                last_task = curr_min_slot[-1] if curr_min_slot else ("waiting", 0)
                curr_min_slot.extend([last_task] * (total_expected_min - len(curr_min_slot)))

            cr_ret = [["dummy", -1],]
            for task, task_index in curr_min_slot:
                if not cr_ret[-1][0] == task:
                    cr_ret += [[task, 1]]
                else:
                    cr_ret[-1][1] += 1
            cr = cr_ret[1:]

            return cr
        except Exception as e:
            print(f"Error in task decomposition: {str(e)}")
            return [["waiting", duration]]  # Return a safe default

    output = safe_generate_response(prompt,
                                     gpt_parameter,
                                     5,
                                     "rest",
                                     __func_validate,
                                     __func_clean_up,
                                     True)

    print(output)
