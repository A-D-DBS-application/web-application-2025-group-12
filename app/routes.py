# app/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from . import db
from .models import Ground, Company, Match

bp = Blueprint("main", __name__)

# Simuleer ingelogde company:
CURRENT_COMPANY_ID = 1

@bp.route("/")
def home():
    # order by id desc (schema doesn't define a created_at column)
    grounds = Ground.query.order_by(Ground.id.desc()).all()
    return render_template("index.html", grounds=grounds)

@bp.route("/grounds/new", methods=["GET", "POST"])
def create_ground():
    if request.method == "POST":
        # fields matching DB schema: location, m2, budget, subdivision_type, owner, soil
        location = request.form.get("location", "").strip()
        m2 = request.form.get("m2", "").strip()
        budget = request.form.get("budget", "").strip()
        subdivision_type = request.form.get("subdivision_type", "").strip() or "unknown"
        owner = request.form.get("owner", "").strip() or ""
        soil = request.form.get("soil", "").strip() or "unknown"

        if not location or not m2 or not budget:
            flash("Please provide location, area (m2) and budget.", "error")
            return redirect(url_for("main.create_ground"))

        try:
            m2_val = int(m2)
            budget_val = float(budget)
        except ValueError:
            flash("Area and budget must be numeric.", "error")
            return redirect(url_for("main.create_ground"))

        ground = Ground(
            location=location,
            m2=m2_val,
            budget=budget_val,
            subdivision_type=subdivision_type,
            owner=owner,
            soil=soil,
        )
        db.session.add(ground)
        db.session.commit()
        flash("Ground added!", "success")
        return redirect(url_for("main.home"))

    return render_template("new_listing.html")

@bp.route("/my-company")
def my_company():
    company = Company.query.get(CURRENT_COMPANY_ID)
    company_grounds = (
        Ground.query.join(Match)
        .filter(Match.company_id == CURRENT_COMPANY_ID)
        # Ground model does not have created_at in the current schema — order by id instead
        .order_by(Ground.id.desc())
        .all()
    )
    return render_template("my_listings.html", grounds=company_grounds, company=company)
