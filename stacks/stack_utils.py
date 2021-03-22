def to_camel_case(string: str):
    """Returns a CamelCase version of the string and removes some characters (see source code)"""
    string = string.title()
    remove = ["_", " ", ".", "-", ":", "@", "#", "!", "?", "(", ")", "[", "]", "{", "}", "/", "\\", ",", "=", ">", "<",
              "|"]
    string = string.translate({ord(c): None for c in remove})
    return string
