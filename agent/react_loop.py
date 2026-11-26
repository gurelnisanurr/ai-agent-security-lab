import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

from tools.files import read_file

load_dotenv()

MODEL = "openai/gpt-oss-120b"
TEMPERATURE = 0
SEED = 42
MAX_STEPS = 15
TIMEOUT_SEC = 120
TRACE_FILE = Path("results/trace.jsonl")

SYSTEM_PROMPT = """Sen bir dosya okuma asistanısın.
Her yanıtını SADECE geçerli bir JSON nesnesi olarak ver, başka metin ekleme.

Araç çağırmak için:
{"arac": "read_file", "argumanlar": {"path": "dosya_adi"}}

Görev bittiğinde:
{"arac": "FINAL", "argumanlar": {"final": "kullanıcıya verilecek cevap"}}

Kullanılabilir araçlar:
- read_file(path): çalışma alanındaki bir dosyanın içeriğini okur.
"""

client = Groq(api_key=os.environ["GROQ_API_KEY"])


def simdi():
    return datetime.now(timezone.utc).isoformat()


def iz_yaz(kayit: dict):
    TRACE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with TRACE_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(kayit, ensure_ascii=False) + "\n")


def run_agent(gorev: str) -> str:
    kosu_id = str(uuid.uuid4())
    baslangic = time.time()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": gorev},  # T1: kullanıcı görevi
    ]

    for adim in range(1, MAX_STEPS + 1):
        if time.time() - baslangic > TIMEOUT_SEC:
            iz_yaz({"zaman": simdi(), "kosu_id": kosu_id, "adim": adim, "karar": "ZAMAN_ASIMI"})
            return "ZAMAN_ASIMI"

        resp = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=TEMPERATURE,
            seed=SEED,
        )
        icerik = resp.choices[0].message.content or ""
        token = resp.usage.total_tokens

        try:
            eylem = json.loads(icerik)
            arac = eylem["arac"]
            argumanlar = eylem.get("argumanlar", {})
        except (json.JSONDecodeError, KeyError, TypeError):
            iz_yaz({"zaman": simdi(), "kosu_id": kosu_id, "adim": adim,
                    "arac": None, "argumanlar": None, "guven": "T1",
                    "karar": "GECERSIZ_JSON", "token": token})
            messages.append({"role": "assistant", "content": icerik})
            messages.append({"role": "user",
                             "content": "Yanıtın geçerli JSON değil. Sadece JSON nesnesi ver."})
            continue

        if arac == "FINAL":
            iz_yaz({"zaman": simdi(), "kosu_id": kosu_id, "adim": adim,
                    "arac": "FINAL", "argumanlar": argumanlar, "guven": "T1",
                    "karar": "BITTI", "token": token})
            return argumanlar.get("final", "")

        if arac == "read_file":
            try:
                sonuc = read_file(**argumanlar)
                karar = "IZIN"
            except Exception as e:
                sonuc = f"HATA: {e}"
                karar = "HATA"
        else:
            sonuc = f"HATA: bilinmeyen araç '{arac}'"
            karar = "HATA"

        iz_yaz({"zaman": simdi(), "kosu_id": kosu_id, "adim": adim,
                "arac": arac, "argumanlar": argumanlar, "guven": "T1",
                "karar": karar, "token": token})

        # Araç çıktısı dış veridir (T3), modele bu etiketle verilir.
        messages.append({"role": "assistant", "content": icerik})
        messages.append({"role": "user", "content": f"Araç sonucu (dış veri, T3):\n{sonuc}"})

    iz_yaz({"zaman": simdi(), "kosu_id": kosu_id, "adim": MAX_STEPS, "karar": "ADIM_SINIRI"})
    return "ADIM_SINIRI"