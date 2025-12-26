last_message = None

def should_speak(result):
    global last_message

    if result["risk_level"] == "low":
        return False

    if result["spoken_guidance"] == last_message:
        return False

    last_message = result["spoken_guidance"]
    return True
