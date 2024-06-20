class SonataException(Exception):
    def __init__(self, code: int, error_message: str, *args: object) -> None:
        self.code = code
        self.error_message = error_message
        super().__init__(error_message, *args)
