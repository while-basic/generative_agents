"""
Author: Joon Sung Park (joonspk@stanford.edu)

File: run_gpt_prompt.py
Description: Defines all run gpt prompt functions. These functions directly
interface with the safe_generate_response function.
"""
import re
import datetime
import sys
import ast
import json

sys.path.append('../../')

from global_methods import *
from persona.prompt_template.gpt_structure import *
from persona.prompt_template.print_prompt import *

def get_random_alphanumeric(i=6, j=6):
  """
  Returns a random alpha numeric strength that has the length of somewhere
  between i and j.

  INPUT:
    i: min_range for the length
    j: max_range for the length
  OUTPUT:
    an alpha numeric str with the length of somewhere between i and j.
  """
  k = random.randint(i, j)
  x = ''.join(random.choices(string.ascii_letters + string.digits, k=k))
  return x


##############################################################################
# CHAPTER 1: Run GPT Prompt
##############################################################################

def run_gpt_prompt_wake_up_hour(persona, test_input=None, verbose=False):
  """
  Given the persona, returns an integer that indicates the hour when the
  persona wakes up.

  INPUT:
    persona: The Persona class instance
  OUTPUT:
    integer for the wake up hour.
  """
  def create_prompt_input(persona, test_input=None):
    if test_input: return test_input
    prompt_input = [persona.scratch.get_str_iss(),
                    persona.scratch.get_str_lifestyle(),
                    persona.scratch.get_str_firstname()]
    return prompt_input

  def __func_clean_up(gpt_response, prompt=""):
    cr = int(gpt_response.strip().lower().split("am")[0])
    return cr

  def __func_validate(gpt_response, prompt=""):
    try: __func_clean_up(gpt_response, prompt="")
    except: return False
    return True

  def get_fail_safe():
    fs = 8
    return fs

  gpt_param = {"model": "gpt-4o-mini", "max_tokens": 5,
             "temperature": 0.8, "top_p": 1, "stream": False,
             "frequency_penalty": 0, "presence_penalty": 0, "stop": ["\n"]}
  prompt_template = "persona/prompt_template/v2/wake_up_hour_v1.txt"
  prompt_input = create_prompt_input(persona, test_input)
  prompt = generate_prompt(prompt_input, prompt_template)
  fail_safe = get_fail_safe()

  output = safe_generate_response(prompt, gpt_param, 5, fail_safe,
                                   __func_validate, __func_clean_up)

  if debug or verbose:
    print_run_prompts(prompt_template, persona, gpt_param,
                      prompt_input, prompt, output)

  return output, [output, prompt, gpt_param, prompt_input, fail_safe]


