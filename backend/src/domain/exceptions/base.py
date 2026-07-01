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


class ExternalToolError(ParallaxError):
    """A skill/tool an agent invoked (retrieval, rerank, MCP call) failed."""

    pass
