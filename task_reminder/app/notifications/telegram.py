class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id

    async def send(self, title: str, message: str, actions: list[dict] | None = None) -> None:
        # TODO: implement python-telegram-bot message with inline keyboard.
        return None
