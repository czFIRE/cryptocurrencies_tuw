

class MessageException(Exception):
    def __init__(self, message: str, *args, **kwargs):
        super().__init__(message, *args, **kwargs)


class InvalidMsgException(MessageException):
    def __init__(self, message: str = "Message is invalid"):
        super().__init__(message=message)


class MalformedMsgException(MessageException):
    def __init__(self, message: str = "Message is malformed"):
        super().__init__(message=message)


class UnsupportedMsgException(MessageException):
    def __init__(self, message: str = "Unsupported message type"):
        super().__init__(message=message)


class UnexpectedMsgException(MessageException):
    def __init__(self, message: str = "Unexpected message received"):
        super().__init__(message=message)


class ErrorMsgException(MessageException):
    def __init__(self, message: str = "Received error message"):
        super().__init__(message=message)
