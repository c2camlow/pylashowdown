import hashlib
import io
import os
from io import BytesIO
import ctypes
import json
import aiohttp
import requests
import toml
from PIL import Image
from discord import Webhook
import discord
import cv2
import numpy as np
from packaging import version
import easyocr

def extract_text_and_positions(image_path):
    results = reader.readtext(image_path)
    text_details = {}
    for (bbox, text, prob) in results:
        top_left, top_right, bottom_right, bottom_left = bbox
        cx = (top_left[0] + top_right[0] + bottom_right[0] + bottom_left[0]) / 4
        cy = (top_left[1] + top_right[1] + bottom_right[1] + bottom_left[1]) / 4
        center = (cx, cy)
        formatted_bbox = {
            'top_left': top_left,
            'top_right': top_right,
            'bottom_right': bottom_right,
            'bottom_left': bottom_left,
            'center': center
        }

        text_details[text.lower()] = formatted_bbox

    return text_details

class DefaultEasyOCR:
    def __init__(self):
        self.reader = easyocr.Reader(['en'])

    def readtext(self, image_input):
        return self.reader.readtext(image_input)


cached_toml = {}

def load_toml_as_dict(file_path):
    if file_path not in cached_toml:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                cached_toml[file_path] = toml.load(f)
        else:
            cached_toml[file_path] = {}
    return cached_toml[file_path]

def save_dict_as_toml(data, file_path):
    with open(file_path, 'w') as f:
        toml.dump(data, f)
    cached_toml[file_path] = data


reader = DefaultEasyOCR()
cfg_api_base_url = load_toml_as_dict("cfg/general_config.toml")["api_base_url"]
api_base_url = cfg_api_base_url if cfg_api_base_url != "default" else "localhost"
brawlers_info_file_path = "cfg/brawlers_info.json"

def count_hsv_pixels(cv_image, low_hsv, high_hsv):
    hsv_image = cv2.cvtColor(cv_image, cv2.COLOR_RGB2HSV)
    mask = cv2.inRange(hsv_image, low_hsv, high_hsv)
    return cv2.countNonZero(mask)

def save_brawler_data(data):
    """
    Save the given data to a json file. As a list of dictionaries.
    """
    with open("latest_brawler_data.json", 'w') as f:
        json.dump(data, f, indent=4)



