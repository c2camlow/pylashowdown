import os.path
import sys

import asyncio
import time

import cv2
import numpy as np
import requests

from state_finder import get_state, find_game_result
from trophy_observer import TrophyObserver
from utils import find_template_center, load_toml_as_dict, async_notify_user, \
    save_brawler_data

user_id = load_toml_as_dict("cfg/general_config.toml")['discord_id']
debug = load_toml_as_dict("cfg/general_config.toml")['super_debug'] == "yes"
user_webhook = load_toml_as_dict("cfg/general_config.toml")['personal_webhook']


def notify_user(message_type):
    # message type will be used to have conditions determining the message
    # but for now there's only one possible type of message
    message_data = {
        'content': f"<@{user_id}> Pyla Bot has completed all it's targets !"
    }

    response = requests.post(user_webhook, json=message_data)

    if response.status_code != 204:
        print(
            f'Failed to send message. Be sure to have put a valid webhook url in the config. Status code: {response.status_code}')


def load_image(image_path, scale_factor):
    # Load the image
    image = cv2.imread(image_path)
    orig_height, orig_width = image.shape[:2]

    # Calculate the new dimensions based on the scale factor
    new_width = int(orig_width * scale_factor)
    new_height = int(orig_height * scale_factor)

    # Resize the image
    resized_image = cv2.resize(image, (new_width, new_height))
    return resized_image

