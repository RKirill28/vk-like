from dataclasses import dataclass


@dataclass
class Captcha:
    pass


class CaptchaService:
    def __init__(self, captcha_json: dict) -> None:
        self._captcha_json = captcha_json

    def _parse_captcha_json(self) -> Captcha:
        pass
