KEYWORDS = {
    'pothole':     ['pothole','road','crater','hole','bump','broken road','khada','damaged road','manhole cover'],
    'water':       ['water','leak','pipe','flood','waterlog','pani','overflow','pipeline','burst','puddle'],
    'garbage':     ['garbage','waste','trash','kachra','dump','litter','smell','refuse','filth','bin','burning'],
    'streetlight': ['streetlight','street light','lamp post','dark street','batti','light pole'],
    'traffic':     ['traffic','signal','jam','congestion','accident','zebra crossing','speed breaker'],
    'noise':       ['noise','sound','loud','speaker','music','construction','drilling','awaz','loudspeaker'],
    'sewage':      ['sewage','sewer','drain','blocked drain','stink','nali','naali','open drain'],
    'electricity': ['power cut','electric','current','wire','transformer','outage','bijli','no electricity','shock'],
    'tree':        ['tree','branch','fallen tree','blocking tree','ped','park','garden'],
}

def auto_tag(desc: str) -> str:
    d = desc.lower()
    for tag, words in KEYWORDS.items():
        if any(w in d for w in words):
            return tag
    return 'other'
