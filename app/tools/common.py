def success(data):
    return {"ok": True, "data": data, "error": None}


def failure(code, message):
    return {"ok": False, "data": {}, "error": {"code": code, "message": message}}
