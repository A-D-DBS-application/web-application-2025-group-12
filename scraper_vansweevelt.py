import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from supabase import create_client, Client
from dotenv import load_dotenv
from typing import Optional, List, Dict

# -----------------------------
# Laad .env variabelen
# -----------------------------
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# If Supabase credentials are not provided, avoid raising at import time so
# the scraper parser can still be used locally. The save_to_supabase function
# will check and error if credentials are missing.
if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    supabase = None

TABLE_NAME = "ground"

# -----------------------------
# Scrape instellingen
# -----------------------------
URL = (
    "https://www.vansweevelt.be/panden-ophalen-v4.json"
    "?method=GET&page=1&paginaId=2&pagina=https%3A%2F%2Fwww.vansweevelt.be%2Fte-koop"
    "&project=0&investeren=0&purpose=1&weergave=galerij&query=0%3D&format=json"
    "&zoekterm=&type=1&slpk=Slaapkamers&radius=&staat=&charmeur=&cat=28"
    "&prijs%5Bmin%5D=&prijs%5Bmax%5D=&sort="
)


# -----------------------------
# Helper-functies
# -----------------------------
def parse_m2(surface_text: Optional[str]) -> Optional[int]:
    """Haalt de m² als integer uit bv. '975m²' of '975 m2'."""
    if not surface_text:
        return None
    digits = "".join(ch for ch in surface_text if ch.isdigit())
    return int(digits) if digits else None


def parse_budget(price_text: Optional[str]) -> Optional[int]:
    """Haalt het bedrag als integer uit bv. '€ 149.000' -> 149000."""
    if not price_text:
        return None
    digits = "".join(ch for ch in price_text if ch.isdigit())
    return int(digits) if digits else None


# -----------------------------
# Hoofd-scrape functie
# -----------------------------
def scrape_vansweevelt() -> List[Dict]:
    """Haalt bouwgronden op en mapt ze naar de kolommen van 'ground'."""

    headers = {"User-Agent": "Mozilla/5.0"}

    resp = requests.get(URL, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    coords = data.get("coordinaten", [])
    print(f"Aantal items in 'coordinaten': {len(coords)}")

    results: List[Dict] = []

    for item in coords:
        # reclame-tegels e.d. hebben tellen = 0
        if item.get("tellen") != 1:
            continue

        chunk_html = item.get("chunk", "")
        soup = BeautifulSoup(chunk_html, "html.parser")

        # detail-url (niet in DB, maar handig voor debug / clicks)
        a_tag = soup.find("a", class_="pand-link")
        detail_url = (
            urljoin("https://www.vansweevelt.be", a_tag["href"])
            if a_tag and a_tag.has_attr("href")
            else None
        )

        # Try to find a thumbnail or hero image in the chunk HTML
        img_tag = soup.find("img")
        image_url = None

        if img_tag:
            src = (
                img_tag.get("data-src")
                or img_tag.get("data-srcset")
                or img_tag.get("src")
            )
            if src:
                image_url = urljoin("https://www.vansweevelt.be", src)

        # prijs
        price_div = soup.find("div", class_="slider-bedrag")
        price_text = price_div.get_text(strip=True) if price_div else None
        budget_val = parse_budget(price_text)

        # titel + stad
        h3 = soup.find("h3")
        title = h3.get_text(strip=True) if h3 else None

        grond_type = None
        city = None
        if title and " - " in title:
            grond_type, city = [p.strip() for p in title.split(" - ", 1)]
        else:
            grond_type = title

        # straat (optioneel)
        h4 = soup.find("h4")
        street = h4.get_text(strip=True) if h4 else None

        # oppervlakte
        icons_div = soup.find("div", class_="icons")
        surface_text = icons_div.get_text(" ", strip=True) if icons_div else None
        m2_val = parse_m2(surface_text)

        # Kolommen m2 en budget zijn NOT NULL in DB -> skip als we ze niet hebben
        if m2_val is None or budget_val is None:
            continue

        # Separate location (city) and address (street + number)
        location_val = city or "onbekend"
        address_val = street or ""

        # Map to valid subdivision types (default to development_plot for scraped grounds)
        subdivision_mapping = {
            "bouwgrond": "development_plot",
            "grond": "development_plot",
            "plot": "development_plot",
        }
        subdivision_key = (grond_type or "").lower()
        subdivision_val = subdivision_mapping.get(subdivision_key, "development_plot")

        record = {
            "location": location_val,
            "address": address_val,
            "m2": m2_val,
            "budget": budget_val,
            "subdivision_type": subdivision_val,
            "owner": "Vansweevelt",
            "provider": None,        # Scraped grounds not tied to a company
            "detail_url": detail_url,
            "image_url": image_url,
            "photo_url": image_url,  # Use scraped image as photo
        }

        results.append(record)

    return results


# -----------------------------
# Opslaan in Supabase
# -----------------------------
def save_to_supabase(plots: List[Dict]) -> None:
    if not plots:
        print("Geen plots om op te slaan.")
        return

    response = supabase.table(TABLE_NAME).insert(plots).execute()
    print("Supabase insert response:", response)


# -----------------------------
# Script entrypoint
# -----------------------------
if __name__ == "__main__":
    plots = scrape_vansweevelt()
    print(f"{len(plots)} gescrapete bouwgronden (na filter)\n")

    for p in plots:
        print(p)

    save_to_supabase(plots)










