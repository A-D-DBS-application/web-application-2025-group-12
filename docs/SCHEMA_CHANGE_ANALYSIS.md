# Schema Wijziging Analyse

## ❌ PROBLEEM: Hun voorgestelde model is NIET compatibel

### Kritieke Issues:

1. **Match relaties zijn 1-op-1 gemaakt**
   ```python
   # HUN voorstel:
   client.match = db.relationship("Match", uselist=False)  # ❌ 1 client = 1 match
   ground.match = db.relationship("Match", uselist=False)  # ❌ 1 grond = 1 match
   ```
   
   **Gevolg:** 
   - Client kan maar naar 1 grond kijken tegelijk
   - Grond kan maar met 1 client gematcht worden
   - Hele matching algoritme werkt niet meer!

2. **Veldnamen botsen met bestaande code**
   - `id` → `company_id`, `client_id`, etc.
   - Breekt 100+ referenties in routes.py
   - Breekt alle templates ({{ company.id }})
   - Breekt session management

3. **Inconsistente naamgeving**
   - `budget` → `price` (maar preferences heeft nog `min_budget`/`max_budget`)
   - `owner` → `provider` (beide zelfde betekenis)

## ✅ OPLOSSING: Hybride model (zie PROPOSED_MODEL_HYBRID.py)

### Wat behouden we van hun voorstel:
- ✅ `{table}_id` naming convention (professioneler)
- ✅ `UserMixin` voor Company (Flask-Login ready)
- ✅ Expliciete relationship namen
- ✅ `BigInteger` i.p.v. `Integer` voor primary keys

### Wat we MOETEN aanpassen:
- ❌ Match moet **many-to-many** blijven (geen `unique=True` op FKs)
- ❌ Ground moet **meerdere matches** kunnen hebben
- ❌ Preferences moet **meerdere matches** kunnen hebben
- ✅ `budget` blijft `budget` (niet `price`)

## 📊 Impact Assessment

### Wijzigingen nodig in code:
1. **models.py** - 5 models herschrijven
2. **routes.py** - ~50 query aanpassingen (`id` → `{table}_id`)
3. **templates** - ~30 template variabele aanpassingen
4. **database schema** - volledige migratie nodig
5. **session management** - blijft hetzelfde (gebruikt al `company_id`)

### Geschatte effort:
- **Database migratie:** 1 uur (script schrijven + testen)
- **Models update:** 30 min
- **Routes update:** 2-3 uur (veel zoek-vervang werk)
- **Templates update:** 1 uur
- **Testing:** 2 uur
- **TOTAAL:** ~7 uur werk

## 🎯 Aanbeveling

**OPTIE A: Niet doen (recommended)**
- Huidige model werkt perfect
- Geen functionele voordelen
- Veel risico op bugs tijdens migratie
- Projectdeadline risico

**OPTIE B: Gedeeltelijke adoptie**
- Alleen `{table}_id` naming convention overnemen
- Match structuur NIET aanpassen
- Laag risico, medium effort (~3 uur)

**OPTIE C: Volledige migratie**
- Gebruik hybride model (PROPOSED_MODEL_HYBRID.py)
- Match blijft many-to-many
- Hoog risico, veel werk (~7 uur)

## ⚠️ Waarschuwing

Als jullie docent/begeleider eist dat Match 1-op-1 wordt:
- Leg uit dat dit de functionaliteit breekt
- Toon deze analyse
- Vraag om verduidelijking van requirements

**Een matching platform waar 1 client maar 1 match kan hebben is functioneel zinloos!**
