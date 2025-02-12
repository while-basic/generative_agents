"""
Author: Joon Sung Park (joonspk@stanford.edu)

File: execute.py
Description: This defines the "Act" module for generative agents. 
"""
import sys
import random
sys.path.append('../../')

from global_methods import *
from path_finder import *
from utils import *

def execute(persona, maze, personas, plan): 
  """
  Given a plan (action's string address), we execute the plan (actually 
  outputs the tile coordinate path and the next coordinate for the 
  persona). 

  INPUT:
    persona: Current <Persona> instance.  
    maze: An instance of current <Maze>.
    personas: A dictionary of all personas in the world. 
    plan: This is a string address of the action we need to execute. 
       It comes in the form of "{world}:{sector}:{arena}:{game_objects}". 
       It is important that you access this without doing negative 
       indexing (e.g., [-1]) because the latter address elements may not be 
       present in some cases. 
       e.g., "dolores double studio:double studio:bedroom 1:bed"
    
  OUTPUT: 
    execution
  """
  if "<random>" in plan and persona.scratch.planned_path == []: 
    persona.scratch.act_path_set = False

  # <act_path_set> is set to True if the path is set for the current action. 
  # It is False otherwise, and means we need to construct a new path. 
  if not persona.scratch.act_path_set: 
    # <target_tiles> is a list of tile coordinates where the persona may go 
    # to execute the current action. The goal is to pick one of them.
    target_tiles = None
    closest_target_tile = None  
    path = [persona.scratch.curr_tile]  

    print ('aldhfoaf/????')
    print (plan)

    if "<persona>" in plan: 
      # Executing persona-persona interaction.
      target_p_tile = (personas[plan.split("<persona>")[-1].strip()]
                       .scratch.curr_tile)
      potential_path = path_finder(maze.collision_maze, 
                                   persona.scratch.curr_tile, 
                                   target_p_tile, 
                                   collision_block_id)
      if len(potential_path) <= 2: 
        target_tiles = [potential_path[0]]
      else: 
        potential_1 = path_finder(maze.collision_maze, 
                                persona.scratch.curr_tile, 
                                potential_path[int(len(potential_path)/2)], 
                                collision_block_id)
        potential_2 = path_finder(maze.collision_maze, 
                                persona.scratch.curr_tile, 
                                potential_path[int(len(potential_path)/2)+1], 
                                collision_block_id)
        if len(potential_1) <= len(potential_2): 
          target_tiles = [potential_path[int(len(potential_path)/2)]]
        else: 
          target_tiles = [potential_path[int(len(potential_path)/2+1)]]
    
    elif "<waiting>" in plan: 
      # Executing interaction where the persona has decided to wait before 
      # executing their action.
      x = int(plan.split()[1])
      y = int(plan.split()[2])
      target_tiles = [[x, y]]

    elif "<random>" in plan: 
      # Executing a random location action.
      plan = ":".join(plan.split(":")[:-1])
      target_tiles = maze.address_tiles.get(plan)
      if not target_tiles:
        print(f"Warning: Invalid address {plan}, defaulting to current tile")
        return persona.scratch.curr_tile, "", f"{persona.name} is waiting as the destination {plan} is unavailable"
      target_tiles = random.sample(list(target_tiles), 1)

    else: 
      # This is our default execution. We simply take the persona to the
      # location where the current action is taking place. 
      # Retrieve the target addresses. Again, plan is an action address in its
      # string form. <maze.address_tiles> takes this and returns candidate 
      # coordinates. 
      target_tiles = maze.address_tiles.get(plan)
      if not target_tiles:
        print(f"Warning: Invalid address {plan}, defaulting to current tile")
        return persona.scratch.curr_tile, "", f"{persona.name} is waiting as the destination {plan} is unavailable"

    # There are sometimes more than one tile returned from this (e.g., a tabe
    # may stretch many coordinates). So, we sample a few here. And from that 
    # random sample, we will take the closest ones. 
    if len(target_tiles) < 4: 
      target_tiles = random.sample(list(target_tiles), len(target_tiles))
    else:
      target_tiles = random.sample(list(target_tiles), 4)
    # If possible, we want personas to occupy different tiles when they are 
    # headed to the same location on the maze. It is ok if they end up on the 
    # same time, but we try to lower that probability. 
    # We take care of that overlap here.  
    persona_name_set = set(personas.keys())
    new_target_tiles = []
    for i in target_tiles: 
      curr_event_set = maze.access_tile(i)["events"]
      pass_curr_tile = False
      for j in curr_event_set: 
        if j[0] in persona_name_set: 
          pass_curr_tile = True
      if not pass_curr_tile: 
        new_target_tiles += [i]
    if len(new_target_tiles) == 0: 
      new_target_tiles = target_tiles
    target_tiles = new_target_tiles

    # Now that we've identified the target tile, we find the shortest path to
    # one of the target tiles. 
    curr_tile = persona.scratch.curr_tile
    collision_maze = maze.collision_maze
    
    if not target_tiles:
        # If we have no target tiles, stay at current position
        closest_target_tile = curr_tile
    else:
        min_path_length = float('inf')
        for i in target_tiles: 
            try:
                # Ensure coordinates are in the correct format
                start = tuple(map(int, curr_tile))
                end = tuple(map(int, i))
                
                # path_finder takes a collision_maze and the curr_tile coordinate as 
                # an input, and returns a list of coordinate tuples that becomes the
                # path. 
                curr_path = path_finder(maze.collision_maze, 
                                    start, 
                                    end, 
                                    collision_block_id)
                
                if curr_path and len(curr_path) < min_path_length:
                    min_path_length = len(curr_path)
                    closest_target_tile = i
                    path = curr_path
            except Exception as e:
                print(f"Path finding error for tile {i}: {str(e)}")
                continue

        if not closest_target_tile:
            # If no valid path was found to any target, stay at current position
            print(f"No valid path found for {persona.name} to any target tile")
            closest_target_tile = curr_tile
            path = [curr_tile]

    # Store the target tile and path for future reference
    persona.scratch.current_target_tile = closest_target_tile
    
    # Actually setting the <planned_path> and <act_path_set>. We cut the 
    # first element in the planned_path because it includes the curr_tile. 
    try:
        persona.scratch.planned_path = path[1:] if len(path) > 1 else []
    except Exception as e:
        print(f"Error setting planned path: {str(e)}")
        persona.scratch.planned_path = []
    
    persona.scratch.act_path_set = True
  
  # Setting up the next immediate step. We stay at our curr_tile if there is
  # no <planned_path> left, but otherwise, we go to the next tile in the path.
  try:
    if not persona.scratch.planned_path:
      # We've reached our destination or have nowhere to go
      pronunciatio = ""
      description = f"{persona.name} is {persona.scratch.act_description}"
      return persona.scratch.current_target_tile or persona.scratch.curr_tile, pronunciatio, description
    
    # We're still moving to our destination
    next_tile = tuple(map(int, persona.scratch.planned_path[0]))  # Ensure coordinates are integers
    pronunciatio = f"{persona.name} is on the way to {persona.scratch.act_description}"
    description = pronunciatio
    
    persona.scratch.planned_path = persona.scratch.planned_path[1:]
    return next_tile, pronunciatio, description
    
  except Exception as e:
    print(f"Error in execute: {str(e)}")
    # If anything goes wrong, stay at current position
    return persona.scratch.curr_tile, "", f"{persona.name} is waiting due to an error"
