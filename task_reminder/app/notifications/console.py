class ConsoleNotifier:
    def send(self, title: str, message: str) -> None:
        print(f"{title}\n{message}")
