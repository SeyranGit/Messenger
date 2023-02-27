from src.config.types import (singinData_t, singupData_t,
                              userExists_t, userNotExists_t,
                              userAdded_t, appendUser_t)

unsuccessfulLogin = {
    "type": singupData_t,
    "code": 400,
    "singin": False,
    "content": None
}

successfulLogin = {
    "type": singinData_t,
    "code": 200,
    "content": {
        "singin": True,
        "username": None,
        "friends": None
    }
}

successfulRegistration = {
    "type": singupData_t,
    "code": 200,
    "content": {
        "singup": True,
        "username": None
    }
}

userExists = {
    "type": userExists_t,
    "code": 200,
    "content": None
}

userNotExists = {
    "type": userNotExists_t,
    "code": 200,
    "content": None
}

userAdded = {
    "type": userAdded_t,
    "code": 200,
    "content": None
}

badRequest = {
    "type": None,
    "code": 400,
    "content": None
}

appendUser = {
    "type": appendUser_t,
    "code": 200,
    "content": {}
}


def appendFieldResponse(response: dict, fields: dict) -> dict:
    for key, value in fields.items():
        if isinstance(value, dict): response[key].update(value)
        else: response[key] = value

    return response

