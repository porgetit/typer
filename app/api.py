"""pywebview bridge exposed to the frontend."""

from typing import Dict

from .game_service import GameService
import webview


class GameAPI:
    def __init__(self, service: GameService) -> None:
        self.service = service

    # Methods below are called from JavaScript through window.pywebview.api

    def load_demo_text(self) -> Dict[str, object]:
        return self.service.load_demo_text()

    def load_text_file(self, path: str) -> Dict[str, object]:
        return self.service.load_text_file(path)

    def set_text(self, text: str) -> Dict[str, object]:
        return self.service.set_text(text)

    def current(self) -> Dict[str, object]:
        return self.service.current()

    def reset(self) -> Dict[str, object]:
        return self.service.reset()

    def repeat_current(self) -> Dict[str, object]:
        return self.service.repeat_current()

    def restart_progress(self) -> Dict[str, object]:
        return self.service.restart_progress()

    def next_text(self) -> Dict[str, object]:
        return self.service.next_text()

    def submit_input(self, typed: str) -> Dict[str, object]:
        return self.service.submit_input(typed)

    def tick(self) -> Dict[str, object]:
        return self.service.tick()

    def summary(self) -> Dict[str, object]:
        return self.service.summary()

    def exit_app(self) -> None:
        if webview.windows:
            webview.windows[0].destroy()
