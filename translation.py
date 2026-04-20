import http.client
import json

RAPIDAPI_KEY = "79115cebe8msh7aeb0698c33cb2bp140b6cjsn20d3c311c6f4"
RAPIDAPI_HOST = "deep-translate1.p.rapidapi.com"

def translate_text(text: str, target_lang: str, source_lang: str = "en") -> str:
    """Translates text using Deep Translate API via RapidAPI."""
    try:
        conn = http.client.HTTPSConnection(RAPIDAPI_HOST)
        payload = json.dumps({
            "q": text,
            "source": source_lang,
            "target": target_lang
        })
        headers = {
            'x-rapidapi-key': RAPIDAPI_KEY,
            'x-rapidapi-host': RAPIDAPI_HOST,
            'Content-Type': "application/json"
        }
        conn.request("POST", "/language/translate/v2", payload, headers)
        res = conn.getresponse()
        data = res.read()
        result = json.loads(data.decode("utf-8"))
        
        return result.get("data", {}).get("translations", {}).get("translatedText", text)
    except Exception:
        return text
