class SonataException(Exception):
    def __init__(self, code: int, error_message: str, *args: object) -> None:
        self.code = code
        self.error_message = error_message
        super().__init__(error_message, *args)


class SonataMissingParametersException(SonataException):
    def __init__(self, error_message: str, *args: object) -> None:
        super().__init__(400, error_message, *args)


class SonataUnauthorizedException(SonataException):
    def __init__(self, error_message: str, *args: object) -> None:
        super().__init__(401, error_message, *args)


class SonataNotFoundException(SonataException):
    def __init__(self, error_message: str, *args: object) -> None:
        super().__init__(404, error_message, *args)


class SonataAlreadyExistsException(SonataException):
    def __init__(self, error_message: str, *args: object) -> None:
        super().__init__(400, error_message, *args)
