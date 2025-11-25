import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from supabase import create_client, Client
from dotenv import load_dotenv

# -----------------------------
# Laad .env variabelen
# -----------------------------
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL of SUPABASE_KEY ontbreekt in .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
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
def parse_m2(surface_text: str | None) -> int | None:
    """Haalt de m² als integer uit bv. '975m²' of '975 m2'."""
    if not surface_text:
        return None
    digits = "".join(ch for ch in surface_text if ch.isdigit())
    return int(digits) if digits else None


def parse_budget(price_text: str | None) -> int | None:
    """Haalt het bedrag als integer uit bv. '€ 149.000' -> 149000."""
    if not price_text:
        return None
    digits = "".join(ch for ch in price_text if ch.isdigit())
    return int(digits) if digits else None


# -----------------------------
# Hoofd-scrape functie
# -----------------------------
def scrape_vansweevelt() -> list[dict]:
    """Haalt bouwgronden op en mapt ze naar de kolommen van 'ground'."""

    headers = {"User-Agent": "Mozilla/5.0"}

    resp = requests.get(URL, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    coords = data.get("coordinaten", [])
    print(f"Aantal items in 'coordinaten': {len(coords)}")

    results: list[dict] = []

    for item in coords:
        # reclame-tegels e.d. hebben tellen = 0
        if item.get("tellen") != 1:
            continue

        chunk_html = item.get("chunk", "")
        soup = BeautifulSoup(chunk_html, "html.parser")

        # detail-url (niet in DB, maar handig voor debug)
        a_tag = soup.find("a", class_="pand-link")
        detail_url = (
            urljoin("https://www.vansweevelt.be", a_tag["href"])
            if a_tag and a_tag.has_attr("href")
            else None
        )

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
            # print(f"Skipping item zonder m2/budget: title={title}")
            continue

        location_val = city or street or "onbekend"

        record = {
            "location": location_val,
            "m2": m2_val,
            "budget": budget_val,
            "subdivision_type": grond_type or "onbekend",
            "owner": "Vansweevelt",
            # detail_url zou extra kolom vereisen, dus laten we weg
        }

        results.append(record)

    return results


# -----------------------------
# Opslaan in Supabase
# -----------------------------
def save_to_supabase(plots: list[dict]) -> None:
    if not plots:
        print("Geen plots om op te slaan.")
        return

    # Eenvoudige insert: voor een MVP is dit prima.
    # Als je duplicaten wilt vermijden, kun je eerst de tabel leegmaken
    # of een unieke key toevoegen.
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



