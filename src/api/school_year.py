"""
Año escolar (School_Year) — fuente única de verdad del backend.

Reglas:
- Si existe la variable de entorno SCHOOL_YEAR (ej. 2027), se usa tal cual.
- Si no, se calcula: desde el mes SCHOOL_YEAR_ROLLOVER_MONTH (por defecto 11 = noviembre)
  el colegio ya planea el año siguiente. Ej: 18-nov-2026 -> 2027.

Filtro en GET (?year=):
- sin parámetro     -> año escolar actual
- ?year=2026        -> solo ese año
- ?year=all         -> sin filtro (todos los años)
"""
import os
from datetime import datetime

# Primer año con datos en la plataforma (todo lo anterior a la migración quedó en 2026)
FIRST_SCHOOL_YEAR = 2026


def current_school_year():
    env_year = str(os.getenv('SCHOOL_YEAR', '')).strip()
    if env_year.isdigit():
        return int(env_year)
    try:
        rollover = int(os.getenv('SCHOOL_YEAR_ROLLOVER_MONTH', '11'))
    except ValueError:
        rollover = 11
    now = datetime.now()
    return now.year + 1 if now.month >= rollover else now.year


def to_year(value):
    """Convierte '2027', 2027, ' 2027 ' -> 2027. Cualquier otra cosa -> None."""
    if value is None:
        return None
    s = str(value).strip()
    if s.isdigit() and len(s) == 4:
        return int(s)
    return None


def year_from_request(args):
    """Devuelve el año a filtrar, o None si piden 'all'."""
    raw = args.get('year')
    if raw is None or str(raw).strip() == '':
        return current_school_year()
    if str(raw).strip().lower() == 'all':
        return None
    return to_year(raw) or current_school_year()


def apply_year_filter(query, model, args):
    year = year_from_request(args)
    if year is not None and hasattr(model, 'School_Year'):
        query = query.filter(model.School_Year == year)
    return query


def year_for_new_record(data):
    """Año para un registro nuevo: el que venga en el payload o el actual."""
    if data:
        y = to_year(data.get('School_Year'))
        if y:
            return y
    return current_school_year()
