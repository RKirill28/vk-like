from pathlib import Path


class Config:
    session_path: Path = Path("./session.json").absolute()


cfg = Config()
