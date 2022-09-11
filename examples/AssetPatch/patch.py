import json
import os
import time
import UnityPy
from googletrans import Translator

root = os.path.dirname(os.path.realpath(__file__))

def main():
    # load the original japanese localisation
    src = os.path.join(root, "522608825")
    e = UnityPy.load(src)
    # iterate over all localisation assets
    for cont, obj in e.container.items():
        # read the asset data
        data = obj.read()
        # get the localisation data
        script = json.loads(bytes(data.script)) # bytes wrapper to handle memoryview
        if hasattr(script, "infos"):
            continue
        print(data.name)
        # translate the localisation
        for entry in script["infos"]:
            entry["value"] = translate(entry["value"])
        # overwrite the original
        data.script = json.dumps(
            script, 
            ensure_ascii=False, indent=4
        ).encode("utf8")
        # apply the changes
        data.save()
    
    # save the modified Bundle as file
    with open(os.path.join(root, "522608825_patched"), "wb") as f:
        f.write(e.file.save())


# simple cache for already translated strings
# prevents requesting the same string multiple times
# therefore saving time and reducing the chance of being IP-blocked
TL_CACHE = {}
def translate(text):
    # check if the text is valid
    if not text.strip(" "):
        return text
    # check if the text was already translated once
    if text in TL_CACHE:
        return TL_CACHE[text]
    
    # actual google translation
    translator = Translator(service_urls=['translate.googleapis.com'])
    try:
        ret = translator.translate(text, "en", "ja").text
        TL_CACHE[text] = ret
        return ret
    except json.JSONDecodeError:
        input("DecodeError")
        return translate(text)
    except (ConnectionError, AttributeError) as e:
        print(e)
        time.sleep(1)
        return translate(text)

if __name__ == "__main__":
    main()
