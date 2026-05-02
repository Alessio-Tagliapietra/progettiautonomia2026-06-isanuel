try:
    from flask import (
        Flask, render_template, request, redirect,
        url_for, flash, session, make_response,
    )
    from flask_login import (
        LoginManager, login_user, logout_user,
        login_required, current_user,
    )
    from datetime import date
    from authlib.integrations.flask_client import OAuth
    from modules.webApp.gcal_client import add_editor, remove_editor, is_available as gcal_available
    import secrets

    from modules.webApp.user import User
    from modules.webApp.db_client import DbClient
    import modules.webApp.config as config
    from modules.webApp.users_db import UsersDatabase
    from modules.webApp.service_controller import service, WEEKDAY_NAMES

except ImportError as e:
    print(f"Errore import webapp.py: {e}")


app = Flask(__name__, template_folder="templates")
app.jinja_env.filters['enumerate'] = enumerate
app.secret_key = config.SECRET_KEY
app.config["SESSION_COOKIE_SECURE"]   = False
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_PERMANENT"]       = False

db = DbClient(config.DB_API_URL)

users_db = UsersDatabase(config.USERS_DATABASE_PATH)
users_db.seed(config.SEED_AUTHORIZED_USERS)

login_manager = LoginManager()
login_manager.login_view = "login_page"
login_manager.init_app(app)

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


# ── Auth ──────────────────────────────────────────────────────────────────────

@app.route("/login")
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    return render_template("login.html")


@app.route("/auth/google")
def google_login():
    redirect_uri = url_for("callback", _external=True)
    session["nonce"] = secrets.token_urlsafe(16)
    return google.authorize_redirect(redirect_uri, nonce=session["nonce"])


@app.route("/callback")
def callback():
    try:
        token     = google.authorize_access_token()
        user_info = google.parse_id_token(token, nonce=session["nonce"])
        email     = user_info.get("email", "").lower().strip()

        if not users_db.is_authorized(email):
            flash("Non sei autorizzato ad accedere.", "danger")
            return redirect(url_for("login_page"))

        login_user(User(email), remember=False)
        session["user_email"] = email
        session["user_name"]  = user_info.get("name", email)
        flash(f"Benvenuto {user_info.get('name', email)}!", "success")
        return redirect(url_for("index"))

    except Exception as e:
        print(f"Errore OAuth callback: {e}")
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


# ── Routes principali ─────────────────────────────────────────────────────────

@app.route("/")
@login_required
def index():
    stats = {
        "total_plates": len(db.get_all_plates()),
        "recent_logs":  db.get_access_history(limit=10),
    }
    return render_template("index.html", stats=stats)


@app.route("/plates")
@login_required
def plates():
    query = request.args.get("q", "").strip()
    persons = db.search_persons(query) if query else db.get_all_persons()
    return render_template("plates.html", persons=persons, query=query)


# ── Persone ───────────────────────────────────────────────────────────────────

@app.route("/person/add", methods=["POST"])
@login_required
def add_person():
    first_name = request.form.get("first_name", "").strip()
    last_name  = request.form.get("last_name", "").strip()
    role       = request.form.get("role", "").strip()
    notes      = request.form.get("notes", "").strip()

    if not first_name or not last_name or not role:
        flash("Nome, cognome e ruolo sono obbligatori.", "danger")
        return redirect(url_for("plates"))

    person_id = db.add_person(first_name, last_name, role, notes)
    if person_id > 0:
        flash(f"Persona {first_name} {last_name} aggiunta.", "success")
    else:
        flash("Errore durante l'aggiunta della persona.", "danger")
    return redirect(url_for("plates"))


@app.route("/person/<int:person_id>/edit", methods=["POST"])
@login_required
def edit_person(person_id):
    first_name = request.form.get("first_name", "").strip()
    last_name  = request.form.get("last_name", "").strip()
    role       = request.form.get("role", "").strip()
    notes      = request.form.get("notes", "").strip()

    if not first_name or not last_name or not role:
        flash("Nome, cognome e ruolo sono obbligatori.", "danger")
        return redirect(url_for("plates"))

    if db.update_person(person_id, first_name, last_name, role, notes):
        flash("Persona aggiornata con successo.", "success")
    else:
        flash("Errore durante l'aggiornamento.", "danger")
    return redirect(url_for("plates"))


