
def get_curr_date():
    from datetime import datetime
    return datetime.now().strftime("%d.%m.%Y")

def get_curr_time():
    from datetime import datetime
    return datetime.now().strftime("%H:%M")