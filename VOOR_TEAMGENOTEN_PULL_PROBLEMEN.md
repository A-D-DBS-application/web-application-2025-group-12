# 🚨 Fix: Niet de juiste main branch?

## Het probleem:
Jullie feature branches zijn gebaseerd op OUDE commits vóór de schema fix!

## ✅ Oplossing (kies je situatie):

### 📍 Situatie 1: Je werkt op een FEATURE branch
```bash
# 1. Check op welke branch je bent
git branch --show-current

# 2. Haal laatste main op
git fetch origin

# 3. Update je branch met nieuwe main
git rebase origin/main

# 4. Als er conflicts zijn, los ze op en doe:
git rebase --continue

# 5. Force push je geüpdatete branch
git push --force-with-lease origin [JOUW-BRANCH-NAAM]
```

### 📍 Situatie 2: Je werkt op MAIN direct
```bash
# 1. Ga naar main
git checkout main

# 2. Haal laatste versie op
git pull origin main

# 3. Reset je database!
python scripts/reset_database.py
```

### 📍 Situatie 3: Je weet niet zeker wat te doen
```bash
# 1. Check je huidige status
git status

# 2. Check welke branch
git branch --show-current

# 3. Als het MAIN is:
git pull origin main
python scripts/reset_database.py

# 4. Als het een FEATURE branch is:
git fetch origin
git rebase origin/main
```

## 🎯 Wat moet je zien na de fix:

Als je `git log -1` doet, moet je zien:
```
86c5e2a 🔧 Fix schema.sql: Match table nu consistent met models.py
```

## ⚠️ BELANGRIJK na pull/rebase:
**ALTIJD database resetten:**
```bash
python scripts/reset_database.py
```

Want de schema.sql is veranderd!