@app.route("/person/<int:person_id>/delete", methods=["POST"])
@login_required
def delete_person(person_id):
    person = db.get_person(person_id)
    if person:
        n_plates = len(person.get("plates", []))
        if db.delete_person(person_id):
            flash(
                f"Persona {person['first_name']} {person['last_name']} eliminata "
                f"insieme a {n_plates} targa/targhe.",
                "warning",
            )
        else:
            flash("Errore durante l'eliminazione.", "danger")
    else:
        flash("Persona non trovata.", "danger")
    return redirect(url_for("plates"))


# ── Targhe ────────────────────────────────────────────────────────────────────

@app.route("/person/<int:person_id>/add_plate", methods=["POST"])
@login_required
def add_plate_to_person(person_id):
    plate_number    = request.form.get("plate_number", "").strip().upper()
    expiration_date = request.form.get("expiration_date", "").strip()
    notes           = request.form.get("notes", "").strip()

    if not plate_number or len(plate_number) < 6:
        flash("Numero targa non valido.", "danger")
        return redirect(url_for("plates"))

    if db.add_plate_to_person(person_id, plate_number, expiration_date, notes):
        flash(f"Targa {plate_number} aggiunta.", "success")
    else:
        flash(f"Targa {plate_number} già esistente o errore.", "warning")
    return redirect(url_for("plates"))


@app.route("/edit_plate/<plate_number>", methods=["GET", "POST"])
@login_required
def edit_plate(plate_number):
    plate = db.get_plate(plate_number)
    if not plate:
        flash("Targa non trovata!", "danger")
        return redirect(url_for("plates"))

    if request.method == "POST":
        try:
            new_plate = request.form.get("new_plate_number", "").strip().upper()
            db.update_plate(
                plate_number,
                request.form.get("expiration_date", ""),
                request.form.get("notes", ""),
                new_plate_number=new_plate if new_plate != plate_number.upper() else None,
            )
            flash("Targa aggiornata con successo!", "success")
            return redirect(url_for("plates"))
        except ValueError as e:
            flash(str(e), "danger")
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


@app.route("/add_plate", methods=["GET", "POST"])
@login_required
def add_plate():
    return redirect(url_for("plates"))


# ── Logs ──────────────────────────────────────────────────────────────────────

@app.route("/logs")
@login_required
def logs():
    today = date.today().isoformat()
    selected_date = request.args.get("selected_date", today).strip() or today
    all_logs = db.get_access_history(date=selected_date, status="authorized")
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
        **{k: v or None for k, v in filters.items() if k != "limit"},
        limit=limit_val,
    )
    return render_template("logs_storico.html", logs=all_logs, filters=filters, today=today)


@app.route("/logs/storico/delete", methods=["POST"])
@login_required
def delete_selected_logs():
    try:
        log_ids = [int(i) for i in request.form.getlist("log_ids") if i.isdigit()]
        if not log_ids:
            flash("Nessun log selezionato.", "warning")
        else:
            deleted = db.delete_logs_by_ids(log_ids)
            flash(f"Eliminati {deleted} log.", "success")
    except Exception as e:
        flash(f"Errore: {str(e)}", "danger")
    return redirect(url_for("logs_storico"))


@app.route("/logs/storico/export")
@login_required
def export_logs_filtered():
    try:
        from datetime import datetime as dt
        from flask import send_file
        import tempfile, os, csv

        filters = {
            "plate_number": request.args.get("plate_number", "").strip().upper(),
            "first_name":   request.args.get("first_name", "").strip(),
            "last_name":    request.args.get("last_name", "").strip(),
            "role":         request.args.get("role", "").strip(),
            "status":       request.args.get("status", "").strip(),
            "date_single":  request.args.get("date_single", "").strip(),
            "date_from":    request.args.get("date_from", "").strip(),
            "date_to":      request.args.get("date_to", "").strip(),
        }
        all_logs = db.get_access_history_advanced(
            **{k: v or None for k, v in filters.items()}, limit=0
        )
        if not all_logs:
            flash("Nessun log da esportare.", "warning")
            return redirect(url_for("logs_storico"))

        filename = f"storico_{dt.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(tempfile.gettempdir(), filename)
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Targa", "Data e Ora", "Stato", "Evento", "Nome", "Cognome", "Ruolo"])
            for row in all_logs:
                writer.writerow([
                    row["id"], row["plate_number"], row["timestamp"],
                    row["status"], row.get("event", ""),
                    row.get("first_name", ""), row.get("last_name", ""), row.get("role", ""),
                ])
        return send_file(filepath, mimetype="text/csv", as_attachment=True, download_name=filename)

    except Exception as e:
        flash(f"Errore esportazione: {str(e)}", "danger")
        return redirect(url_for("logs_storico"))


