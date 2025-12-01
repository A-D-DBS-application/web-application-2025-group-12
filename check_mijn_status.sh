#!/bin/bash
echo "🔍 DIAGNOSE SCRIPT"
echo "=================="
echo ""

echo "1️⃣ Op welke branch ben je?"
BRANCH=$(git branch --show-current)
echo "   → $BRANCH"
echo ""

echo "2️⃣ Laatste commit?"
git log -1 --oneline
echo ""

echo "3️⃣ Heb je de 3 belangrijke commits?"
echo "   Checking..."
HAS_MODELS=$(git log --oneline -20 | grep "32ff27c.*Update models.py" | wc -l)
HAS_RELATIES=$(git log --oneline -20 | grep "7e405ae.*relaties gefixt" | wc -l)
HAS_SCHEMA=$(git log --oneline -20 | grep "86c5e2a.*Fix schema.sql" | wc -l)

if [ "$HAS_MODELS" -gt 0 ] && [ "$HAS_RELATIES" -gt 0 ] && [ "$HAS_SCHEMA" -gt 0 ]; then
    echo "   ✅ JA - Je hebt alle 3 de fixes!"
else
    echo "   ❌ NEE - Je mist commits!"
    [ "$HAS_MODELS" -eq 0 ] && echo "      ❌ 32ff27c Update models.py"
    [ "$HAS_RELATIES" -eq 0 ] && echo "      ❌ 7e405ae relaties gefixt"
    [ "$HAS_SCHEMA" -eq 0 ] && echo "      ❌ 86c5e2a Fix schema.sql"
    echo "   → Doe: git pull origin main"
fi
echo ""

echo "4️⃣ Wat staat er in je Match model?"
if grep -A 10 "class Match" app/models.py | grep -q "client_id.*=.*db.Column"; then
    echo "   ✅ GOED - Match heeft client_id!"
else
    echo "   ❌ PROBLEEM - Match heeft geen client_id!"
fi
echo ""

echo "5️⃣ Wat staat er in je schema.sql match table?"
if grep -A 10 "CREATE TABLE.*match" db/schema.sql | grep -q "client_id.*INT NOT NULL"; then
    echo "   ✅ GOED - schema.sql match heeft client_id!"
else
    echo "   ❌ PROBLEEM - schema.sql match heeft geen client_id!"
fi
echo ""

echo "📋 SAMENVATTING:"
echo "================"
if [ "$HAS_MODELS" -gt 0 ] && [ "$HAS_RELATIES" -gt 0 ] && [ "$HAS_SCHEMA" -gt 0 ]; then
    echo "✅ Je code is up to date!"
    echo ""
    echo "💡 Als je TOCH nog errors hebt, reset je database:"
    echo "   python scripts/reset_database.py"
    echo "   python run.py"
else
    echo "❌ Je hebt NIET de laatste versie!"
    echo ""
    echo "💡 OPLOSSING:"
    echo "   git fetch origin"
    echo "   git reset --hard origin/main"
    echo "   python scripts/reset_database.py"
    echo "   python run.py"
fi
