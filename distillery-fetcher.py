##### Distillery Fetcher Runpod Bot - Version 1.0 - June 14 2023
import os
import discord
from discord.ext import commands
import json
import time
import runpod

######## User inputs below this line
RUNPOD_KEY = os.getenv('RUNPOD_API_KEY')  # Fetch token from environment variable; add this to the environment variables of your system.
ENDPOINT_ID = 'fobs31pt8lfxtx' # 'serve_bloodymary_v1'
TOKEN = os.getenv('DISCORD_BOT_TOKEN')  # Fetch token from environment variable; add this to the environment variables of your system
SERVER_ID = [1105589864453394472]  # Followfox AI Testbed
TOTAL_BATCHES = 4  # Maximum number of batches to generate
BOT_NAME = 'serve' # This name will be the slash command name
BOT_DESCRIPTION = 'Create upscaled images using Distillery Models'
BASE_NEGATIVE_PROMPT = ", worst quality, deformed, low quality, bad"
BASE_POSITIVE_PROMPT = ", best quality, high quality, good"
IMG_PER_BATCH = 1  # Number of images to generate per batch (warning: Runpod has a limit of 2 megabytes per request without AWS as an intermediary, which makes it impossible to get more than one image without it)

######## Code to call the API to generate images (must be in the Master Server) ########
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

runpod.api_key=RUNPOD_KEY
endpoint = runpod.Endpoint(ENDPOINT_ID)

async def call_runpod(payload_for_runpod):
    run_request = await endpoint.run(payload_for_runpod)
    return run_request.output()  # Sends a request to the API and returns a list of file objects

async def image_file_assembler(image_json): # Assemble the image file in Discord file format from the JSON response, which contains 'image_b64' and 'parameters' keys. 'parameters' are the png info
    image_file = []
    for i in range(len(image_json)):
        image_file.append(discord.File(fp=image_json[i]['image_b64'], filename=f"image{i}.png"))
    return image_file  # Returns a list of file objects

async def fetch_images(payload, num_batches):
    payload_for_runpod = {
        'input': payload
    }    
    timestamp=time.time()
    print(f"    {timestamp}      3. JSON adapted for Runpod use. Sending to Runpod iteration loop...")
    file_objects = []
    image_json = None  # Initialize responses here
    image_file = None
    print(payload_for_runpod)
    for i in range(num_batches):
        timestamp=time.time()
        print(f"    {timestamp}      3.    - Sending for Runpod... ({i+1}/{num_batches})")
        image_json = await call_runpod(payload_for_runpod)
        timestamp=time.time()
        print(f"    {timestamp}      3.    - Image JSON received. Converting to Discord file... ({i+1}/{num_batches})")
        image_file = await image_file_assembler(image_json)        
        file_objects.extend(image_file)
        timestamp=time.time()
        print(f"    {timestamp}      3.    - Discord file appended. Reiterating... ({i+1}/{num_batches})")
    print(f"    {timestamp}      3.    - Iterations finished.")
    return file_objects  # Sends requests to the API and returns a list of file objects

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.slash_command(name=BOT_NAME, guild_ids=SERVER_ID, description=BOT_DESCRIPTION, interaction_response_message="Serving images. Please wait...")
async def create(ctx, *, prompt: str, negative_prompt: str = ""):
    timestamp=time.time()
    print(f"    {timestamp}      1. Command received! Building payload...")
    start_time = time.time()

    #build the payload variable for the request
    with open('payload-txt2img.json', 'r') as json_file:
        payload = json.load(json_file)        
    payload["prompt"] = prompt + BASE_POSITIVE_PROMPT  # Introduce to payload the input text
    payload["negative_prompt"] = negative_prompt + BASE_NEGATIVE_PROMPT  # Introduce to payload the input negative text
    payload["batch_size"]=IMG_PER_BATCH
    timestamp=time.time()
    print(f"    {timestamp}      2. Payload built. Sending to Fetcher...")

    #inform the user in Discord that the request is being processed
    await ctx.respond(f"Serving images for *{prompt} --neg {negative_prompt}*. Please wait...")

    #send the request for image generation
    images = await fetch_images(payload, TOTAL_BATCHES)

    #receive the images and send them to Discord
    files_dict = {f'file{i}': image for i, image in enumerate(images)}
    await ctx.send(f"*{prompt} --neg {negative_prompt}, by {ctx.author.mention}:*", files=files_dict.values())       
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"    {timestamp} Fetcher request completed in {elapsed_time:.2f} seconds.")

bot.run(TOKEN)
######## End of Code to call the API to generate images (must be in the Master Server) ########