try:
    from flask import (
        Flask,
        render_template,
        request,
        redirect,
        url_for,
        flash,
        session,
        make_response,
    )
    from flask_login import (
        LoginManager,
        login_user,
        logout_user,
        login_required,
        current_user,
    )
    from datetime import date
    from authlib.integrations.flask_client import OAuth
    import requests
    import secrets
    from server.web.user import User
    from server.database import DatabaseManager
    import server.config as config
    from server.connection.frame_receiver import receiver as frame_receiver_blueprint
    



except ImportError as e:
    print(f"Errore nel caricamento dei moduli in appWeb.py: {e}")


app = Flask(__name__)
app.register_blueprint(frame_receiver_blueprint)
# debug, per vedere se la rotta di
if config.VERBOSE:
    print("\n=== ROUTE REGISTRATE ===")
    for rule in app.url_map.iter_rules():
        print(f"   {rule.endpoint}: {rule.rule} {list(rule.methods)}")
    print("========================\n")


app.secret_key = config.SECRET_KEY
app.config["SESSION_COOKIE_SECURE"] = False  # False per debug
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_PERMANENT"] = False


# Database
db = DatabaseManager(config.DATABASE_PATH)

from server.process.access_tracker import access_tracker
access_tracker.set_db(db)



# login manager
login_manager = LoginManager()
login_manager.login_view = "login_page"
login_manager.init_app(app)

