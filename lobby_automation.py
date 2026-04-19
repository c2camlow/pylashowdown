import time

import cv2
import numpy as np

from typization import BrawlerName
from utils import extract_text_and_positions, count_hsv_pixels, load_toml_as_dict, find_template_center

debug = load_toml_as_dict("cfg/general_config.toml")['super_debug'] == "yes"
gray_pixels_treshold = load_toml_as_dict("./cfg/bot_config.toml")['idle_pixels_minimum']
class LobbyAutomation:

    def __init__(self, window_controller):
        self.coords_cfg = load_toml_as_dict("./cfg/lobby_config.toml")
        self.window_controller = window_controller

    def check_for_idle(self, frame):
        wr = self.window_controller.width_ratio
        hr = self.window_controller.height_ratio
        x_start, x_end = int(400 * wr), int(1500 * wr)
        y_start, y_end = int(380 * hr), int(700 * hr)
        gray_pixels = count_hsv_pixels(frame[y_start:y_end, x_start:x_end], (0, 0, 55), (10, 15, 77))
        if debug: print(f"gray pixels (if > {gray_pixels_treshold} then bot will try to unidle) :", gray_pixels)
        if gray_pixels > gray_pixels_treshold:
            self.window_controller.click(int(535 * wr), int(615 * hr))

    def select_brawler(self, brawler):
        self.window_controller.screenshot()
        wr = self.window_controller.width_ratio
        hr = self.window_controller.height_ratio

        x, y = self.coords_cfg['lobby']['brawler_btn'][0]*wr, self.coords_cfg['lobby']['brawler_btn'][1]*hr
        self.window_controller.click(x, y)
        c = 0
        found_brawler = False
        for i in range(50):
            screenshot = self.window_controller.screenshot()
            screenshot = cv2.resize(screenshot, (int(screenshot.shape[1] * 0.65), int(screenshot.shape[0] * 0.65)), interpolation=cv2.INTER_AREA)

            if debug: print("extracting text on current screen...")
            results = extract_text_and_positions(screenshot)
            reworked_results = {}
            for key in results.keys():
                orig_key = key
                for symbol in [' ', '-', '.', "&"]:
                    key = key.replace(symbol, "")
                
                key = self.resolve_ocr_typos(key)
                reworked_results[key] = results[orig_key]
            if debug:
                print("All detected text while looking for brawler name:", reworked_results.keys())
                print()
            if brawler in reworked_results.keys():
                x, y = reworked_results[brawler]['center']
                self.window_controller.click(int(x * 1.5385), int(y * 1.5385))
                print("Found brawler ", brawler, "clicking on its icon at ", int(x * 1.5385), int(y * 1.5385))
                time.sleep(1)
                select_x, select_y = self.coords_cfg['lobby']['select_btn'][0], self.coords_cfg['lobby']['select_btn'][1]
                self.window_controller.click(select_x, select_y, already_include_ratio=False)
                time.sleep(0.5)
                print("Selected brawler ", brawler)
                found_brawler = True
                break
            if c == 0:
                wr = self.window_controller.width_ratio
                hr = self.window_controller.height_ratio
                self.window_controller.swipe(int(1700 * wr), int(900 * hr), int(1700 * wr), int(850 * hr), duration=0.8)
                c += 1
                continue

            self.window_controller.swipe(int(1700 * wr), int(900 * hr), int(1700 * wr), int(650 * hr), duration=0.8)
            time.sleep(1)
        if not found_brawler:
            print(f"WARNING: Brawler '{brawler}' was not found after 50 scroll attempts. "
                  f"The bot will continue with the currently selected brawler.")
            raise ValueError(f"Brawler '{brawler}' could not be found in the brawler selection menu.")

    @staticmethod
    def resolve_ocr_typos(potential_brawler_name: str) -> str:
        """
        Matches well known 'typos' from OCR to the correct brawler's name
        or returns the original string
        """

        matched_typo: str | None = {
            'shey': BrawlerName.Shelly.value,
            'shlly': BrawlerName.Shelly.value,
            'larryslawrie': BrawlerName.Larry.value,
            '[eon': BrawlerName.Leon.value,
        }.get(potential_brawler_name, None)

        return matched_typo or potential_brawler_name