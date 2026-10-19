#!/usr/bin/env python3
"""Generate the call's voice clips with ElevenLabs text-to-speech (standard library only).

    export ELEVENLABS_API_KEY=...        # never paste the key into chat or the page
    python3 voice-clips/generate.py --dry-run   # list the clips, no key needed
    python3 voice-clips/generate.py             # create them in voice-clips/audio/

Clips that already exist are skipped, so it is safe to re-run after a failure.
Chunks mirror SCRIPT in the artifact's call.html; the *emphasis* markers are dropped from the audio.
"""
import json, os, sys, time, urllib.error, urllib.request

USER_VOICE = "FCdKzv68Ofr4VUDcZXIy"
AGENTS = {  # slug: (voice id, vent-page data-agent index)
    "roaster": ("gE0owC0H9C8SzfDyIUtB", 0),
    "ride-or-die": ("imUL0PI6vneM0Ei5YNAz", 1),
    "calm-sibling": ("4tRn1lSkEn13EVTuqb0g", 2),
}
MODEL = os.environ.get("ELEVENLABS_MODEL", "eleven_multilingual_v2")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio")

SCRIPT = [
    ("u", ["Okay so… my package got stolen.", "Like, it says delivered.", "There’s literally a photo of it sitting in my lobby."]),
    ("a", ["Wait.", "They took a photo of it in your lobby…", "and it’s not there?"]),
    ("u", ["No!", "I went down like ten minutes later", "and it was just gone."]),
    ("a", ["What???", "You already tried your best going downstairs!"]),
    ("u", ["And this is the third time this month.", "I’m so done."]),
    ("a", ["Third time?", "Then it’s probably not a mistake,", "there might be theft happening."]),
    ("u", ["The seller’s not gonna do anything.", "I just want to know who did this."]),
]

def jobs():
    n = 0
    for who, chunks in SCRIPT:
        for text in chunks:
            n += 1
            if who == "u":
                yield f"{n:02d}-user.mp3", USER_VOICE, text
            else:
                for slug, (vid, _) in AGENTS.items():
                    yield f"{n:02d}-{slug}.mp3", vid, text

def synth(key, voice, text):
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_128",
        data=json.dumps({"text": text, "model_id": MODEL}).encode(),
        headers={"xi-api-key": key, "Content-Type": "application/json", "Accept": "audio/mpeg"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()

def main():
    todo = list(jobs())
    if "--dry-run" in sys.argv:
        for name, voice, text in todo:
            print(f"{name:24} {voice}  {text}")
        print(f"{len(todo)} clips")
        return
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        sys.exit("Set ELEVENLABS_API_KEY first (export ELEVENLABS_API_KEY=...).")
    os.makedirs(OUT, exist_ok=True)
    for i, (name, voice, text) in enumerate(todo, 1):
        path = os.path.join(OUT, name)
        if os.path.exists(path):
            print(f"[{i}/{len(todo)}] skip {name}")
            continue
        for attempt in range(4):
            try:
                data = synth(key, voice, text)
                break
            except urllib.error.HTTPError as e:
                if e.code in (429, 500, 502, 503) and attempt < 3:
                    time.sleep(2 ** (attempt + 1)); continue
                sys.exit(f"{name}: HTTP {e.code} {e.read().decode(errors='replace')[:300]}")
        open(path, "wb").write(data)
        print(f"[{i}/{len(todo)}] {name}")
    print("Done. Clips are in", OUT)

main()
