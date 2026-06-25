class ParallaxError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class DomainError(ParallaxError):
    pass


class NotFoundError(DomainError):
    pass


class IngestionError(ParallaxError):
    pass


class DebateError(ParallaxError):
    pass


class IntakeError(ParallaxError):
    pass
