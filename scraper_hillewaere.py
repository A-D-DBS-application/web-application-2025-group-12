import os
import re
import json
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from supabase import create_client, Client
from typing import List, Dict, Optional

# -----------------------------
# .env laden (SUPABASE_URL, SUPABASE_KEY)
# -----------------------------
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    supabase = None

TABLE_NAME = "ground"

# -----------------------------
# Hillewaere endpoint
# -----------------------------
# TODO: vul hier de echte URL in van de request die je in de Network-tab ziet
HILLEWAERE_URL = "https://www.hillewaere-vastgoed.be/vastgoed/gronden/te-koop?markers=1&view=split"



# -----------------------------
# Helpers
# -----------------------------
def parse_js_array_from_response(text: str):
    """
    Response ziet eruit als:
      esignMap.overviewMap([ { ... }, { ... } ]);
    We knippen gewoon het stuk tussen de eerste '[' en de laatste ']' eruit.
    """
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Kon geen JSON-array vinden in Hillewaere response")
    json_str = text[start : end + 1]
    return json.loads(json_str)


def parse_budget_from_subtitle(subtitle: Optional[str]) -> Optional[int]:
    """
    subtitle: bv. '€ 275 000' -> 275000
    """
    if not subtitle:
        return None
    digits = "".join(ch for ch in subtitle if ch.isdigit())
    return int(digits) if digits else None


def parse_m2_from_url(url: str) -> Optional[int]:
    """
    Probeer m² uit de URL-slug te halen.
    Voorbeelden:
    - .../bouwgrond-van-1632-m2-...
    - .../uniek-bouwperceel-van-ca-6035m2-...
    - .../bouwgrond-van-30-are-...
    """
    if not url:
        return None

    # Neem de slug (laatste stuk na '/')
    slug = url.rstrip("/").split("/")[-1]
    # vervang '-' door spaties zodat regex makkelijker matcht
    slug_spaced = slug.replace("-", " ")

    # eerst zoeken naar '1234 m2' of '1234m2'
    m = re.search(r"(\d+)\s*m2", slug_spaced, flags=re.IGNORECASE)
    if m:
        return int(m.group(1))

    # dan zoeken naar '30 are'
    m = re.search(r"(\d+)\s*are", slug_spaced, flags=re.IGNORECASE)
    if m:
        return int(m.group(1)) * 100  # 1 are = 100 m²

    return None


def parse_address_and_city_from_description(desc_html: Optional[str]):
    """
    description HTML ziet eruit als:
      <p>Straat 123<br>2400 Mol</p><p>...</p>
    We willen:
      address = 'Straat 123'
      city    = 'Mol'
    """
    if not desc_html:
        return None, None

    soup = BeautifulSoup(desc_html, "html.parser")
    p = soup.find("p")
    if not p:
        return None, None

    # Split op regels in de eerste <p>
    lines = list(p.stripped_strings)
    # Verwachting:
    #   lines[0] = 'Steenweg Op Mol 202 - 9B'
    #   lines[1] = '2360 Oud-Turnhout'
    address = lines[0] if len(lines) >= 1 else None
    city_line = lines[1] if len(lines) >= 2 else None

    city = None
    if city_line:
        parts = city_line.split(" ", 1)
        if len(parts) == 2:
            # postcode = parts[0]
            city = parts[1]
        else:
            city = city_line

    return address, city


# -----------------------------
# Normalisatie van 1 item
# -----------------------------
def normalize_hillewaere_item(item: Dict) -> Optional[Dict]:
    """
    Zet één Hillewaere-object om naar een rij voor de 'ground' tabel.
    Verwachte keys (zoals in jouw voorbeeld):
      - id
      - title
      - subtitle (bevat prijs)
      - lat, lng
      - img
      - url
      - sold (bool)
      - new (bool)
      - search_match (bool)
      - description (HTML)
    """

    # Sla verkochte gronden eventueel over
    if item.get("sold"):
        return None

    subtitle = item.get("subtitle")
    budget_val = parse_budget_from_subtitle(subtitle)

    url = item.get("url")
    m2_val = parse_m2_from_url(url or "")

    desc_html = item.get("description")
    address, city = parse_address_and_city_from_description(desc_html)

    # Als m² of budget ontbreken en je DB heeft NOT NULL, dan skippen:
    if m2_val is None or budget_val is None:
        # als je liever toch inschuift, haal deze return weg
        return None

    record = {
        "location": city or "onbekend",
        "address": address or "",
        "m2": m2_val,
        "budget": budget_val,
        "subdivision_type": "development_plot",  # alles is grond
        "owner": "Hillewaere",
        "provider": "Hillewaere",
        #"detail_url": url,
        "image_url": item.get("img"),
        "image_url": item.get("img"),
        # Als je ook lat/lng kolommen hebt in DB, kun je die hier toevoegen:
        # "lat": float(item["lat"]),
        # "lng": float(item["lng"]),
    }

    return record


# -----------------------------
# Hoofd-scrape functie
# -----------------------------
def scrape_hillewaere() -> List[Dict]:
    headers = {"User-Agent": "Mozilla/5.0"}

    resp = requests.get(HILLEWAERE_URL, headers=headers, timeout=15)
    resp.raise_for_status()

    # Response is GEEN pure JSON, maar JS-functie-aanroep
    items = parse_js_array_from_response(resp.text)
    print(f"Aantal items in Hillewaere array: {len(items)}")

    results: List[Dict] = []
    for item in items:
        record = normalize_hillewaere_item(item)
        if record:
            results.append(record)

    return results


# -----------------------------
# Opslaan in Supabase
# -----------------------------
def save_to_supabase(plots: List[Dict]) -> None:
    if not supabase:
        print("Supabase client niet geconfigureerd (check .env).")
        return

    if not plots:
        print("Geen plots om op te slaan.")
        return
    
    supabase.table(TABLE_NAME).delete().eq("owner", "Hillewaere").execute()

    response = supabase.table(TABLE_NAME).insert(plots).execute()
    print("Supabase insert response:", response)


# -----------------------------
# Script entrypoint
# -----------------------------
if __name__ == "__main__":
    plots = scrape_hillewaere()
    print(f"{len(plots)} gescrapete Hillewaere-bouwgronden (na filter)\n")

    for p in plots:
        print(p)

    save_to_supabase(plots)
