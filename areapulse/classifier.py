KEYWORDS = {
    'Water':       ['no water','pipe burst','leak','water supply','water issue','nahi aa raha'],
    'LPG':         ['gas cylinder','no gas','lpg','cylinder','gas nahi'],
    'Garbage':     ['waste','garbage','trash','bin','kachra','smell'],
    'Electricity': ['no power','blackout','electricity','light gone','bijli','current nahi'],
}

def auto_tag(description):
    desc = description.lower()
    for tag, words in KEYWORDS.items():
        if any(w in desc for w in words):
            return tag
    return 'Other'

def priority_score(upvotes, timestamp):
    import time
    age = max((time.time() - timestamp) / 3600, 1)
    return round(upvotes / age, 2)