@app.route("/logs/analytics")
@login_required
def logs_analytics():
    from datetime import timedelta
    today         = date.today().isoformat()
    default_start = (date.today() - timedelta(days=6)).isoformat()
    start_date    = request.args.get("start_date", default_start).strip()
    end_date      = request.args.get("end_date", today).strip()

    dati_stato = db.get_accessi_per_stato(start_date, end_date)
    kpi_ev     = db.get_kpi_entrate_uscite(start_date, end_date)

    kpi = {
        "total":    sum(dati_stato.values()),
        **dati_stato,
        "entrate":  kpi_ev.get("entrate", 0),
        "uscite":   kpi_ev.get("uscite", 0),
        "presenti": kpi_ev.get("presenti", 0),
    }

    return render_template(
        "logs_analytics.html",
        start_date=start_date, end_date=end_date, today=today, kpi=kpi,
        dati_per_giorno=db.get_accessi_per_giorno(start_date, end_date),
        dati_stato=dati_stato,
        dati_orario=db.get_accessi_per_ora(start_date, end_date),
        dati_top_targhe=db.get_top_targhe(start_date, end_date, limit=10),
        dati_trend=db.get_trend_per_stato(start_date, end_date),
        dati_distrib_ev=db.get_distribuzione_entrate_uscite(start_date, end_date),
        dati_flusso_ore=db.get_flusso_orario_entrate_uscite(start_date, end_date),
        dati_saldo=db.get_saldo_giornaliero(start_date, end_date),
    )


# ── Users ─────────────────────────────────────────────────────────────────────

@app.route("/users")
@login_required
def users_list():
    return render_template("users.html", users=users_db.get_all())


@app.route("/users/add", methods=["POST"])
@login_required
def user_add():
    email = request.form.get("email", "").strip().lower()
    note  = request.form.get("note", "").strip()
 
    if not email or "@" not in email:
        flash("Email non valida.", "danger")
        return redirect(url_for("users_list"))
 
    if users_db.add(email, note):
        flash(f"Utente {email} aggiunto.", "success")
 
        # Aggiunge automaticamente come editor del Google Calendar
        if gcal_available():
            ok = add_editor(email)
            if ok:
                flash(f"{email} aggiunto come editor del calendario Google.", "info")
            else:
                flash(f"Utente aggiunto ma non è stato possibile aggiungerlo al calendario Google.", "warning")
        else:
            flash("Google Calendar non configurato — utente aggiunto solo alla webapp.", "warning")
    else:
        flash(f"L'email {email} è già autorizzata.", "warning")
 
    return redirect(url_for("users_list"))
 
 
@app.route("/users/delete/<path:email>", methods=["POST"])
@login_required
def user_delete(email):
    if email.lower() == session.get("user_email", "").lower():
        flash("Non puoi rimuovere te stesso!", "danger")
        return redirect(url_for("users_list"))
 
    if users_db.remove(email):
        flash(f"Utente {email} rimosso.", "warning")
 
        # Rimuove automaticamente dal Google Calendar
        if gcal_available():
            ok = remove_editor(email)
            if ok:
                flash(f"{email} rimosso dal calendario Google.", "info")
            else:
                flash(f"Utente rimosso dalla webapp ma non trovato nel calendario Google.", "warning")
    else:
        flash("Utente non trovato.", "danger")
 
    return redirect(url_for("users_list"))


