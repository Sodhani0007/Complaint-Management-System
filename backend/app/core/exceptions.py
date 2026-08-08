"""
Domain-specific exceptions, caught by exception handlers registered in
main.py and translated into the correct HTTP status codes. Routers raise
these instead of raw HTTPException so the same error type maps consistently
no matter which endpoint triggers it.
"""


class UnsupportedFileTypeError(Exception):
    pass


class FileTooLargeError(Exception):
    pass


class NoInputProvidedError(Exception):
    pass


class ComplaintNotFoundError(Exception):
    pass


class InvalidBatchReferenceError(Exception):
    pass
