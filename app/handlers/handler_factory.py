from app.handlers.dutchie_handler import DutchieHandler
from app.handlers.iheartjane_handler import IHeartJaneHandler
from app.handlers.leafly_handler import LeaflyHandler


class HandlerFactory:
    """
    Factory class responsible for creating the appropriate cart and checkout handlers
    based on the URL of the website.
    """

    @staticmethod
    def get_bot_handler(website_url: str):
        if "dutchie.com" in website_url:
            return DutchieHandler()
        elif "iheartjane.com" in website_url:
            return IHeartJaneHandler()
        elif "leafly.com" in website_url:
            return LeaflyHandler()
        else:
            raise ValueError(
                f"No bot handler available for the website: {website_url}"
            )