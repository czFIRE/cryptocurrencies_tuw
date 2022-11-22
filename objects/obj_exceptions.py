
class ValidationException(Exception):
    def __init__(self, message: str = "Object is invalid", *args, **kwargs):
        super().__init__(message, *args, **kwargs)