def find_template_center(main_img, template, threshold=0.8):

    main_image_cv = cv2.cvtColor(main_img, cv2.COLOR_RGB2GRAY)
    if len(template.shape) == 3 and template.shape[2] == 3:
        template_cv = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    else:
        template_cv = template
    w, h = template_cv.shape[::-1]

    # Perform template matching
    result = cv2.matchTemplate(main_image_cv, template_cv, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    # Check if the match is found based on a threshold value
    if max_val >= threshold:
        center_x = max_loc[0] + w // 2
        center_y = max_loc[1] + h // 2

        return center_x, center_y
    else:
        return False


def load_brawlers_info():
    if os.path.exists(brawlers_info_file_path):
        with open(brawlers_info_file_path, 'r') as f:
            return json.load(f)
    else:
        return {}

def update_brawlers_info(brawlers_info):
    with open(brawlers_info_file_path, 'w') as f:
        json.dump(brawlers_info, f, indent=4)


def get_brawler_list():
    if api_base_url == "localhost":
        brawler_list = list(load_brawlers_info().keys())
        return brawler_list
    url = f'https://{api_base_url}/get_brawler_list'
    response = requests.post(url)
    if response.status_code == 201:
        data = response.json()
        return data.get('brawlers', [])
    else:
        return []


def update_missing_brawlers_info(brawlers):
    brawlers_info = load_brawlers_info()
    for brawler in brawlers:
        if brawler not in brawlers_info:
            brawler_info = get_brawler_info(brawler)
            if brawler_info:
                brawlers_info[brawler] = brawler_info
                update_brawlers_info(brawlers_info)
                print(f"Added info for brawler '{brawler}': {brawler_info}")
                # Download the brawler icon
                save_brawler_icon(brawler)
            else:
                print(f"Could not find info for brawler '{brawler}'")
        if not os.path.exists(f"./api/assets/brawler_icons/{brawler}.png"):
            save_brawler_icon(brawler)


def get_brawler_info(brawler_name):
    url = f'https://{api_base_url}/get_brawler_info'  # Adjust the URL if necessary
    response = requests.post(url, json={'brawler_name': brawler_name})
    if response.status_code == 200:
        data = response.json()
        return data.get('info', [])
    else:
        print(f"Error fetching range for '{brawler_name}': {response.status_code} - {response.text}")
        return None


def save_brawler_icon(brawler_name):
    # Clean the brawler name for filename
    brawler_name_clean = brawler_name.lower().replace(' ', '').replace('-', '').replace('.', '').replace('&',
                                                                                                         '')
    brawlers_url = "https://api.brawlapi.com/v1/brawlers"
    response = requests.get(brawlers_url)
    if response.status_code != 200:
        print(f"Failed to fetch brawlers from API: {response.status_code}")
        return
    brawlers_data = response.json()['list']

    # Find the brawler in the API data
    for brawler_obj in brawlers_data:
        api_brawler_name = brawler_obj['name'].lower().replace(' ', '').replace('-', '').replace('.',
                                                                                                 '').replace(
            '&', '')
        if api_brawler_name == brawler_name_clean:
            icon_url = brawler_obj['imageUrl2']
            img_response = requests.get(icon_url)
            if img_response.status_code == 200:
                image = Image.open(BytesIO(img_response.content))
                image.save(f"api/assets/brawler_icons/{brawler_name_clean}.png")
                print(f"Saved icon for brawler '{brawler_name}'")
            else:
                print(f"Failed to download icon for '{brawler_name}'")
            return
    print(f"Icon not found for brawler '{brawler_name}'")




def get_latest_version():
    url = f'https://{api_base_url}/check_version'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data.get('version', '')
    else:
        return None

def check_version():
    if api_base_url != "localhost":
        latest_version = get_latest_version()
        if latest_version:
            current_version = load_toml_as_dict("cfg/general_config.toml").get('pyla_version', '')
            if version.parse(current_version) < version.parse(latest_version):
                print(f"Warning: (ignore if you're using early access) You are not using the latest public version of Pyla. \nCheck the discord for the latest download link.")
        else:
            print("Error, couldn't get the version, please check your internet connection or go ask for help in the discord.")


async def async_notify_user(message_type: str | None = None, screenshot: Image = None) -> None:
    user_id = load_toml_as_dict("cfg/general_config.toml")["discord_id"]
    webhook_url = load_toml_as_dict("cfg/general_config.toml")["personal_webhook"]
    if not webhook_url:
        print("Couldn't notify: no webhook configured.")
        return

    if message_type == "completed":
        status_line = f"Pyla has completed all its targets!"
        ping = f"<@{user_id}>"
    elif message_type == "bot_is_stuck":
        status_line = f"Your bot is currently stuck, attempted to restart brawl stars !"
        ping = f"<@{user_id}>"
    else:
        status_line = f"Pyla completed brawler goal for {message_type}!"
        ping = f"<@{user_id}>"

    screenshot = Image.fromarray(screenshot)
    buffer = io.BytesIO()
    screenshot.save(buffer, format="PNG")
    buffer.seek(0)
    file = discord.File(buffer, filename="screenshot.png")

    # Build the embed that holds both the text and the screenshot
    embed = discord.Embed(description=status_line)
    embed.set_image(url="attachment://screenshot.png")   # show the attached screenshot

    # Send the embed
    async with aiohttp.ClientSession() as session:
        webhook = Webhook.from_url(webhook_url, session=session)
        print("sending webhook")
        await webhook.send(embed=embed, file=file, username="Pyla notifier", content=ping)
        
def get_discord_link():
    if api_base_url == "localhost":
        return "https://discord.gg/xUusk3fw4A"
    url = f'https://{api_base_url}/get_discord_link'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data.get('link', '')
    else:
        return None

def get_online_wall_model_hash():
    url = f'https://{api_base_url}/get_wall_model_hash'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data.get('hash', '')
    else:
        return None

def calculate_sha256(file_path):
    """
    Calculate the SHA-256 hash of a file.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as file:
        # Read the file in chunks to handle large files
        for chunk in iter(lambda: file.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def current_wall_model_is_latest() -> bool:
    """
    Check if the current wall model is the latest version.
    """
    local_hash = calculate_sha256("models/tileDetector.onnx")
    online_hash = get_online_wall_model_hash()
    return local_hash == online_hash

def get_latest_wall_model_file():
    #download the new model to replace the current file and also updates the tile list
    url = f'https://{api_base_url}/get_wall_model_file'
    response = requests.get(url)
    if response.status_code == 200:
        with open("./models/tileDetector.onnx", "wb") as file:
            file.write(response.content)
        print("Downloaded the latest wall model.")
    else:
        print(f"Failed to download the latest wall model. Status code: {response.status_code}")

def get_latest_wall_model_classes():
    url = f'https://{api_base_url}/get_wall_model_classes'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data.get('classes', [])
    else:
        return None

def update_wall_model_classes():
    classes = get_latest_wall_model_classes()
    current_classes = load_toml_as_dict("cfg/bot_config.toml")["wall_model_classes"]
    if classes:
        if classes != current_classes:
            print("New wall model classes found. Updating...")
            full_config = load_toml_as_dict("cfg/bot_config.toml")
            full_config["wall_model_classes"] = classes
            save_dict_as_toml(full_config, "cfg/bot_config.toml")
            print("Updated the wall model classes.")
    else:
        print("Failed to update the wall model classes, please report this error.")


def cprint(text: str, hex_color: str): #omg color!!!
    try:
        hex_color = hex_color.lstrip("#")
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        print(f"\033[38;2;{r};{g};{b}m{text}\033[0m")
    except Exception:
        print(text)

def get_dpi_scale():
    user32 = ctypes.windll.user32
    user32.SetProcessDPIAware()
    return int(user32.GetDpiForSystem())