@app.route("/users/edit/<path:email>", methods=["POST"])
@login_required
def user_edit_note(email):
    note = request.form.get("note", "").strip()
    users_db.update_note(email, note)
    flash("Nota aggiornata.", "success")
    return redirect(url_for("users_list"))

@app.route("/service")
@login_required
def service_page():
    from datetime import date as ddate
    today = ddate.today()
    status = service.get_status()
    # Calendario del mese corrente
    cal = service.get_calendar_month(today.year, today.month)
    return render_template(
        "service.html",
        status=status,
        weekday_names=WEEKDAY_NAMES,
        calendar=cal,
        cal_year=today.year,
        cal_month=today.month,
        today=today.isoformat(),
    )
 
 
@app.route("/service/calendar")
@login_required
def service_calendar_json():
    """Dati calendario per un mese (AJAX). ?year=2026&month=4"""
    from flask import jsonify
    try:
        year  = int(request.args.get("year",  __import__("datetime").date.today().year))
        month = int(request.args.get("month", __import__("datetime").date.today().month))
        return jsonify(service.get_calendar_month(year, month))
    except Exception as e:
        return jsonify({"error": str(e)}), 400
 
 
@app.route("/service/override", methods=["POST"])
@login_required
def service_override():
    action = request.form.get("action")
    if action == "activate":
        service.set_manual_override(True)
        flash("Servizio attivato manualmente.", "success")
    elif action == "deactivate":
        service.set_manual_override(False)
        flash("Servizio disattivato manualmente.", "warning")
    elif action == "auto":
        service.set_manual_override(None)
        flash("Servizio impostato su automatico.", "info")
    else:
        flash("Azione non riconosciuta.", "danger")
    return redirect(url_for("service_page"))
 
 
@app.route("/service/weekly", methods=["POST"])
@login_required
def service_weekly_save():
    """
    Salva il template settimanale.
    Form: per ogni giorno (0-6) un campo JSON con la lista di fasce.
    Esempio: day_0 = '[{"start":"07:40","end":"08:00"},{"start":"12:00","end":"12:30"}]'
    """
    import json as _json
    try:
        for d in range(7):
            raw = request.form.get(f"day_{d}", "[]").strip()
            slots = _json.loads(raw) if raw else []
            # Validazione minima
            clean = []
            for s in slots:
                if s.get("start") and s.get("end") and s["start"] < s["end"]:
                    clean.append({"start": s["start"], "end": s["end"]})
            service.set_weekly_day(d, clean)
        flash("Template settimanale salvato.", "success")
    except Exception as e:
        flash(f"Errore: {str(e)}", "danger")
    return redirect(url_for("service_page"))
 
 
@app.route("/service/day-override", methods=["POST"])
@login_required
def service_day_override():
    """
    Imposta o rimuove un override per una data specifica.
    Form: date (YYYY-MM-DD), slots (JSON array), action (set|remove)
    """
    import json as _json
    try:
        date_str = request.form.get("date", "").strip()
        action   = request.form.get("action", "set")
 
        if not date_str:
            flash("Data mancante.", "danger")
            return redirect(url_for("service_page"))
 
        if action == "remove":
            service.remove_day_override(date_str)
            flash(f"Override rimosso per {date_str}.", "info")
        else:
            raw   = request.form.get("slots", "[]").strip()
            slots = _json.loads(raw) if raw else []
            clean = []
            for s in slots:
                if s.get("start") and s.get("end") and s["start"] < s["end"]:
                    clean.append({"start": s["start"], "end": s["end"]})
            service.set_day_override(date_str, clean)
            label = "chiuso" if not clean else f"{len(clean)} fascia/e"
            flash(f"Override impostato per {date_str}: {label}.", "success")
    except Exception as e:
        flash(f"Errore: {str(e)}", "danger")
    return redirect(url_for("service_page"))
 
 
@app.route("/service/default", methods=["POST"])
@login_required
def service_default():
    default_active = request.form.get("default_active") == "1"
    service.set_default_active(default_active)
    state = "attivo" if default_active else "disattivo"
    flash(f"Comportamento fuori orario: {state}.", "info")
    return redirect(url_for("service_page"))
 
 
@app.route("/service/status")
@login_required
def service_status_json():
    from flask import jsonify
    return jsonify(service.get_status())

# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)