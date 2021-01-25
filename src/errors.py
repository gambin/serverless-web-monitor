from enum import Enum
class CustomErrors(Enum):
    OS_ENV_NOT_DEFINED = 1
    TEST_NOT_DEFINED = 2
    TEST_NOT_FOUND = 3
    GENERIC_EXCEPTION = 99

class HaltException(Exception):
    pass