class StageManager:

    def __init__(self, brawlers_data, lobby_automator, window_controller):
        self.Lobby_automation = lobby_automator
        self.lobby_config = load_toml_as_dict("./cfg/lobby_config.toml")
        self.close_popup_icon = None
        self.brawlers_pick_data = brawlers_data
        brawler_list = [brawler["brawler"] for brawler in brawlers_data]
        self.Trophy_observer = TrophyObserver(brawler_list)
        self.time_since_last_stat_change = time.time()
        self.long_press_star_drop = load_toml_as_dict("./cfg/general_config.toml")["long_press_star_drop"]
        self.play_again_on_win = load_toml_as_dict("./cfg/bot_config.toml")["play_again_on_win"] == "yes"
        self.window_controller = window_controller
        self.states = {
            'shop': self.quit_shop,
            'brawler_selection': self.quit_shop,
            'popup': self.close_pop_up,
            'match': lambda: 0,
            'end_draw': self.end_game,
            'end_victory': self.end_game,
            'end_defeat': self.end_game,
            'lobby': self.start_game,
            'star_drop': self.click_star_drop,
            'trophy_reward': lambda: self.window_controller.press_key("Q")
        }

    @staticmethod
    def validate_trophies(trophies_string):
        trophies_string = trophies_string.lower()
        while "s" in trophies_string:
            trophies_string = trophies_string.replace("s", "5")
        numbers = ''.join(filter(str.isdigit, trophies_string))

        if not numbers:
            return False

        trophy_value = int(numbers)
        return trophy_value

    def start_game(self):
        print("state is lobby, starting game")
        values = {
            "trophies": self.Trophy_observer.current_trophies,
            "wins": self.Trophy_observer.current_wins
        }

        type_of_push = self.brawlers_pick_data[0]['type']
        if type_of_push not in values:
            type_of_push = "trophies"
        value = values[type_of_push]
        if value == "" and type_of_push == "wins":
            value = 0
        push_current_brawler_till = self.brawlers_pick_data[0]['push_until']
        if push_current_brawler_till == "" and type_of_push == "wins":
            push_current_brawler_till = 300
        if push_current_brawler_till == "" and type_of_push == "trophies":
            push_current_brawler_till = 1000

        if value >= push_current_brawler_till:
            if len(self.brawlers_pick_data) <= 1:
                print("Brawler reached required trophies/wins. No more brawlers selected for pushing in the menu. "
                      "Bot will now pause itself until closed.", value, push_current_brawler_till)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    screenshot = self.window_controller.screenshot()
                    loop.run_until_complete(async_notify_user("completed", screenshot))
                finally:
                    loop.close()
                print("Bot stopping: all targets completed with no more brawlers.")
                self.window_controller.keys_up(list("wasd"))
                self.window_controller.close()
                sys.exit(0)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                screenshot = self.window_controller.screenshot()
                loop.run_until_complete(async_notify_user(self.brawlers_pick_data[0]["brawler"], screenshot))
            finally:
                loop.close()
            self.brawlers_pick_data.pop(0)
            self.Trophy_observer.change_trophies(self.brawlers_pick_data[0]['trophies'])
            self.Trophy_observer.current_wins = self.brawlers_pick_data[0]['wins'] if self.brawlers_pick_data[0]['wins'] != "" else 0
            self.Trophy_observer.win_streak = self.brawlers_pick_data[0]['win_streak']
            next_brawler_name = self.brawlers_pick_data[0]['brawler']
            if self.brawlers_pick_data[0]["automatically_pick"]:
                print("Picking next automatically picked brawler")
                screenshot = self.window_controller.screenshot()
                current_state = get_state(screenshot)
                if current_state != "lobby":
                    print("Trying to reach the lobby to switch brawler")

                max_attempts = 30
                attempts = 0
                while current_state != "lobby" and attempts < max_attempts:
                    self.window_controller.press_key("Q")
                    print("Pressed Q to return to lobby")
                    time.sleep(1)
                    screenshot = self.window_controller.screenshot()
                    current_state = get_state(screenshot)
                    attempts += 1
                if attempts >= max_attempts:
                    print("Failed to reach lobby after max attempts")
                else:
                    self.Lobby_automation.select_brawler(next_brawler_name)
            else:
                print("Next brawler is in manual mode, waiting 10 seconds to let user switch.")

        # q btn is over the start btn
        self.window_controller.keys_up(list("wasd"))
        self.window_controller.press_key("Q")
        print("Pressed Q to start a match")
    def click_star_drop(self):
        if self.long_press_star_drop == "yes":
            self.window_controller.press_key("Q",10)
        else:
            self.window_controller.press_key("Q")

    def end_game(self):
        screenshot = self.window_controller.screenshot()

        found_game_result = False
        current_state = get_state(screenshot)
        button_pressed = False
        end_screen_time = time.time()
        
        while current_state.startswith("end") and time.time() - end_screen_time < 25:
            if time.time() - self.time_since_last_stat_change > 10:

                # , current_brawler=self.brawlers_pick_data[0]['brawler']
                found_game_result = current_state.split("_")[1]
                current_brawler = self.brawlers_pick_data[0]['brawler']
                self.Trophy_observer.add_trophies(found_game_result, current_brawler)
                self.Trophy_observer.add_win(found_game_result)
                self.time_since_last_stat_change = time.time()
                values = {
                    "trophies": self.Trophy_observer.current_trophies,
                    "wins": self.Trophy_observer.current_wins
                }
                type_to_push = self.brawlers_pick_data[0]['type']
                if type_to_push not in values:
                    type_to_push = "trophies"
                value = values[type_to_push]
                self.brawlers_pick_data[0][type_to_push] = value
                save_brawler_data(self.brawlers_pick_data)
                push_current_brawler_till = self.brawlers_pick_data[0]['push_until']

                if value == "" and type_to_push == "wins":
                    value = 0
                if push_current_brawler_till == "" and type_to_push == "wins":
                    push_current_brawler_till = 300
                if push_current_brawler_till == "" and type_to_push == "trophies":
                    push_current_brawler_till = 1000

                if value >= push_current_brawler_till:
                    if len(self.brawlers_pick_data) <= 1:
                        print(
                            "Brawler reached required trophies/wins. No more brawlers selected for pushing in the menu. "
                            "Bot will now pause itself until closed.")
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            screenshot = self.window_controller.screenshot()
                            loop.run_until_complete(async_notify_user("completed", screenshot))
                        finally:
                            loop.close()
                        if os.path.exists("latest_brawler_data.json"):
                            os.remove("latest_brawler_data.json")
                        print("Bot stopping: all targets completed.")
                        self.window_controller.keys_up(list("wasd"))
                        self.window_controller.close()
                        sys.exit(0)
            
            if not button_pressed:
                if self.play_again_on_win and found_game_result == "victory":
                    self.window_controller.press_key("F")
                else:
                    print("Game has ended, pressing Q")
                    self.window_controller.press_key("Q")
                    time.sleep(2)
                    print("Pressing Q again")
                    self.window_controller.press_key("Q")
                button_pressed = True
            
            time.sleep(0.5)
            screenshot = self.window_controller.screenshot()
            current_state = get_state(screenshot)
        
        if self.play_again_on_win and found_game_result == "victory":
            print("Waiting for match to start...")
            start_wait_time = time.time()
            while time.time() - start_wait_time < 25:
                screenshot = self.window_controller.screenshot()
                current_state = get_state(screenshot)
                if current_state == "match":
                    print("Match started successfully!")
                    return
                time.sleep(0.5)
            
            print("Match did not start within 25s, pressing Q to return to lobby.")
            self.window_controller.press_key("Q")
            time.sleep(2)
            print("Pressing Q again")
            self.window_controller.press_key("Q")
        
        print("Game has ended", current_state)

    def quit_shop(self):
        self.window_controller.click(100*self.window_controller.width_ratio, 60*self.window_controller.height_ratio)

    def close_pop_up(self):
        screenshot = self.window_controller.screenshot()
        if self.close_popup_icon is None:
            self.close_popup_icon = load_image("images/states/close_popup.png", self.window_controller.scale_factor)
        popup_location = find_template_center(screenshot, self.close_popup_icon)
        if popup_location:
            self.window_controller.click(*popup_location)

    def do_state(self, state, data=None):
        if data is not None:
            self.states[state](data)
            return
        self.states[state]()

