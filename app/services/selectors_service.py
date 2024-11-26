import json
from pathlib import Path
from typing import Dict, Optional

class SelectorsService:
    _selectors = {}

    @staticmethod
    def load_all_selectors(directory: str):
        """
        Load all JSON selector files from the specified directory.
        This method is called once during the app startup.
        :param directory: The directory containing JSON files.
        """
        selectors_path = Path(directory)
        for json_file in selectors_path.glob("*.json"):
            with open(json_file, "r") as file:
                selectors_data = json.load(file)
                bot_name = selectors_data["bot_name"].lower()
                SelectorsService._selectors[bot_name] = selectors_data

    @staticmethod
    def get_selectors(bot_name: str, section: Optional[str] = None):
        """
        Retrieves the selectors for a specific bot and section (e.g., 'add_to_cart').
        :param bot_name: The name of the bot (e.g., 'dutchie').
        :param section: The section of selectors (e.g., 'add_to_cart').
        :param key: The specific selector key within the section (optional).
        :return: The selector or the dictionary of selectors for the section.
        """
        bot_name = bot_name.lower()
        if bot_name not in SelectorsService._selectors:
            raise ValueError(f"No selectors found for bot '{bot_name}'.")

        selectors = SelectorsService._selectors[bot_name]
        if section:
            return selectors.get("selectors", {}).get(section, {})
        else:
            return selectors
    
    @staticmethod
    def get_checkout_url(bot_name: str) -> str:
        """
        Retrieves the checkout URL for a specific bot.
        :param bot_name: The name of the bot (e.g., 'iheartjane').
        :return: The checkout URL.
        """
        bot_name = bot_name.lower()
        if bot_name not in SelectorsService._selectors:
            raise ValueError(f"No selectors found for bot '{bot_name}'.")

        selectors = SelectorsService._selectors[bot_name]
        return selectors.get("checkout_url", "")
    
    @staticmethod
    def get_cart_url(bot_name: str) -> str:
        """
        Retrieves the checkout URL for a specific bot.
        :param bot_name: The name of the bot (e.g., 'iheartjane').
        :return: The checkout URL.
        """
        bot_name = bot_name.lower()
        if bot_name not in SelectorsService._selectors:
            raise ValueError(f"No selectors found for bot '{bot_name}'.")

        selectors = SelectorsService._selectors[bot_name]
        return selectors.get("bag", "")