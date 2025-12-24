from pathlib import Path

import webview

from app import GameAPI, GameService, TextSource


def build_api() -> GameAPI:
    service = GameService(TextSource())
    return GameAPI(service)


def main() -> None:
    base_dir = Path(__file__).parent
    index_path = base_dir / "web" / "index.html"
    if not index_path.exists():
        raise FileNotFoundError(f"No se encontró la vista web en {index_path}")

    api = build_api()
    webview.create_window(
        "Typer",
        index_path.as_uri(),
        js_api=api,
        frameless=True,
        easy_drag=True,
        fullscreen=True,
    )
    webview.start(debug=True)


if __name__ == "__main__":
    main()
