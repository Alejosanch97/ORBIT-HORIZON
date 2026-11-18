/* ============================================================
   AÑO ESCOLAR — helpers compartidos del frontend
   ------------------------------------------------------------
   - store.schoolYear   → año escolar vigente (lo dice el backend: /api/school-year)
   - store.viewYear     → año que el usuario está consultando en los filtros
   - Todo lo que se CREA se guarda con el año vigente (schoolYear).
   - Todo lo que se CONSULTA usa viewYear (por defecto = año vigente).
   ============================================================ */

export const FIRST_SCHOOL_YEAR = 2026;

// Mismo cálculo que el backend (fallback mientras llega /api/school-year):
// desde noviembre ya se planea el año siguiente.
export const computeSchoolYear = () => {
    const d = new Date();
    return d.getMonth() + 1 >= 11 ? d.getFullYear() + 1 : d.getFullYear();
};

export const getCurrentYear = (store) => Number(store?.schoolYear) || computeSchoolYear();

export const getViewYear = (store) => Number(store?.viewYear) || getCurrentYear(store);

export const getYearOptions = (store) => {
    const current = getCurrentYear(store);
    const set = new Set((store?.availableYears || []).map(Number).filter(Boolean));
    for (let y = FIRST_SCHOOL_YEAR; y <= current; y++) set.add(y);
    return [...set].sort((a, b) => b - a);
};

// Año de un registro (los locales sin sincronizar aún no traen School_Year)
export const recordYear = (record, fallback) => Number(record?.School_Year) || fallback;

// Trae el año vigente del backend UNA sola vez por sesión de la app
let schoolYearPromise = null;
export const ensureSchoolYear = (api, dispatch) => {
    if (!schoolYearPromise) {
        schoolYearPromise = fetch(`${api}/school-year`)
            .then(r => r.json())
            .then(data => {
                if (data && data.current) {
                    dispatch({
                        type: 'set_school_year',
                        payload: { current: Number(data.current), years: data.years || [] }
                    });
                }
                return data;
            })
            .catch(e => {
                console.warn('[school-year] usando cálculo local:', e);
                schoolYearPromise = null; // permite reintentar luego
                return null;
            });
    }
    return schoolYearPromise;
};
