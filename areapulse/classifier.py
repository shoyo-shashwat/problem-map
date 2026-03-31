KEYWORDS = {
    'pothole': ['pothole', 'road', 'crater', 'hole', 'bump', 'damaged road', 'broken road', 'khada'],
    'water': ['water', 'leak', 'pipe', 'flood', 'drainage', 'sewage', 'naali', 'pani', 'overflow'],
    'garbage': ['garbage', 'waste', 'trash', 'kachra', 'dump', 'litter', 'smell', 'refuse', 'filth'],
    'streetlight': ['light', 'streetlight', 'lamp', 'dark', 'bulb', 'electric pole', 'batti'],
    'traffic': ['traffic', 'signal', 'jam', 'congestion', 'accident', 'speed', 'zebra', 'crossing'],
    'noise': ['noise', 'sound', 'loud', 'speaker', 'music', 'construction', 'drilling', 'awaz'],
    'sewage': ['sewage', 'sewer', 'drain', 'blocked', 'overflow', 'stink', 'manhole', 'nali'],
    'electricity': ['power', 'electric', 'current', 'wire', 'transformer', 'outage', 'bijli'],
    'tree': ['tree', 'branch', 'fallen', 'blocking', 'park', 'garden', 'ped'],
}

def auto_tag(desc: str) -> str:
    d = desc.lower()
    for tag, words in KEYWORDS.items():
        if any(w in d for w in words):
            return tag
    return 'other'