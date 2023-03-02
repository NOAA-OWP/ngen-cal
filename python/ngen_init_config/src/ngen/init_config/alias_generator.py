def lower_case(s: str) -> str:
    return s.lower()


def upper_case(s: str) -> str:
    return s.upper()


def pascal_case(s: str) -> str:
    s = s.replace("-", "_")
    if s.isupper() and s.find("_") > -1:
        s = s.lower()

    capitalize = True
    pascal = ""
    for c in s:
        if c == "_":
            capitalize = True
        elif capitalize:
            pascal = pascal + c.upper()
            capitalize = False
        else:
            pascal = pascal + c

    return pascal


def camel_case(s: str) -> str:
    s = pascal_case(s)
    return s[:1].lower() + s[1:]


def snake_case(s: str) -> str:
    s = s.replace("-", "_")
    if s.find("_") > -1:
        return s.lower()

    snake = ""
    for i, c in enumerate(s):
        if i > 0 and c.isupper():
            snake = snake + "_"
        snake = snake + c.lower()
    return snake


def screaming_snake_case(s: str) -> str:
    s = snake_case(s)
    return s.upper()


def kabab_case(s: str) -> str:
    s = snake_case(s)
    return s.replace("_", "-")


def screaming_kabab_case(s: str) -> str:
    s = kabab_case(s)
    return s.upper()
