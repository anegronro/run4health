"""Two languages, one app.

The interface strings live here; the programs themselves are separate files
per language under data/programs/<lang>/. Anything missing in Spanish falls
back to English rather than showing a blank, so a half-finished translation
degrades instead of breaking.
"""
from __future__ import annotations

DEFAULT = "en"
LANGS = {"en": "English", "es": "Español"}

STRINGS: dict[str, dict[str, str]] = {
    # ── shell ──
    "programs": {"en": "Programs", "es": "Programas"},
    "training_log": {"en": "Training log", "es": "Mi registro"},
    "my_programs": {"en": "My programs", "es": "Mis programas"},
    "your_account": {"en": "Your account", "es": "Tu cuenta"},
    "back_to_app": {"en": "Back to the app", "es": "Volver a la app"},
    "no_programs": {
        "en": "No programs yet.",
        "es": "Todavía no hay programas.",
    },

    # ── gate ──
    "gate_prompt": {
        "en": "Enter the password to open the app.",
        "es": "Escribe la contraseña para abrir la app.",
    },
    "password": {"en": "Password", "es": "Contraseña"},
    "enter": {"en": "Enter", "es": "Entrar"},
    "wrong_password": {
        "en": "Wrong password. Try again.",
        "es": "Contraseña incorrecta. Inténtalo otra vez.",
    },

    # ── sign in / sign up ──
    "welcome_back": {"en": "Welcome back", "es": "Bienvenido de nuevo"},
    "signin_sub": {
        "en": "Sign in to pick up where you left off.",
        "es": "Entra y sigue donde lo dejaste.",
    },
    "email": {"en": "Email", "es": "Correo"},
    "sign_in": {"en": "Sign in", "es": "Entrar"},
    "sign_out": {"en": "Sign out", "es": "Cerrar sesión"},
    "new_here": {"en": "New here?", "es": "¿Primera vez?"},
    "create_account": {"en": "Create an account", "es": "Crear una cuenta"},
    "signup_sub": {
        "en": "Your name, your email, and a password only you know.",
        "es": "Tu nombre, tu correo y una contraseña que solo tú sepas.",
    },
    "your_name": {"en": "Your name", "es": "Tu nombre"},
    "password_min": {
        "en": "Password — at least {n} characters",
        "es": "Contraseña — mínimo {n} caracteres",
    },
    "write_your_name": {
        "en": "Write your name the way you write it, accents and all.",
        "es": "Escribe tu nombre como lo escribes tú, con acentos y todo.",
    },
    "have_account": {
        "en": "Already have an account?",
        "es": "¿Ya tienes cuenta?",
    },
    "what_we_store": {
        "en": "What we store about you",
        "es": "Qué guardamos sobre ti",
    },

    # ── account ──
    "change_name": {"en": "Change your name", "es": "Cambiar tu nombre"},
    "save_name": {"en": "Save name", "es": "Guardar nombre"},
    "name_saved": {"en": "Name saved.", "es": "Nombre guardado."},
    "change_password": {"en": "Change your password", "es": "Cambiar tu contraseña"},
    "current_password": {"en": "Current password", "es": "Contraseña actual"},
    "new_password_min": {
        "en": "New password — at least {n} characters",
        "es": "Contraseña nueva — mínimo {n} caracteres",
    },
    "password_note": {
        "en": "Changing it signs you out everywhere, including here.",
        "es": "Al cambiarla se cierra la sesión en todas partes, aquí incluido.",
    },
    "language": {"en": "Language", "es": "Idioma"},
    "language_note": {
        "en": "Changes the app and the training programs.",
        "es": "Cambia la app y los programas de entrenamiento.",
    },
    "save_language": {"en": "Save language", "es": "Guardar idioma"},
    "language_saved": {"en": "Language saved.", "es": "Idioma guardado."},
    "download_data": {"en": "Download your data", "es": "Descargar tus datos"},
    "download_pdf": {"en": "Download PDF", "es": "Descargar PDF"},
    "download_note": {
        "en": "A PDF with your account and every session you ticked off, with "
              "dates and miles. Your password isn't included: it's stored "
              "hashed and can't be read back.",
        "es": "Un PDF con tu cuenta y cada sesión que marcaste, con fechas y "
              "millas. Tu contraseña no va incluida: se guarda cifrada y no "
              "se puede leer.",
    },
    "moving_app": {"en": "Moving to another app?", "es": "¿Te mudas a otra app?"},
    "as_data_file": {
        "en": "Get it as a data file (JSON)",
        "es": "Descárgalo como archivo de datos (JSON)",
    },
    "delete_account": {"en": "Delete your account", "es": "Borrar tu cuenta"},
    "delete_note": {
        "en": "This deletes your name, your email and every session you've "
              "ticked off. It cannot be undone. Your data stays in the nightly "
              "backups for up to fourteen days before those expire too.",
        "es": "Esto borra tu nombre, tu correo y todas las sesiones que has "
              "marcado. No se puede deshacer. Tus datos siguen en las copias "
              "de seguridad nocturnas hasta catorce días, hasta que caducan.",
    },
    "download_first": {
        "en": "Consider downloading your data first.",
        "es": "Piensa en descargar tus datos antes.",
    },
    "type_to_confirm": {
        "en": "Type {email} to confirm",
        "es": "Escribe {email} para confirmar",
    },
    "delete_for_good": {
        "en": "Delete my account for good",
        "es": "Borrar mi cuenta definitivamente",
    },
    "signout_note": {
        "en": "Signing out only ends this browser's session. Your ticked "
              "sessions stay exactly where they are.",
        "es": "Cerrar sesión solo termina la sesión de este navegador. Las "
              "sesiones que marcaste se quedan donde están.",
    },

    # ── programs ──
    "weeks": {"en": "weeks", "es": "semanas"},
    "days_week": {"en": "days/week", "es": "días/sem"},
    "peak_week": {"en": "peak {n} mi/week", "es": "pico {n} mi/sem"},
    "guide": {"en": "Guide", "es": "Guía"},
    "week": {"en": "Week", "es": "Semana"},
    "session": {"en": "session", "es": "sesión"},
    "sessions": {"en": "sessions", "es": "sesiones"},
    "of_sessions": {"en": "{done} of {total} sessions", "es": "{done} de {total} sesiones"},
    "reset": {"en": "Reset", "es": "Reiniciar"},
    "reset_confirm": {"en": "Tap again to clear", "es": "Toca otra vez para borrar"},
    "cancel": {"en": "Cancel", "es": "Cancelar"},
    "miles_per_week": {"en": "Miles per week", "es": "Millas por semana"},
    "chart_note": {
        "en": "Miles of measured running per week — peak {mi} mi ({km} km). "
              "Warm-ups and cool-downs are timed rather than measured, so they "
              "are not counted here. The dips are the down weeks, on purpose.",
        "es": "Millas medidas por semana — pico {mi} mi ({km} km). El "
              "calentamiento y la vuelta a la calma van en minutos, no en "
              "distancia, así que no cuentan aquí. Los bajones son las semanas "
              "de descarga, a propósito.",
    },
    "mark_done": {"en": "Mark as done", "es": "Marcar como hecha"},
    "completed": {"en": "Completed", "es": "Completada"},
    "previous_day": {"en": "Previous day", "es": "Día anterior"},
    "next_day": {"en": "Next day", "es": "Día siguiente"},
    "watch_demo": {"en": "Watch demo", "es": "Ver demostración"},
    "rest": {"en": "rest", "es": "descanso"},
    "sets": {"en": "sets", "es": "series"},

    # ── training log ──
    "log_title": {"en": "Training log", "es": "Mi registro"},
    "miles_run": {"en": "miles run", "es": "millas corridas"},
    "sessions_done": {"en": "sessions done", "es": "sesiones hechas"},
    "of_planned": {"en": "of {n} planned", "es": "de {n} planificadas"},
    "of_distance": {"en": "of the distance", "es": "de la distancia"},
    "across_programs": {
        "en": "of {mi} mi across all programs",
        "es": "de {mi} mi entre todos los programas",
    },
    "nothing_yet": {
        "en": "Nothing ticked off yet. Open a program and mark a session as "
              "done — the miles land here.",
        "es": "Todavía no has marcado nada. Abre un programa y marca una "
              "sesión como hecha: las millas aparecen aquí.",
    },
    "mi_run": {"en": "{mi} mi run", "es": "{mi} mi corridas"},
    "done_of": {"en": "{done} of {total} sessions", "es": "{done} de {total} sesiones"},
    "solid_outline": {
        "en": "Solid is what you ticked off, the outline is what the week plans.",
        "es": "Lo relleno es lo que marcaste; el contorno es lo que planifica la semana.",
    },
    "th_week": {"en": "Week", "es": "Semana"},
    "th_miles_run": {"en": "Miles run", "es": "Millas corridas"},
    "th_planned": {"en": "Planned", "es": "Planificadas"},
    "th_sessions": {"en": "Sessions", "es": "Sesiones"},
    "all": {"en": "All", "es": "Total"},
    "log_note": {
        "en": "Sessions written in minutes rather than a distance — tempo runs, "
              "the walk-run weeks — add no miles here, but still count as sessions.",
        "es": "Las sesiones escritas en minutos y no en distancia — los ritmos "
              "controlados, las semanas de caminata-trote — no suman millas "
              "aquí, pero cuentan como sesiones.",
    },

    # ── gone ──
    "gone_title": {"en": "Your account is gone", "es": "Tu cuenta ya no existe"},
    "gone_sub": {
        "en": "Your name, email and every session you ticked off have been "
              "deleted from the database.",
        "es": "Tu nombre, tu correo y todas las sesiones que marcaste se han "
              "borrado de la base de datos.",
    },
    "gone_note": {
        "en": "They remain in the nightly backups for up to fourteen days, then "
              "those expire too — that window is what protects everyone from an "
              "accidental deletion.",
        "es": "Siguen en las copias de seguridad nocturnas hasta catorce días, "
              "y luego caducan — esa ventana es lo que protege a todos de un "
              "borrado accidental.",
    },
    "welcome_back_any": {
        "en": "You're welcome back any time.",
        "es": "Puedes volver cuando quieras.",
    },
}


def normalise(lang: str | None) -> str:
    return lang if lang in LANGS else DEFAULT


def t(lang: str, key: str, **kw) -> str:
    """A string in the chosen language, falling back to English."""
    entry = STRINGS.get(key)
    if entry is None:
        return key
    text = entry.get(lang) or entry[DEFAULT]
    return text.format(**kw) if kw else text
