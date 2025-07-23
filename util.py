from datetime import datetime

def get_curr_date():
    return datetime.now().strftime("%d.%m.%Y")

def get_curr_time():
    return datetime.now().strftime("%H:%M")