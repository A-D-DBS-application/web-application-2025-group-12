# app/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from . import db
from .models import Listing, User

bp = Blueprint("main", __name__)

# Simuleer ingelogde user:
CURRENT_USER_ID = 1

@bp.route("/")
def home():
    listings = Listing.query.order_by(Listing.created_at.desc()).all()
    return render_template("index.html", listings=listings)

@bp.route("/listings/new", methods=["GET", "POST"])
def create_listing():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        price = request.form.get("price", "").strip()

        if not title or not price:
            flash("Vul titel en prijs in.", "error")
            return redirect(url_for("main.create_listing"))

        try:
            price_val = float(price)
        except ValueError:
            flash("Prijs moet een getal zijn.", "error")
            return redirect(url_for("main.create_listing"))

        listing = Listing(title=title, price=price_val, user_id=CURRENT_USER_ID)
        db.session.add(listing)
        db.session.commit()
        flash("Listing aangemaakt!", "success")
        return redirect(url_for("main.home"))

    return render_template("new_listing.html")

@bp.route("/my-listings")
def my_listings():
    my_items = Listing.query.filter_by(user_id=CURRENT_USER_ID)\
                            .order_by(Listing.created_at.desc())\
                            .all()
    me = User.query.get(CURRENT_USER_ID)
    return render_template("my_listings.html", listings=my_items, me=me)