# OAuth setup
oauth = OAuth(app)
google = oauth.register(
    name="google",
    client_id=config.GOOGLE_CLIENT_ID,
    client_secret=config.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


@login_manager.user_loader
def load_user(user_id):
    return User(user_id)


@app.route("/login")
def login_page():
    if current_user.is_authenticated:
        print("Utente già loggato")
        return redirect(url_for("index"))
    return render_template("login.html")


@app.route("/auth/google")
def google_login():
    redirect_uri = url_for("callback", _external=True)
    session["nonce"] = secrets.token_urlsafe(16)
    print(redirect_uri)
    return google.authorize_redirect(redirect_uri, nonce=session["nonce"])


@app.route("/callback")
def callback():
    try:
        token = google.authorize_access_token()
        user_info = google.parse_id_token(token, nonce=session["nonce"])
        email = user_info.get("email")

        # Controlla se l'email è autorizzata
        if email not in config.AUTHORIZED_USERS:
            flash("Non sei autorizzato ad accedere.", "danger")
            return redirect(url_for("login_page"))

        user = User(email)
        login_user(user, remember=False)
        session["user_email"] = email
        session["user_name"] = user_info.get("name", email)

        flash(f"Benvenuto {email}!", "success")
        return redirect(url_for("index"))

    except Exception as e:
        print(f"Error during OAuth callback: {e}")
        flash("Errore durante l'autenticazione.", "danger")
        return redirect(url_for("login_page"))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    resp = make_response(redirect(url_for("login_page")))
    resp.set_cookie("remember_token", "", expires=0, max_age=0)
    flash("Logout effettuato con successo.", "info")
    return resp


# ============================================================================
# ROUTES
# ============================================================================
@app.route("/")
@login_required
def index():
    stats = {
        "total_plates": len(db.get_all_plates()),
        "recent_logs": db.get_access_history(limit=10),
    }
    return render_template("index.html", stats=stats)


@app.route("/plates")
@login_required
def plates():
    plates = db.get_all_plates()
    # print (plates)
    return render_template("plates.html", plates=plates)


@app.route("/add_plate", methods=["GET", "POST"])
@login_required
def add_plate():
    if request.method == "POST":
        plate = request.form["plate_number"].strip().upper()
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        role = request.form["role"]
        expiration = request.form["expiration_date"]

        if not plate or len(plate) < 6:
            flash("Numero targa non valido!", "danger")
            return render_template("add_plate.html")

        try:
            result = db.add_authorized_plate(
                plate, first_name, last_name, role, expiration
            )
            if result:
                flash(f"Targa {plate} aggiunta con successo!", "success")
            else:
                flash(f"Targa {plate} già esistente!", "warning")
            return redirect(url_for("plates"))
        except Exception as e:
            flash(f"Errore: {str(e)}", "danger")
            return render_template("add_plate.html")

    return render_template("add_plate.html")


@app.route("/edit_plate/<plate_number>", methods=["GET", "POST"])
@login_required
def edit_plate(plate_number):

    plate = db.get_plate(plate_number)
    if not plate:
        flash("Targa non trovata!", "danger")
        return redirect(url_for("plates"))

    if request.method == "POST":
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        role = request.form["role"]
        expiration = request.form["expiration_date"]
        try:
            db.update_plate(plate_number, first_name, last_name, role, expiration)
            flash("Targa aggiornata con successo!", "success")
            return redirect(url_for("plates"))
        except Exception as e:
            flash(f"Errore: {str(e)}", "danger")

    return render_template("edit_plate.html", plate=plate)


@app.route("/delete_plate/<plate_number>", methods=["POST"])
@login_required
def delete_plate(plate_number):

    try:
        db.remove_plate(plate_number)
        flash(f"Targa {plate_number} rimossa!", "warning")
    except Exception as e:
        flash(f"Errore: {str(e)}", "danger")

    return redirect(url_for("plates"))


@app.route("/logs")
@login_required
def logs():
    selected_date = request.args.get("selected_date", "").strip()
    today = date.today().isoformat()

    if not selected_date:
        selected_date = today

    # Solo accessi con status "authorized"
    all_logs = db.get_access_history(
        date=selected_date,
        status="authorized"
    )

    return render_template("logs.html", logs=all_logs, selected_date=selected_date, today=today)





@app.route("/logs/storico")
@login_required
def logs_storico():
    today = date.today().isoformat()

    filters = {
        "plate_number": request.args.get("plate_number", "").strip().upper(),
        "first_name":   request.args.get("first_name", "").strip(),
        "last_name":    request.args.get("last_name", "").strip(),
        "role":         request.args.get("role", "").strip(),
        "status":       request.args.get("status", "").strip(),
        "date_single":  request.args.get("date_single", "").strip(),
        "date_from":    request.args.get("date_from", "").strip(),
        "date_to":      request.args.get("date_to", "").strip(),
        "limit":        request.args.get("limit", "100").strip(),
    }

    limit_val = int(filters["limit"]) if filters["limit"].isdigit() else 100

    all_logs = db.get_access_history_advanced(
        plate_number=filters["plate_number"] or None,
        first_name=filters["first_name"] or None,
        last_name=filters["last_name"] or None,
        role=filters["role"] or None,
        status=filters["status"] or None,
        date_single=filters["date_single"] or None,
        date_from=filters["date_from"] or None,
        date_to=filters["date_to"] or None,
        limit=limit_val,
    )

    return render_template("logs_storico.html", logs=all_logs, filters=filters, today=today)


@app.route("/logs/storico/delete", methods=["POST"])
@login_required
def delete_selected_logs():
    """Elimina i log selezionati per ID"""
    try:
        log_ids = request.form.getlist("log_ids")
        if not log_ids:
            flash("Nessun log selezionato.", "warning")
            return redirect(url_for("logs_storico"))

        log_ids = [int(id) for id in log_ids if id.isdigit()]
        deleted = db.delete_logs_by_ids(log_ids)
        flash(f"Eliminati {deleted} log con successo.", "success")
    except Exception as e:
        flash(f"Errore durante l'eliminazione: {str(e)}", "danger")

    return redirect(url_for("logs_storico"))


@app.route("/logs/storico/export")
@login_required
def export_logs_filtered():
    """Esporta i log filtrati in CSV"""
    try:
        from datetime import datetime as dt
        from flask import send_file
        import tempfile, os, csv

        today = date.today().isoformat()
        filters = {
            "plate_number": request.args.get("plate_number", "").strip().upper(),
            "first_name":   request.args.get("first_name", "").strip(),
            "last_name":    request.args.get("last_name", "").strip(),
            "role":         request.args.get("role", "").strip(),
            "status":       request.args.get("status", "").strip(),
            "date_single":  request.args.get("date_single", "").strip(),
            "date_from":    request.args.get("date_from", "").strip(),
            "date_to":      request.args.get("date_to", "").strip(),
            "limit":        request.args.get("limit", "0").strip(),
        }
        limit_val = int(filters["limit"]) if filters["limit"].isdigit() else 0

        logs = db.get_access_history_advanced(
            plate_number=filters["plate_number"] or None,
            first_name=filters["first_name"] or None,
            last_name=filters["last_name"] or None,
            role=filters["role"] or None,
            status=filters["status"] or None,
            date_single=filters["date_single"] or None,
            date_from=filters["date_from"] or None,
            date_to=filters["date_to"] or None,
            limit=limit_val,
        )

        if not logs:
            flash("Nessun log da esportare con i filtri selezionati.", "warning")
            return redirect(url_for("logs_storico"))

        timestamp = dt.now().strftime("%Y%m%d_%H%M%S")
        filename = f"storico_accessi_{timestamp}.csv"
        filepath = os.path.join(tempfile.gettempdir(), filename)

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Targa", "Data e Ora", "Stato", "Evento", "Nome", "Cognome", "Ruolo"])
            for row in logs:
                writer.writerow([
                    row["id"],
                    row["plate_number"],
                    row["timestamp"],
                    row["status"],
                    row.get("event", ""),
                    row.get("first_name", ""),
                    row.get("last_name", ""),
                    row.get("role", ""),
                ])

        return send_file(filepath, mimetype="text/csv", as_attachment=True, download_name=filename)

    except Exception as e:
        flash(f"Errore durante l'esportazione: {str(e)}", "danger")
        return redirect(url_for("logs_storico"))



@app.route("/logs/analytics")
@login_required
def logs_analytics():
    from datetime import date, timedelta

    today = date.today().isoformat()
    default_start = (date.today() - timedelta(days=6)).isoformat()

    start_date = request.args.get("start_date", default_start).strip()
    end_date   = request.args.get("end_date", today).strip()

    # ── Dati grafici esistenti ──────────────────────────────────────────────
    dati_per_giorno = db.get_accessi_per_giorno(start_date, end_date)
    dati_stato      = db.get_accessi_per_stato(start_date, end_date)
    dati_orario     = db.get_accessi_per_ora(start_date, end_date)
    dati_top_targhe = db.get_top_targhe(start_date, end_date, limit=10)
    dati_trend      = db.get_trend_per_stato(start_date, end_date)

    # ── Nuovi dati entrate/uscite ───────────────────────────────────────────
    kpi_ev          = db.get_kpi_entrate_uscite(start_date, end_date)
    dati_distrib_ev = db.get_distribuzione_entrate_uscite(start_date, end_date)
    dati_flusso_ore = db.get_flusso_orario_entrate_uscite(start_date, end_date)
    dati_saldo      = db.get_saldo_giornaliero(start_date, end_date)

    # ── KPI aggregati totali ────────────────────────────────────────────────
    kpi = {
        "total":          dati_stato.get("authorized", 0)
                        + dati_stato.get("not_authorized", 0)
                        + dati_stato.get("expired", 0),
        "authorized":     dati_stato.get("authorized", 0),
        "not_authorized": dati_stato.get("not_authorized", 0),
        "expired":        dati_stato.get("expired", 0),
        # nuovi
        "entrate":        kpi_ev.get("entrate", 0),
        "uscite":         kpi_ev.get("uscite", 0),
        "presenti":       kpi_ev.get("presenti", 0),
    }

    return render_template(
        "logs_analytics.html",
        start_date=start_date,
        end_date=end_date,
        today=today,
        kpi=kpi,
        # dati grafici originali
        dati_per_giorno=dati_per_giorno,
        dati_stato=dati_stato,
        dati_orario=dati_orario,
        dati_top_targhe=dati_top_targhe,
        dati_trend=dati_trend,
        # dati nuovi grafici entry/exit
        dati_distrib_ev=dati_distrib_ev,
        dati_flusso_ore=dati_flusso_ore,
        dati_saldo=dati_saldo,
    )




# ====================================
# funzionalità da implementare ancora
# ====================================
@app.route("/service/enable", methods=["POST"])
@login_required
def enable_service():
    try:
        resp = requests.post(
            "http://localhost:5000/api/service/set", json={"enabled": True}
        )
        if resp.ok:
            flash("Servizio attivato!", "success")
        else:
            flash(f"Errore attivando servizio: {resp.text}", "danger")
    except Exception as e:
        flash(f"Errore: {str(e)}", "danger")
    return redirect(url_for("index"))


# @app.route("/service/disable", methods=['POST'])
# @login_required
# def disable_service():
#     try:
#         resp = requests.post("http://localhost:5000/api/service/set", json={"enabled": False})
#         if resp.ok:
#             flash("Servizio disattivato!", "warning")
#         else:
#             flash(f"Errore disattivando servizio: {resp.text}", "danger")
#     except Exception as e:
#         flash(f"Errore: {str(e)}", "danger")
#     return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