def run_gpt_prompt_daily_plan(persona,
                              wake_up_hour,
                              test_input=None,
                              verbose=False):
  """
  Basically the long term planning that spans a day. Returns a list of actions
  that the persona will take today. Usually comes in the following form:
  'wake up and complete the morning routine at 6:00 am',
  'eat breakfast at 7:00 am',..
  Note that the actions come without a period.

  INPUT:
    persona: The Persona class instance
  OUTPUT:
    a list of daily actions in broad strokes.
  """
  def create_prompt_input(persona, wake_up_hour, test_input=None):
    if test_input: return test_input
    prompt_input = []
    prompt_input += [persona.scratch.get_str_iss()]
    prompt_input += [persona.scratch.get_str_lifestyle()]
    prompt_input += [persona.scratch.get_str_curr_date_str()]
    prompt_input += [persona.scratch.get_str_firstname()]
    prompt_input += [f"{str(wake_up_hour)}:00 am"]
    return prompt_input

  def __func_clean_up(gpt_response, prompt=""):
    cr = []
    _cr = gpt_response.split(")")
    for i in _cr:
      if i[-1].isdigit():
        i = i[:-1].strip()
        if i[-1] == "." or i[-1] == ",":
          cr += [i[:-1].strip()]
    return cr

  def __func_validate(gpt_response, prompt=""):
    try: __func_clean_up(gpt_response, prompt="")
    except:
      return False
    return True

  def get_fail_safe():
    fs = ['wake up and complete the morning routine at 6:00 am',
          'eat breakfast at 7:00 am',
          'read a book from 8:00 am to 12:00 pm',
          'have lunch at 12:00 pm',
          'take a nap from 1:00 pm to 4:00 pm',
          'relax and watch TV from 7:00 pm to 8:00 pm',
          'go to bed at 11:00 pm']
    return fs



  gpt_param = {"model": "gpt-4o-mini", "max_tokens": 500,
               "temperature": 0.7, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  prompt_template = "persona/prompt_template/v2/daily_planning_v6.txt"
  prompt_input = create_prompt_input(persona, wake_up_hour, test_input)
  prompt = generate_prompt(prompt_input, prompt_template)
  fail_safe = get_fail_safe()

  output = safe_generate_response(prompt, gpt_param, 5, fail_safe,
                                   __func_validate, __func_clean_up)
  output = ([f"wake up and complete the morning routine at {wake_up_hour}:00 am"]
              + output)

  if debug or verbose:
    print_run_prompts(prompt_template, persona, gpt_param,
                      prompt_input, prompt, output)

  return output, [output, prompt, gpt_param, prompt_input, fail_safe]


def run_gpt_prompt_generate_hourly_schedule(persona,
                                            curr_hour_str,
                                            p_f_ds_hourly_org,
                                            hour_str,
                                            intermission2=None,
                                            test_input=None,
                                            verbose=False):
  def create_prompt_input(persona,
                          curr_hour_str,
                          p_f_ds_hourly_org,
                          hour_str,
                          intermission2=None,
                          test_input=None):
    if test_input: return test_input
    schedule_format = ""
    for i in hour_str:
      schedule_format += f"[{persona.scratch.get_str_curr_date_str()} -- {i}]"
      schedule_format += f" Activity: [Fill in]\n"
    schedule_format = schedule_format[:-1]

    intermission_str = f"Here the originally intended hourly breakdown of"
    intermission_str += f" {persona.scratch.get_str_firstname()}'s schedule today: "
    for count, i in enumerate(persona.scratch.daily_req):
      intermission_str += f"{str(count+1)}) {i}, "
    intermission_str = intermission_str[:-2]

    prior_schedule = ""
    if p_f_ds_hourly_org:
      prior_schedule = "\n"
      for count, i in enumerate(p_f_ds_hourly_org):
        prior_schedule += f"[(ID:{get_random_alphanumeric()})"
        prior_schedule += f" {persona.scratch.get_str_curr_date_str()} --"
        prior_schedule += f" {hour_str[count]}] Activity:"
        prior_schedule += f" {persona.scratch.get_str_firstname()}"
        prior_schedule += f" is {i}\n"

    prompt_ending = f"[(ID:{get_random_alphanumeric()})"
    prompt_ending += f" {persona.scratch.get_str_curr_date_str()}"
    prompt_ending += f" -- {curr_hour_str}] Activity:"
    prompt_ending += f" {persona.scratch.get_str_firstname()} is"

    if intermission2:
      intermission2 = f"\n{intermission2}"

    prompt_input = []
    prompt_input += [schedule_format]
    prompt_input += [persona.scratch.get_str_iss()]

    prompt_input += [prior_schedule + "\n"]
    prompt_input += [intermission_str]
    if intermission2:
      prompt_input += [intermission2]
    else:
      prompt_input += [""]
    prompt_input += [prompt_ending]

    return prompt_input

  def __func_clean_up(gpt_response, prompt=""):
    cr = gpt_response.strip()
    if cr[-1] == ".":
      cr = cr[:-1]
    return cr

  def __func_validate(gpt_response, prompt=""):
    try: __func_clean_up(gpt_response, prompt="")
    except: return False
    return True

  def get_fail_safe():
    fs = "asleep"
    return fs

  gpt_param = {"model": "gpt-4o-mini", "max_tokens": 50,
               "temperature": 0.2, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  prompt_template = "persona/prompt_template/v2/generate_hourly_schedule_v2.txt"
  prompt_input = create_prompt_input(persona,
                                     curr_hour_str,
                                     p_f_ds_hourly_org,
                                     hour_str,
                                     intermission2,
                                     test_input)
  prompt = generate_prompt(prompt_input, prompt_template)
  fail_safe = get_fail_safe()

  output = safe_generate_response(prompt, gpt_param, 5, fail_safe,
                                   __func_validate, __func_clean_up)

  if debug or verbose:
    print_run_prompts(prompt_template, persona, gpt_param,
                      prompt_input, prompt, output)

  return output, [output, prompt, gpt_param, prompt_input, fail_safe]








def run_gpt_prompt_task_decomp(persona,
                               task,
                               duration,
                               test_input=None,
                               verbose=False):
  def create_prompt_input(persona, task, duration, test_input=None):

    """
    Today is Saturday June 25. From 00:00 ~ 06:00am, Maeve is
    planning on sleeping, 06:00 ~ 07:00am, Maeve is
    planning on waking up and doing her morning routine,
    and from 07:00am ~08:00am, Maeve is planning on having breakfast.
    """

    curr_f_org_index = persona.scratch.get_f_daily_schedule_hourly_org_index()
    all_indices = []
    # if curr_f_org_index > 0:
    #   all_indices += [curr_f_org_index-1]
    all_indices += [curr_f_org_index]
    if curr_f_org_index+1 <= len(persona.scratch.f_daily_schedule_hourly_org):
      all_indices += [curr_f_org_index+1]
    if curr_f_org_index+2 <= len(persona.scratch.f_daily_schedule_hourly_org):
      all_indices += [curr_f_org_index+2]

    curr_time_range = ""

    print ("DEBUG")
    print (persona.scratch.f_daily_schedule_hourly_org)
    print (all_indices)

    summ_str = f'Today is {persona.scratch.curr_time.strftime("%B %d, %Y")}. '
    summ_str += f'From '
    for_time = persona.scratch.curr_time
    for index in all_indices:
      print ("index", index)
      if index < len(persona.scratch.f_daily_schedule_hourly_org):
        start_min = 0
        for i in range(index):
          start_min += persona.scratch.f_daily_schedule_hourly_org[i][1]
        end_min = start_min + persona.scratch.f_daily_schedule_hourly_org[index][1]
        start_time = (datetime.datetime.strptime("00:00:00", "%H:%M:%S")
                      + datetime.timedelta(minutes=start_min))
        end_time = (datetime.datetime.strptime("00:00:00", "%H:%M:%S")
                      + datetime.timedelta(minutes=end_min))
        start_time_str = start_time.strftime("%H:%M%p")
        end_time_str = end_time.strftime("%H:%M%p")
        summ_str += f"{start_time_str} ~ {end_time_str}, {persona.name} is planning on {persona.scratch.f_daily_schedule_hourly_org[index][0]}, "
        if curr_f_org_index+1 == index:
          curr_time_range = f'{start_time_str} ~ {end_time_str}'
    summ_str = summ_str[:-2] + "."

    prompt_input = []
    prompt_input += [persona.scratch.get_str_iss()]
    prompt_input += [summ_str]
    # prompt_input += [persona.scratch.get_str_curr_date_str()]
    prompt_input += [persona.scratch.get_str_firstname()]
    prompt_input += [persona.scratch.get_str_firstname()]
    prompt_input += [task]
    prompt_input += [curr_time_range]
    prompt_input += [duration]
    prompt_input += [persona.scratch.get_str_firstname()]
    return prompt_input

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
      # Get duration from prompt if possible
      try:
        duration = int(prompt.split("(total duration in minutes")[-1].split("):")[0].strip())
      except:
        duration = 60  # fallback duration
      return [["waiting", duration]]  # Return a safe default

  def __func_validate(gpt_response, prompt=""):
    # TODO -- this sometimes generates error
    try:
      __func_clean_up(gpt_response)
    except:
      pass
      # return False
    return gpt_response

  def get_fail_safe():
    fs = ["asleep"]
    return fs

  gpt_param = {"model": "gpt-4o-mini", "max_tokens": 1000,
             "temperature": 0, "top_p": 1, "stream": False,
             "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  prompt_template = "persona/prompt_template/v2/task_decomp_v3.txt"
  prompt_input = create_prompt_input(persona, task, duration)
  prompt = generate_prompt(prompt_input, prompt_template)
  fail_safe = get_fail_safe()

  print ("?????")
  print (prompt)
  output = safe_generate_response(prompt, gpt_param, 5, get_fail_safe(),
                                   __func_validate, __func_clean_up)

  # TODO THERE WAS A BUG HERE...
  # This is for preventing overflows...
  """
  File "/Users/joonsungpark/Desktop/Stanford/Projects/
  generative-personas/src_exploration/reverie_simulation/
  brain/get_next_action_v3.py", line 364, in run_gpt_prompt_task_decomp
  fin_output[-1][1] += (duration - ftime_sum)
  IndexError: list index out of range
  """

  print ("IMPORTANT VVV DEBUG")

  # print (prompt_input)
  # print (prompt)
  print (output)

  fin_output = []
  time_sum = 0
  for i_task, i_duration in output:
    time_sum += i_duration
    # HM?????????
    # if time_sum < duration:
    if time_sum <= duration:
      fin_output += [[i_task, i_duration]]
    else:
      break
  ftime_sum = 0
  for fi_task, fi_duration in fin_output:
    ftime_sum += fi_duration

  # print ("for debugging... line 365", fin_output)
  fin_output[-1][1] += (duration - ftime_sum)
  output = fin_output



  task_decomp = output
  ret = []
  for decomp_task, duration in task_decomp:
    ret += [[f"{task} ({decomp_task})", duration]]
  output = ret


  if debug or verbose:
    print_run_prompts(prompt_template, persona, gpt_param,
                      prompt_input, prompt, output)

  return output, [output, prompt, gpt_param, prompt_input, fail_safe]



def run_gpt_prompt_action_sector(action_description,
                                persona,
                                maze,
                                test_input=None,
                                verbose=False):
  def create_prompt_input(action_description, persona, maze, test_input=None):
    act_world = f"{maze.access_tile(persona.scratch.curr_tile)['world']}"

    prompt_input = []

    prompt_input += [persona.scratch.get_str_name()]
    prompt_input += [maze.access_tile(persona.scratch.curr_tile)["arena"]]
    prompt_input += [maze.access_tile(persona.scratch.curr_tile)["sector"]]
    x = f"{act_world}:{persona.scratch.living_area.split(':')[1]}"
    prompt_input += [persona.s_mem.get_str_accessible_sector_arenas(x)]


    prompt_input += [persona.scratch.get_str_name()]
    prompt_input += [f"{maze.access_tile(persona.scratch.curr_tile)['sector']}"]
    x = f"{act_world}:{maze.access_tile(persona.scratch.curr_tile)['sector']}"
    prompt_input += [persona.s_mem.get_str_accessible_sector_arenas(x)]

    if persona.scratch.get_str_daily_plan_req() != "":
      prompt_input += [f"\n{persona.scratch.get_str_daily_plan_req()}"]
    else:
      prompt_input += [""]


    # MAR 11 TEMP
    accessible_sector_str = persona.s_mem.get_str_accessible_sectors(act_world)
    curr = accessible_sector_str.split(", ")
    fin_accessible_sectors = []
    for i in curr:
      if "'s house" in i:
        if persona.scratch.last_name in i:
          fin_accessible_sectors += [i]
      else:
        fin_accessible_sectors += [i]
    accessible_sector_str = ", ".join(fin_accessible_sectors)
    # END MAR 11 TEMP

    prompt_input += [accessible_sector_str]



    action_description_1 = action_description
    action_description_2 = action_description
    if "(" in action_description:
      action_description_1 = action_description.split("(")[0].strip()
      action_description_2 = action_description.split("(")[-1][:-1]
    prompt_input += [persona.scratch.get_str_name()]
    prompt_input += [action_description_1]

    prompt_input += [action_description_2]
    prompt_input += [persona.scratch.get_str_name()]
    return prompt_input







  def __func_clean_up(gpt_response, prompt=""):
    cleaned_response = gpt_response.split("}")[0]
    return cleaned_response

  def __func_validate(gpt_response, prompt=""):
    if len(gpt_response.strip()) < 1:
      return False
    if "}" not in gpt_response:
      return False
    if "," in gpt_response:
      return False
    return True

  def get_fail_safe():
    fs = ("kitchen")
    return fs


  # # ChatGPT Plugin ===========================================================
  # def __chat_func_clean_up(gpt_response, prompt=""): ############
  #   cr = gpt_response.strip()
  #   return cr

  # def __chat_func_validate(gpt_response, prompt=""): ############
  #   try:
  #     gpt_response = __func_clean_up(gpt_response, prompt="")
  #   except: return False
  #   return True

  # print ("asdhfapsh8p9hfaiafdsi;ldfj as DEBUG 20") ########
  # gpt_param = {"engine": "text-davinci-002", "max_tokens": 15,
  #              "temperature": 0, "top_p": 1, "stream": False,
  #              "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  # prompt_template = "persona/prompt_template/v3_ChatGPT/action_location_sector_v2.txt" ########
  # prompt_input = create_prompt_input(action_description, persona, maze)  ########
  # prompt = generate_prompt(prompt_input, prompt_template)
  # example_output = "Johnson Park" ########
  # special_instruction = "The value for the output must contain one of the area options above verbatim (including lower/upper case)." ########
  # fail_safe = get_fail_safe() ########
  # output = ChatGPT_safe_generate_response(prompt, example_output, special_instruction, 3, fail_safe,
  #                                         __chat_func_validate, __chat_func_clean_up, True)
  # if output != False:
  #   return output, [output, prompt, gpt_param, prompt_input, fail_safe]
  # # ChatGPT Plugin ===========================================================





  gpt_param = {"model": "gpt-4o-mini", "max_tokens": 15,
               "temperature": 0.4, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  prompt_template = "persona/prompt_template/v1/action_location_sector_v1.txt"
  prompt_input = create_prompt_input(action_description, persona, maze)
  prompt = generate_prompt(prompt_input, prompt_template)

  fail_safe = get_fail_safe()
  output = safe_generate_response(prompt, gpt_param, 5, fail_safe,
                                   __func_validate, __func_clean_up)

  y = f"{maze.access_tile(persona.scratch.curr_tile)['world']}"
  x = [i.strip() for i in persona.s_mem.get_str_accessible_sectors(y).split(",")]
  if output not in x:
    # output = random.choice(x)
    output = persona.scratch.living_area.split(":")[1]

  print ("DEBUG", random.choice(x), "------", output)

  if debug or verbose:
    print_run_prompts(prompt_template, persona, gpt_param,
                      prompt_input, prompt, output)

  return output, [output, prompt, gpt_param, prompt_input, fail_safe]



def run_gpt_prompt_action_arena(action_description,
                                persona,
                                maze, act_world, act_sector,
                                test_input=None,
                                verbose=False):
  def create_prompt_input(action_description, persona, maze, act_world, act_sector, test_input=None):
    prompt_input = []
    # prompt_input += [persona.scratch.get_str_name()]
    # prompt_input += [maze.access_tile(persona.scratch.curr_tile)["arena"]]
    # prompt_input += [maze.access_tile(persona.scratch.curr_tile)["sector"]]
    prompt_input += [persona.scratch.get_str_name()]
    x = f"{act_world}:{act_sector}"
    prompt_input += [act_sector]

    # MAR 11 TEMP
    accessible_arena_str = persona.s_mem.get_str_accessible_sector_arenas(x)
    curr = accessible_arena_str.split(", ")
    fin_accessible_arenas = []
    for i in curr:
      if "'s room" in i:
        if persona.scratch.last_name in i:
          fin_accessible_arenas += [i]
      else:
        fin_accessible_arenas += [i]
    accessible_arena_str = ", ".join(fin_accessible_arenas)
    # END MAR 11 TEMP


    prompt_input += [accessible_arena_str]


    action_description_1 = action_description
    action_description_2 = action_description
    if "(" in action_description:
      action_description_1 = action_description.split("(")[0].strip()
      action_description_2 = action_description.split("(")[-1][:-1]
    prompt_input += [persona.scratch.get_str_name()]
    prompt_input += [action_description_1]

    prompt_input += [action_description_2]
    prompt_input += [persona.scratch.get_str_name()]



    prompt_input += [act_sector]

    prompt_input += [accessible_arena_str]
    # prompt_input += [maze.access_tile(persona.scratch.curr_tile)["arena"]]
    # x = f"{maze.access_tile(persona.scratch.curr_tile)['world']}:{maze.access_tile(persona.scratch.curr_tile)['sector']}:{maze.access_tile(persona.scratch.curr_tile)['arena']}"
    # prompt_input += [persona.s_mem.get_str_accessible_arena_game_objects(x)]


    return prompt_input

  def __func_clean_up(gpt_response, prompt=""):
    cleaned_response = gpt_response.split("}")[0]
    return cleaned_response

  def __func_validate(gpt_response, prompt=""):
    if len(gpt_response.strip()) < 1:
      return False
    if "}" not in gpt_response:
      return False
    if "," in gpt_response:
      return False
    return True

  def get_fail_safe():
    fs = ("kitchen")
    return fs

  gpt_param = {"model": "gpt-4o-mini", "max_tokens": 15,
               "temperature": 0.4, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  prompt_template = "persona/prompt_template/v1/action_location_object_vMar11.txt"
  prompt_input = create_prompt_input(action_description, persona, maze, act_world, act_sector)
  prompt = generate_prompt(prompt_input, prompt_template)

  fail_safe = get_fail_safe()
  output = safe_generate_response(prompt, gpt_param, 5, fail_safe,
                                   __func_validate, __func_clean_up)
  print (output)
  # y = f"{act_world}:{act_sector}"
  # x = [i.strip() for i in persona.s_mem.get_str_accessible_sector_arenas(y).split(",")]
  # if output not in x:
  #   output = random.choice(x)

  if debug or verbose:
    print_run_prompts(prompt_template, persona, gpt_param,
                      prompt_input, prompt, output)

  return output, [output, prompt, gpt_param, prompt_input, fail_safe]



def run_gpt_prompt_action_game_object(action_description,
                                      persona,
                                      maze,
                                      temp_address,
                                      test_input=None,
                                      verbose=False):
  def create_prompt_input(action_description,
                          persona,
                          temp_address,
                          test_input=None):
    prompt_input = []
    if "(" in action_description:
      action_description = action_description.split("(")[-1][:-1]

    prompt_input += [action_description]
    prompt_input += [persona
                     .s_mem.get_str_accessible_arena_game_objects(temp_address)]
    return prompt_input

  def __func_validate(gpt_response, prompt=""):
    if len(gpt_response.strip()) < 1:
      return False
    return True

  def __func_clean_up(gpt_response, prompt=""):
    cleaned_response = gpt_response.strip()
    return cleaned_response

  def get_fail_safe():
    fs = ("bed")
    return fs

  gpt_param = {"model": "gpt-4o-mini", "max_tokens": 15,
               "temperature": 0.4, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  prompt_template = "persona/prompt_template/v1/action_object_v2.txt"
  prompt_input = create_prompt_input(action_description,
                                     persona,
                                     temp_address,
                                     test_input)
  prompt = generate_prompt(prompt_input, prompt_template)

  fail_safe = get_fail_safe()
  output = safe_generate_response(prompt, gpt_param, 5, fail_safe,
                                   __func_validate, __func_clean_up)

  x = [i.strip() for i in persona.s_mem.get_str_accessible_arena_game_objects(temp_address).split(",")]
  if output not in x:
    output = random.choice(x)

  if debug or verbose:
    print_run_prompts(prompt_template, persona, gpt_param,
                      prompt_input, prompt, output)

  return output, [output, prompt, gpt_param, prompt_input, fail_safe]




def run_gpt_prompt_pronunciatio(action_description, persona, verbose=False):
  def create_prompt_input(action_description):
    if "(" in action_description:
      action_description = action_description.split("(")[-1].split(")")[0]
    prompt_input = [action_description]
    return prompt_input

  def __func_clean_up(gpt_response, prompt=""):
    cr = gpt_response.strip()
    if len(cr) > 3:
      cr = cr[:3]
    return cr

  def __func_validate(gpt_response, prompt=""):
    try:
      __func_clean_up(gpt_response, prompt="")
      if len(gpt_response) == 0:
        return False
    except: return False
    return True

  def get_fail_safe():
    fs = "😋"
    return fs


  # ChatGPT Plugin ===========================================================
  def __chat_func_clean_up(gpt_response, prompt=""): ############
    cr = gpt_response.strip()
    if len(cr) > 3:
      cr = cr[:3]
    return cr

  def __chat_func_validate(gpt_response, prompt=""): ############
    try:
      __func_clean_up(gpt_response, prompt="")
      if len(gpt_response) == 0:
        return False
    except: return False
    return True
    return True

  print ("asdhfapsh8p9hfaiafdsi;ldfj as DEBUG 4") ########
  gpt_param = {"model": "gpt-4o-mini", "max_tokens": 15,
               "temperature": 0.2, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  prompt_template = "persona/prompt_template/v3_ChatGPT/generate_pronunciatio_v1.txt" ########
  prompt_input = create_prompt_input(action_description)  ########
  prompt = generate_prompt(prompt_input, prompt_template)
  example_output = "🛁🧖‍♀️" ########
  special_instruction = "The output must ONLY contain the emojis." ########
  fail_safe = get_fail_safe() ########
  output = ChatGPT_safe_generate_response(prompt, example_output, special_instruction, 3, fail_safe,
                                          __chat_func_validate, __chat_func_clean_up, True)
  if output != False:
    return output, [output, prompt, gpt_param, prompt_input, fail_safe]
  # ChatGPT Plugin ===========================================================





  # gpt_param = {"engine": "text-davinci-003", "max_tokens": 15,
  #              "temperature": 0, "top_p": 1, "stream": False,
  #              "frequency_penalty": 0, "presence_penalty": 0, "stop": ["\n"]}
  # prompt_template = "persona/prompt_template/v2/generate_pronunciatio_v1.txt"
  # prompt_input = create_prompt_input(action_description)

  # prompt = generate_prompt(prompt_input, prompt_template)

  # fail_safe = get_fail_safe()
  # output = safe_generate_response(prompt, gpt_param, 5, fail_safe,
  #                                  __func_validate, __func_clean_up)

  # if debug or verbose:
  #   print_run_prompts(prompt_template, persona, gpt_param,
  #                     prompt_input, prompt, output)

  # return output, [output, prompt, gpt_param, prompt_input, fail_safe]












def run_gpt_prompt_event_triple(action_description, persona, verbose=False):
  def create_prompt_input(action_description, persona):
    if "(" in action_description:
      action_description = action_description.split("(")[-1].split(")")[0]
    prompt_input = [persona.name,
                    action_description,
                    persona.name]
    return prompt_input

  def __func_clean_up(gpt_response, prompt=""):
    cr = gpt_response.strip()
    cr = [i.strip() for i in cr.split(")")[0].split(",")]
    return cr

  def __func_validate(gpt_response, prompt=""):
    try:
      gpt_response = __func_clean_up(gpt_response, prompt="")
      if len(gpt_response) != 2:
        return False
    except: return False
    return True

  def get_fail_safe(persona):
    fs = (persona.name, "is", "idle")
    return fs


  # ChatGPT Plugin ===========================================================
  # def __chat_func_clean_up(gpt_response, prompt=""): ############
  #   cr = gpt_response.strip()
  #   cr = [i.strip() for i in cr.split(")")[0].split(",")]
  #   return cr

  # def __chat_func_validate(gpt_response, prompt=""): ############
  #   try:
  #     gpt_response = __func_clean_up(gpt_response, prompt="")
  #     if len(gpt_response) != 2:
  #       return False
  #   except: return False
  #   return True

  # print ("asdhfapsh8p9hfaiafdsi;ldfj as DEBUG 5") ########
  # gpt_param = {"engine": "text-davinci-002", "max_tokens": 15,
  #              "temperature": 0, "top_p": 1, "stream": False,
  #              "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  # prompt_template = "persona/prompt_template/v3_ChatGPT/generate_event_triple_v1.txt" ########
  # prompt_input = create_prompt_input(action_description, persona)  ########
  # prompt = generate_prompt(prompt_input, prompt_template)
  # example_output = "(Jane Doe, cooking, breakfast)" ########
  # special_instruction = "The value for the output must ONLY contain the triple. If there is an incomplete element, just say 'None' but there needs to be three elements no matter what." ########
  # fail_safe = get_fail_safe(persona) ########
  # output = ChatGPT_safe_generate_response(prompt, example_output, special_instruction, 3, fail_safe,
  #                                         __chat_func_validate, __chat_func_clean_up, True)
  # if output != False:
  #   return output, [output, prompt, gpt_param, prompt_input, fail_safe]
  # ChatGPT Plugin ===========================================================




  gpt_param = {"model": "gpt-4o-mini", "max_tokens": 30,
               "temperature": 0.4, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": ["\n"]}
  prompt_template = "persona/prompt_template/v2/generate_event_triple_v1.txt"
  prompt_input = create_prompt_input(action_description, persona)
  prompt = generate_prompt(prompt_input, prompt_template)
  fail_safe = get_fail_safe(persona) ########
  output = safe_generate_response(prompt, gpt_param, 5, fail_safe,
                                   __func_validate, __func_clean_up)
  output = (persona.name, output[0], output[1])

  if debug or verbose:
    print_run_prompts(prompt_template, persona, gpt_param,
                      prompt_input, prompt, output)

  return output, [output, prompt, gpt_param, prompt_input, fail_safe]













def run_gpt_prompt_act_obj_desc(act_game_object, act_desp, persona, verbose=False):
  def create_prompt_input(act_game_object, act_desp, persona):
    prompt_input = [act_game_object,
                    persona.name,
                    act_desp,
                    act_game_object,
                    act_game_object]
    return prompt_input

  def __func_clean_up(gpt_response, prompt=""):
    cr = gpt_response.strip()
    if cr[-1] == ".": cr = cr[:-1]
    return cr

  def __func_validate(gpt_response, prompt=""):
    try:
      gpt_response = __func_clean_up(gpt_response, prompt="")
    except:
      return False
    return True

  def get_fail_safe(act_game_object):
    fs = f"{act_game_object} is idle"
    return fs

  # ChatGPT Plugin ===========================================================
  def __chat_func_clean_up(gpt_response, prompt=""): ############
    cr = gpt_response.strip()
    if cr[-1] == ".": cr = cr[:-1]
    return cr

  def __chat_func_validate(gpt_response, prompt=""): ############
    try:
      gpt_response = __func_clean_up(gpt_response, prompt="")
    except:
      return False
    return True

  print ("asdhfapsh8p9hfaiafdsi;ldfj as DEBUG 6") ########
  gpt_param = {"model": "gpt-4o-mini", "max_tokens": 15,
               "temperature": 0.2, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  prompt_template = "persona/prompt_template/v3_ChatGPT/generate_obj_event_v1.txt" ########
  prompt_input = create_prompt_input(act_game_object, act_desp, persona)  ########
  prompt = generate_prompt(prompt_input, prompt_template)
  example_output = "being fixed" ########
  special_instruction = "The output should ONLY contain the phrase that should go in <fill in>." ########
  fail_safe = get_fail_safe(act_game_object) ########
  output = ChatGPT_safe_generate_response(prompt, example_output, special_instruction, 3, fail_safe,
                                          __chat_func_validate, __chat_func_clean_up, True)
  if output != False:
    return output, [output, prompt, gpt_param, prompt_input, fail_safe]
  # ChatGPT Plugin ===========================================================



  # gpt_param = {"engine": "text-davinci-003", "max_tokens": 30,
  #              "temperature": 0, "top_p": 1, "stream": False,
  #              "frequency_penalty": 0, "presence_penalty": 0, "stop": ["\n"]}
  # prompt_template = "persona/prompt_template/v2/generate_obj_event_v1.txt"
  # prompt_input = create_prompt_input(act_game_object, act_desp, persona)
  # prompt = generate_prompt(prompt_input, prompt_template)
  # fail_safe = get_fail_safe(act_game_object)
  # output = safe_generate_response(prompt, gpt_param, 5, fail_safe,
  #                                  __func_validate, __func_clean_up)

  # if debug or verbose:
  #   print_run_prompts(prompt_template, persona, gpt_param,
  #                     prompt_input, prompt, output)

  # return output, [output, prompt, gpt_param, prompt_input, fail_safe]









def run_gpt_prompt_act_obj_event_triple(act_game_object, act_obj_desc, persona, verbose=False):
  def create_prompt_input(act_game_object, act_obj_desc):
    prompt_input = [act_game_object,
                    act_obj_desc,
                    act_game_object]
    return prompt_input

  def __func_clean_up(gpt_response, prompt=""):
    cr = gpt_response.strip()
    cr = [i.strip() for i in cr.split(")")[0].split(",")]
    return cr

  def __func_validate(gpt_response, prompt=""):
    try:
      gpt_response = __func_clean_up(gpt_response, prompt="")
      if len(gpt_response) != 2:
        return False
    except: return False
    return True

  def get_fail_safe(act_game_object):
    fs = (act_game_object, "is", "idle")
    return fs

  gpt_param = {"model": "gpt-4o-mini", "max_tokens": 30,
               "temperature": 0.4, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": ["\n"]}
  prompt_template = "persona/prompt_template/v2/generate_event_triple_v1.txt"
  prompt_input = create_prompt_input(act_game_object, act_obj_desc)
  prompt = generate_prompt(prompt_input, prompt_template)
  fail_safe = get_fail_safe(act_game_object)
  output = safe_generate_response(prompt, gpt_param, 5, fail_safe,
                                   __func_validate, __func_clean_up)
  output = (act_game_object, output[0], output[1])

  if debug or verbose:
    print_run_prompts(prompt_template, persona, gpt_param,
                      prompt_input, prompt, output)

  return output, [output, prompt, gpt_param, prompt_input, fail_safe]





def run_gpt_prompt_new_decomp_schedule(persona,
                                       main_act_dur,
                                       truncated_act_dur,
                                       start_time_hour,
                                       end_time_hour,
                                       inserted_act,
                                       inserted_act_dur,
                                       test_input=None,
                                       verbose=False):
  def create_prompt_input(persona,
                           main_act_dur,
                           truncated_act_dur,
                           start_time_hour,
                           end_time_hour,
                           inserted_act,
                           inserted_act_dur,
                           test_input=None):
    persona_name = persona.name
    start_hour_str = start_time_hour.strftime("%H:%M %p")
    end_hour_str = end_time_hour.strftime("%H:%M %p")

    original_plan = ""
    for_time = start_time_hour
    for i in main_act_dur:
      original_plan += f'{for_time.strftime("%H:%M")} ~ {(for_time + datetime.timedelta(minutes=int(i[1]))).strftime("%H:%M")} -- ' + i[0]
      original_plan += "\n"
      for_time += datetime.timedelta(minutes=int(i[1]))

    new_plan_init = ""
    for_time = start_time_hour
    for count, i in enumerate(truncated_act_dur):
      new_plan_init += f'{for_time.strftime("%H:%M")} ~ {(for_time + datetime.timedelta(minutes=int(i[1]))).strftime("%H:%M")} -- ' + i[0]
      new_plan_init += "\n"
      if count < len(truncated_act_dur) - 1:
        for_time += datetime.timedelta(minutes=int(i[1]))

    new_plan_init += (for_time + datetime.timedelta(minutes=int(i[1]))).strftime("%H:%M") + " ~"

    prompt_input = [persona_name,
                    start_hour_str,
                    end_hour_str,
                    original_plan,
                    persona_name,
                    inserted_act,
                    inserted_act_dur,
                    persona_name,
                    start_hour_str,
                    end_hour_str,
                    end_hour_str,
                    new_plan_init]
    return prompt_input

  def __func_clean_up(gpt_response, prompt=""):
    new_schedule = prompt + " " + gpt_response.strip()
    new_schedule = new_schedule.split("The revised schedule:")[-1].strip()
    new_schedule = new_schedule.split("\n")

    ret_temp = []
    for i in new_schedule:
      ret_temp += [i.split(" -- ")]

    ret = []
    for time_str, action in ret_temp:
      start_time = time_str.split(" ~ ")[0].strip()
      end_time = time_str.split(" ~ ")[1].strip()
      delta = datetime.datetime.strptime(end_time, "%H:%M") - datetime.datetime.strptime(start_time, "%H:%M")
      delta_min = int(delta.total_seconds()/60)
      if delta_min < 0: delta_min = 0
      ret += [[action, delta_min]]

    return ret

  def __func_validate(gpt_response, prompt=""):
    try:
      gpt_response = __func_clean_up(gpt_response, prompt)
      dur_sum = 0
      for act, dur in gpt_response:
        dur_sum += dur
        if str(type(act)) != "<class 'str'>":
          return False
        if str(type(dur)) != "<class 'int'>":
          return False
      x = prompt.split("\n")[0].split("originally planned schedule from")[-1].strip()[:-1]
      x = [datetime.datetime.strptime(i.strip(), "%H:%M %p") for i in x.split(" to ")]
      delta_min = int((x[1] - x[0]).total_seconds()/60)

      if int(dur_sum) != int(delta_min):
        return False

    except:
      return False
    return True

  def get_fail_safe(main_act_dur, truncated_act_dur):
    dur_sum = 0
    for act, dur in main_act_dur: dur_sum += dur

    ret = truncated_act_dur[:]
    ret += main_act_dur[len(ret)-1:]

    # If there are access, we need to trim...
    ret_dur_sum = 0
    count = 0
    over = None
    for act, dur in ret:
      ret_dur_sum += dur
      if ret_dur_sum == dur_sum:
        break
      if ret_dur_sum > dur_sum:
        over = ret_dur_sum - dur_sum
        break
      count += 1

    if over:
      ret = ret[:count+1]
      ret[-1][1] -= over

    return ret

  gpt_param = {"model": "gpt-4o-mini", "max_tokens": 1000,
               "temperature": 0.7, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  prompt_template = "persona/prompt_template/v2/new_decomp_schedule_v1.txt"
  prompt_input = create_prompt_input(persona,
                                     main_act_dur,
                                     truncated_act_dur,
                                     start_time_hour,
                                     end_time_hour,
                                     inserted_act,
                                     inserted_act_dur,
                                     test_input)
  prompt = generate_prompt(prompt_input, prompt_template)
  fail_safe = get_fail_safe(main_act_dur, truncated_act_dur)
  output = safe_generate_response(prompt, gpt_param, 5, fail_safe,
                                   __func_validate, __func_clean_up)

  # print ("* * * * output")
  # print (output)
  # print ('* * * * fail_safe')
  # print (fail_safe)



  if debug or verbose:
    print_run_prompts(prompt_template, persona, gpt_param,
                      prompt_input, prompt, output)

  return output, [output, prompt, gpt_param, prompt_input, fail_safe]






def run_gpt_prompt_decide_to_talk(persona, target_persona, retrieved,test_input=None,
                                       verbose=False):
  def create_prompt_input(init_persona, target_persona, retrieved,
                          test_input=None):
    last_chat = init_persona.a_mem.get_last_chat(target_persona.name)
    last_chatted_time = ""
    last_chat_about = ""
    if last_chat:
      last_chatted_time = last_chat.created.strftime("%B %d, %Y, %H:%M:%S")
      last_chat_about = last_chat.description

    context = ""
    for c_node in retrieved["events"]:
      curr_desc = c_node.description.split(" ")
      curr_desc[2:3] = ["was"]
      curr_desc = " ".join(curr_desc)
      context +=  f"{curr_desc}. "
    context += "\n"
    for c_node in retrieved["thoughts"]:
      context +=  f"{c_node.description}. "

    curr_time = init_persona.scratch.curr_time.strftime("%B %d, %Y, %H:%M:%S %p")
    init_act_desc = init_persona.scratch.act_description
    if "(" in init_act_desc:
      init_act_desc = init_act_desc.split("(")[-1][:-1]

    if len(init_persona.scratch.planned_path) == 0 and "waiting" not in init_act_desc:
      init_p_desc = f"{init_persona.name} is already {init_act_desc}"
    elif "waiting" in init_act_desc:
      init_p_desc = f"{init_persona.name} is {init_act_desc}"
    else:
      init_p_desc = f"{init_persona.name} is on the way to {init_act_desc}"

    target_act_desc = target_persona.scratch.act_description
    if "(" in target_act_desc:
      target_act_desc = target_act_desc.split("(")[-1][:-1]

    if len(target_persona.scratch.planned_path) == 0 and "waiting" not in init_act_desc:
      target_p_desc = f"{target_persona.name} is already {target_act_desc}"
    elif "waiting" in init_act_desc:
      target_p_desc = f"{init_persona.name} is {init_act_desc}"
    else:
      target_p_desc = f"{target_persona.name} is on the way to {target_act_desc}"


    prompt_input = []
    prompt_input += [context]

    prompt_input += [curr_time]

    prompt_input += [init_persona.name]
    prompt_input += [target_persona.name]
    prompt_input += [last_chatted_time]
    prompt_input += [last_chat_about]


    prompt_input += [init_p_desc]
    prompt_input += [target_p_desc]
    prompt_input += [init_persona.name]
    prompt_input += [target_persona.name]
    return prompt_input

  def __func_validate(gpt_response, prompt=""):
    try:
      if gpt_response.split("Answer in yes or no:")[-1].strip().lower() in ["yes", "no"]:
        return True
      return False
    except:
      return False

  def __func_clean_up(gpt_response, prompt=""):
    return gpt_response.split("Answer in yes or no:")[-1].strip().lower()

  def get_fail_safe():
    fs = "yes"
    return fs



  gpt_param = {"model": "gpt-4o-mini", "max_tokens": 20,
               "temperature": 0.2, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  prompt_template = "persona/prompt_template/v2/decide_to_talk_v2.txt"
  prompt_input = create_prompt_input(persona, target_persona, retrieved,
                                     test_input)
  prompt = generate_prompt(prompt_input, prompt_template)

  fail_safe = get_fail_safe()
  output = safe_generate_response(prompt, gpt_param, 5, fail_safe,
                                   __func_validate, __func_clean_up)

  if debug or verbose:
    print_run_prompts(prompt_template, persona, gpt_param,
                      prompt_input, prompt, output)

  return output, [output, prompt, gpt_param, prompt_input, fail_safe]


# ... rest of the code remains the same ...


def run_gpt_prompt_event_poignancy(persona, event_description, test_input=None, verbose=False):
  def create_prompt_input(persona, event_description, test_input=None):
    prompt_input = [persona.scratch.name,
                    persona.scratch.get_str_iss(),
                    persona.scratch.name,
                    event_description]
    return prompt_input

  def __func_clean_up(gpt_response, prompt=""):
    gpt_response = int(gpt_response.strip())
    return gpt_response

  def __func_validate(gpt_response, prompt=""):
    try:
      __func_clean_up(gpt_response, prompt="")
      return True
    except:
      return False

  def get_fail_safe():
    return 4

  gpt_param = {"model": "gpt-4o-mini", "max_tokens": 3,
               "temperature": 0.2, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  prompt_template = "persona/prompt_template/v2/poignancy_event_v1.txt"
  prompt_input = create_prompt_input(persona, event_description)
  prompt = generate_prompt(prompt_input, prompt_template)

  fail_safe = get_fail_safe()
  output = safe_generate_response(prompt, gpt_param, 5, fail_safe,
                                   __func_validate, __func_clean_up)

  if debug or verbose:
    print_run_prompts(prompt_template, persona, gpt_param,
                      prompt_input, prompt, output)

  return output, [output, prompt, gpt_param, prompt_input, fail_safe]

def run_gpt_prompt_chat_poignancy(persona, event_description, test_input=None, verbose=False):
  def create_prompt_input(persona, event_description, test_input=None):
    prompt_input = [persona.scratch.name,
                    persona.scratch.get_str_iss(),
                    persona.scratch.name,
                    event_description]
    return prompt_input

  def __func_clean_up(gpt_response, prompt=""):
    gpt_response = int(gpt_response.strip())
    return gpt_response

  def __func_validate(gpt_response, prompt=""):
    try:
      __func_clean_up(gpt_response, prompt="")
      return True
    except:
      return False

  def get_fail_safe():
    return 4

  gpt_param = {"model": "gpt-4o-mini", "max_tokens": 3,
               "temperature": 0.2, "top_p": 1, "stream": False,
               "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
  prompt_template = "persona/prompt_template/v2/poignancy_chat_v1.txt"
  prompt_input = create_prompt_input(persona, event_description)
  prompt = generate_prompt(prompt_input, prompt_template)

  fail_safe = get_fail_safe()
  output = safe_generate_response(prompt, gpt_param, 5, fail_safe,
                                   __func_validate, __func_clean_up)

  if debug or verbose:
    print_run_prompts(prompt_template, persona, gpt_param,
                      prompt_input, prompt, output)

  return output, [output, prompt, gpt_param, prompt_input, fail_safe]


def run_gpt_prompt_memo_on_convo(persona, all_utt, test_input=None, verbose=False):
  """Generate a memo (emoji) based on conversation.

  INPUT:
    persona: The Persona class instance
    all_utt: All utterances in the conversation
  OUTPUT:
    a string of emoji that translates action description.
  EXAMPLE OUTPUT:
    "🧈🍞"
  """
  def create_prompt_input(persona, all_utt, test_input=None):
    prompt_input = {}
    prompt_input["name"] = persona.name
    prompt_input["all_utt"] = all_utt
    return prompt_input

  def __func_validate(response_content):
    return True

  def __func_clean_up(response_content):
    return response_content.strip()

  prompt_input = create_prompt_input(persona, all_utt, test_input)
  prompt = f"""You are {persona.name}. Based on the following conversation, generate 1-3 emojis that summarize the conversation.

Conversation:
{all_utt}

Emojis (1-3 only):"""

  gpt_param = {
    "model": "gpt-4o-mini",
    "max_tokens": 15,
    "temperature": 0.7,
    "top_p": 1,
    "stream": False,
    "frequency_penalty": 0,
    "presence_penalty": 0,
    "stop": None
  }

  fail_safe = "😊"
  output = safe_generate_response(prompt, gpt_param, 5, fail_safe,
                                   __func_validate, __func_clean_up)

  if debug or verbose:
    print(f"Memo Prompt: {prompt}")
    print(f"Memo Output: {output}")

  return output, [output, prompt, gpt_param, prompt_input, fail_safe]


def run_gpt_prompt_event_triple(act_desp, persona, test_input=None, verbose=False):
  """Generate event triple based on action description.

  INPUT:
    act_desp: Action description
    persona: The Persona class instance
  OUTPUT:
    A triple of subject, predicate, object
  """
  def create_prompt_input(act_desp, persona, test_input=None):
    prompt_input = {}
    prompt_input["name"] = persona.name
    prompt_input["action"] = act_desp
    return prompt_input

  def __func_validate(response_content, prompt=""):
    try:
      # Check if the response can be parsed as a triple
      parts = response_content.strip().split(",")
      if len(parts) == 3:
        return True
      return False
    except:
      return False

  def __func_clean_up(response_content, prompt=""):
    try:
      parts = response_content.strip().split(",")
      if len(parts) == 3:
        return [part.strip() for part in parts]
      return [persona.name, "does", act_desp]  # Default fallback
    except:
      return [persona.name, "does", act_desp]  # Default fallback

  prompt_input = create_prompt_input(act_desp, persona, test_input)
  prompt = f"""Convert the following action description into a triple of (subject, predicate, object).

Action: {persona.name} {act_desp}

Provide the triple as three comma-separated values without any additional text or explanation."""

  gpt_param = {
    "model": "gpt-4o-mini",
    "max_tokens": 50,
    "temperature": 0.2,
    "top_p": 1,
    "stream": False,
    "frequency_penalty": 0,
    "presence_penalty": 0,
    "stop": None
  }

  fail_safe = f"{persona.name}, does, {act_desp}"
  output = safe_generate_response(prompt, gpt_param, 5, fail_safe,
                                   __func_validate, __func_clean_up)

  if debug or verbose:
    print(f"Event Triple Prompt: {prompt}")
    print(f"Event Triple Output: {output}")

  return output, [output, prompt, gpt_param, prompt_input, fail_safe]


def run_gpt_prompt_planning_thought_on_convo(persona, all_utt, test_input=None, verbose=False):
  """Generate planning thought based on conversation.

  INPUT:
    persona: The Persona class instance
    all_utt: All utterances in the conversation
  OUTPUT:
    A planning thought
  """
  def create_prompt_input(persona, all_utt, test_input=None):
    prompt_input = {}
    prompt_input["name"] = persona.name
    prompt_input["all_utt"] = all_utt
    return prompt_input

  def __func_validate(response_content):
    return True

  def __func_clean_up(response_content):
    return response_content.strip()

  prompt_input = create_prompt_input(persona, all_utt, test_input)
  prompt = f"""You are {persona.name}. Based on the following conversation, generate a planning thought about what you should do next or how you feel about the conversation.

Conversation:
{all_utt}

Planning thought (1-2 sentences):"""

  gpt_param = {
    "model": "gpt-4o-mini",
    "max_tokens": 100,
    "temperature": 0.7,
    "top_p": 1,
    "stream": False,
    "frequency_penalty": 0,
    "presence_penalty": 0,
    "stop": None
  }

  fail_safe = f"I should think about what was discussed in this conversation."
  output = safe_generate_response(prompt, gpt_param, 5, fail_safe,
                                   __func_validate, __func_clean_up)

  if debug or verbose:
    print(f"Planning Thought Prompt: {prompt}")
    print(f"Planning Thought Output: {output}")

  return output, [output, prompt, gpt_param, prompt_input, fail_safe]


def run_gpt_prompt_insight_and_guidance(persona, statements, n=5, test_input=None, verbose=False):
  """Generate insights and guidance based on recent events and thoughts.

  INPUT:
    persona: The Persona class instance
    statements: Recent events and thoughts as text
    n: Number of insights to generate
  OUTPUT:
    A dictionary mapping insights to evidence
  """
  def create_prompt_input(persona, statements, n, test_input=None):
    prompt_input = {}
    prompt_input["name"] = persona.name
    prompt_input["statements"] = statements
    prompt_input["n"] = n
    return prompt_input

  def __func_validate(response_content):
    try:
      # Check if the response can be parsed as a dictionary
      insights = json.loads(response_content)
      if isinstance(insights, dict) and len(insights) > 0:
        return True
      return False
    except:
      return False

  def __func_clean_up(response_content):
    try:
      insights = json.loads(response_content)
      return insights
    except:
      # If parsing fails, return a simple default insight
      return {"I should reflect on recent events": ["Recent experiences"]}

  prompt_template = "insights_and_guidance"
  prompt_input = create_prompt_input(persona, statements, n, test_input)

  # Create a custom prompt since we don't have a template
  prompt = f"""You are {persona.name}. Based on the following recent events and thoughts, identify {n} key insights and the evidence that supports each insight:

{statements}

Provide exactly {n} insights as a JSON dictionary where each key is an insight and each value is a list of evidence that supports that insight."""

  gpt_param = {
    "model": "gpt-4o-mini",
    "max_tokens": 300,
    "temperature": 0.7,
    "top_p": 1,
    "stream": False,
    "frequency_penalty": 0,
    "presence_penalty": 0,
    "stop": None
  }

  fail_safe = {"I should reflect on recent events": ["Recent experiences"]}
  output = safe_generate_response(prompt, gpt_param, 5, json.dumps(fail_safe),
                                   __func_validate, __func_clean_up)

  if debug or verbose:
    print(f"Insights Prompt: {prompt}")
    print(f"Insights Output: {output}")

  return output, [output, prompt, gpt_param, prompt_input, fail_safe]


def run_gpt_prompt_focal_pt(persona, statements, n=3, test_input=None, verbose=False):
  """Generate focal points for reflection based on recent events and thoughts.

  INPUT:
    persona: The Persona class instance
    statements: Recent events and thoughts as text
    n: Number of focal points to generate
  OUTPUT:
    A list of focal points (strings)
  """
  def create_prompt_input(persona, statements, n, test_input=None):
    prompt_input = {}
    prompt_input["name"] = persona.name
    prompt_input["statements"] = statements
    prompt_input["n"] = n
    return prompt_input

  def __func_validate(response_content):
    try:
      # Check if the response can be parsed as a list
      focal_points = json.loads(response_content)
      if isinstance(focal_points, list) and len(focal_points) > 0:
        return True
      return False
    except:
      return False

  def __func_clean_up(response_content):
    try:
      focal_points = json.loads(response_content)
      return focal_points
    except:
      # If parsing fails, return a simple default focal point
      return ["What happened today"]

  prompt_template = "focal_points"
  prompt_input = create_prompt_input(persona, statements, n, test_input)

  # Create a custom prompt since we don't have a template
  prompt = f"""You are {persona.name}. Based on the following recent events and thoughts, identify {n} key focal points that would be important for reflection:

{statements}

Provide exactly {n} focal points as a JSON list of strings. These should be the most significant themes or questions to reflect on."""

  gpt_param = {
    "model": "gpt-4o-mini",
    "max_tokens": 150,
    "temperature": 0.7,
    "top_p": 1,
    "stream": False,
    "frequency_penalty": 0,
    "presence_penalty": 0,
    "stop": None
  }

  fail_safe = ["What happened today", "My feelings about recent events", "Plans for the future"]
  output = safe_generate_response(prompt, gpt_param, 5, json.dumps(fail_safe),
                                   __func_validate, __func_clean_up)

  if debug or verbose:
    print(f"Focal Points Prompt: {prompt}")
    print(f"Focal Points Output: {output}")

  return output, [output, prompt, gpt_param, prompt_input, fail_safe]