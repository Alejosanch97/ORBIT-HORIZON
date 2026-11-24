import React, { useState, useEffect, useMemo } from 'react';
import '../Styles/curriculum.css';
import {
    Brain, Search, Save, RotateCcw, Download, Plus, Trash2, ChevronDown,
    ChevronRight, BookMarked, AlertTriangle, Lock, X, CheckCircle2, Code2
} from 'lucide-react';
import useGlobalReducer from '../hooks/useGlobalReducer';

const API = `${import.meta.env.VITE_BACKEND_URL}/api`;

/* ============================================================
   Utilidades
   ============================================================ */
const safeParse = (v) => {
    if (v && typeof v === 'object') return v;
    try { return JSON.parse(v || ''); } catch { return null; }
};
const clone = (v) => JSON.parse(JSON.stringify(v));

// Nombres legibles para las llaves más comunes de las mallas
const LABELS = {
    institution: 'Institución', terms: 'Periodos', term_number: 'Número de periodo',
    term_name: 'Nombre del periodo', curriculum_framework: 'Marco curricular',
    standard: 'Estándar', dbas: 'DBA', id: 'ID', descriptor: 'Descriptor',
    evidences: 'Evidencias', sdg: 'ODS (SDG)', sdg_alignment: 'ODS (SDG)', ods: 'ODS',
    challenge_context: 'Contexto del reto', objectives: 'Objetivos',
    competency_based_plan: 'Plan por competencias',
    general_learning_outcome: 'Resultado de aprendizaje general',
    specific_learning_outcomes: 'Resultados de aprendizaje específicos',
    methodology_learning_path: 'Ruta metodológica', steps: 'Pasos',
    subject: 'Materia', grade: 'Grado', year: 'Año', name: 'Nombre', title: 'Título',
    description: 'Descripción', contents: 'Contenidos', topics: 'Temas',
};
const humanize = (key) => {
    if (typeof key === 'number') return `#${key + 1}`;
    if (LABELS[key]) return LABELS[key];
    const s = String(key).replace(/[_-]+/g, ' ').trim();
    return s.charAt(0).toUpperCase() + s.slice(1);
};

// Campos que Lumi usa para encontrar las cosas: se ven pero no se editan
const LOCKED_KEYS = new Set(['term_number']);

const getIn = (obj, path) => path.reduce((o, k) => (o == null ? undefined : o[k]), obj);
const setIn = (obj, path, value) => {
    if (!path.length) return value;
    const [k, ...rest] = path;
    const copy = Array.isArray(obj) ? [...obj] : { ...obj };
    copy[k] = setIn(obj[k], rest, value);
    return copy;
};

// Plantilla vacía con la MISMA forma que un elemento existente
const blankLike = (v) => {
    if (Array.isArray(v)) return [];
    if (v && typeof v === 'object') {
        const o = {};
        Object.keys(v).forEach(k => { o[k] = blankLike(v[k]); });
        return o;
    }
    if (typeof v === 'number') return 0;
    if (typeof v === 'boolean') return false;
    return '';
};

// Lista de cambios (rutas) entre el original y el borrador
const diffPaths = (a, b, path = [], out = []) => {
    const isObj = (x) => x && typeof x === 'object';
    if (isObj(a) && isObj(b) && Array.isArray(a) === Array.isArray(b)) {
        const keys = new Set([...Object.keys(a), ...Object.keys(b)]);
        keys.forEach(k => {
            const key = Array.isArray(a) ? Number(k) : k;
            if (!(k in a)) out.push({ path: [...path, key], type: 'add' });
            else if (!(k in b)) out.push({ path: [...path, key], type: 'remove' });
            else diffPaths(a[k], b[k], [...path, key], out);
        });
    } else if (JSON.stringify(a) !== JSON.stringify(b)) {
        out.push({ path, type: 'edit' });
    }
    return out;
};

const pathLabel = (json, path) => {
    const parts = [];
    path.forEach((k, i) => {
        // Los periodos se nombran por su número real
        if (i === 1 && path[0] === 'terms' && typeof k === 'number') {
            const t = json?.terms?.[k];
            parts.push(`Periodo ${t?.term_number ?? k + 1}`);
        } else parts.push(humanize(k));
    });
    return parts.join(' › ');
};

const pathKey = (path) => path.join('.');

/* ============================================================
   Pop up gigante: "Este es el cerebro de Lumi"
   ============================================================ */
const BrainGate = ({ onEnter, onExit }) => {
    const [ok, setOk] = useState(false);
    return (
        <div className="cm-gate">
            <div className="cm-gate-card">
                <div className="cm-gate-orb"><Brain size={64} strokeWidth={1.6} /></div>
                <span className="cm-gate-kicker">Zona sensible</span>
                <h1>Este es el cerebro de Lumi</h1>
                <p className="cm-gate-lead">
                    Aquí viven las mallas curriculares: DBA, estándares, ODS, objetivos y contenidos
                    de cada periodo. <strong>Lumi lee todo de aquí</strong> para crear las planeaciones.
                </p>
                <div className="cm-gate-rules">
                    <div><AlertTriangle size={20} /> Si editas o borras algo, Lumi no sabrá de dónde tomar los datos.</div>
                    <div><CheckCircle2 size={20} /> Edita solo lo que necesites (por ejemplo, cambiar un ODS o un DBA).</div>
                    <div><Download size={20} /> Antes de guardar, descarga el respaldo de la malla.</div>
                    <div><Brain size={20} /> Revisa muy bien la lista de cambios antes de confirmar.</div>
                </div>
                <label className="cm-gate-check">
                    <input type="checkbox" checked={ok} onChange={e => setOk(e.target.checked)} />
                    <span>Entiendo. Voy a editar con cuidado y estaré pendiente de mis cambios.</span>
                </label>
                <div className="cm-gate-actions">
                    <button className="cm-btn ghost" onClick={onExit}>Mejor no, volver</button>
                    <button className="cm-btn danger" disabled={!ok} onClick={onEnter}>Entrar al cerebro de Lumi</button>
                </div>
            </div>
        </div>
    );
};

/* ============================================================
   Editor recursivo de campos
   ============================================================ */
const AutoText = ({ value, onChange, changed, readOnly }) => (
    <textarea
        className={`cm-input ${changed ? 'changed' : ''}`}
        value={value ?? ''}
        readOnly={readOnly}
        rows={Math.min(8, Math.max(1, Math.ceil(String(value ?? '').length / 90)))}
        onChange={e => onChange(e.target.value)}
    />
);

const FieldNode = ({ name, value, path, ctx, depth }) => {
    const { draft, changedSet, update, removeItem, addItem } = ctx;
    const [open, setOpen] = useState(depth < 2);
    const key = pathKey(path);
    const changed = changedSet.has(key);
    const locked = LOCKED_KEYS.has(name);

    // ---- Valores simples ----
    if (value === null || typeof value !== 'object') {
        return (
            <div className={`cm-field ${changed ? 'is-changed' : ''}`}>
                <label>
                    {humanize(name)}
                    {locked && <span className="cm-lock"><Lock size={11} /> Lumi lo usa, no se edita</span>}
                    {changed && <span className="cm-dot">modificado</span>}
                </label>
                {locked ? (
                    <div className="cm-locked-val">{String(value)}</div>
                ) : typeof value === 'boolean' ? (
                    <button className={`cm-toggle ${value ? 'on' : ''}`} onClick={() => update(path, !value)}>
                        {value ? 'Sí' : 'No'}
                    </button>
                ) : typeof value === 'number' ? (
                    <input
                        type="number" className={`cm-input ${changed ? 'changed' : ''}`}
                        value={value} readOnly={locked}
                        onChange={e => update(path, e.target.value === '' ? 0 : Number(e.target.value))}
                    />
                ) : (
                    <AutoText value={value} readOnly={locked} changed={changed} onChange={v => update(path, v)} />
                )}
            </div>
        );
    }

    // ---- Lista de textos (ej. resultados específicos, ODS múltiples) ----
    if (Array.isArray(value) && value.every(v => v === null || typeof v !== 'object')) {
        return (
            <div className="cm-block">
                <div className="cm-block-head" onClick={() => setOpen(!open)}>
                    {open ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                    <span>{humanize(name)}</span>
                    <em>{value.length}</em>
                </div>
                {open && (
                    <div className="cm-block-body">
                        {value.map((v, i) => {
                            const c = changedSet.has(pathKey([...path, i]));
                            return (
                                <div key={i} className="cm-list-row">
                                    <span className="cm-list-n">{i + 1}</span>
                                    <AutoText value={v} changed={c} onChange={nv => update([...path, i], nv)} />
                                    <button className="cm-icon-btn" title="Quitar" onClick={() => removeItem(path, i)}><Trash2 size={15} /></button>
                                </div>
                            );
                        })}
                        <button className="cm-add" onClick={() => addItem(path)}><Plus size={14} /> Agregar</button>
                    </div>
                )}
            </div>
        );
    }

    // ---- Lista de objetos (ej. DBA, competencias, pasos) ----
    if (Array.isArray(value)) {
        return (
            <div className="cm-block">
                <div className="cm-block-head" onClick={() => setOpen(!open)}>
                    {open ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                    <span>{humanize(name)}</span>
                    <em>{value.length}</em>
                </div>
                {open && (
                    <div className="cm-block-body">
                        {value.map((item, i) => (
                            <div key={i} className="cm-item">
                                <div className="cm-item-head">
                                    <span>{humanize(name)} {i + 1}</span>
                                    <button className="cm-icon-btn" title="Quitar este elemento" onClick={() => removeItem(path, i)}><Trash2 size={15} /></button>
                                </div>
                                {Object.entries(item || {}).map(([k, v]) => (
                                    <FieldNode key={k} name={k} value={v} path={[...path, i, k]} ctx={ctx} depth={depth + 1} />
                                ))}
                            </div>
                        ))}
                        <button className="cm-add" onClick={() => addItem(path)}><Plus size={14} /> Agregar {humanize(name).toLowerCase()}</button>
                    </div>
                )}
            </div>
        );
    }

    // ---- Objeto ----
    return (
        <div className="cm-block">
            <div className="cm-block-head" onClick={() => setOpen(!open)}>
                {open ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                <span>{humanize(name)}</span>
            </div>
            {open && (
                <div className="cm-block-body">
                    {Object.entries(value).map(([k, v]) => (
                        <FieldNode key={k} name={k} value={v} path={[...path, k]} ctx={ctx} depth={depth + 1} />
                    ))}
                </div>
            )}
        </div>
    );
};

/* ============================================================
   Página principal
   ============================================================ */
export const CurriculumEditor = ({ userData, onExit }) => {
    const { store, dispatch } = useGlobalReducer();
    const [accepted, setAccepted] = useState(false);
    const [maps, setMaps] = useState([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');
    const [fSubject, setFSubject] = useState('');
    const [fGrade, setFGrade] = useState('');
    const [selectedId, setSelectedId] = useState(null);
    const [original, setOriginal] = useState(null);
    const [draft, setDraft] = useState(null);
    const [tab, setTab] = useState('general');
    const [showReview, setShowReview] = useState(false);
    const [saving, setSaving] = useState(false);
    const [toast, setToast] = useState(null);

    const notify = (message, type = 'ok') => { setToast({ message, type }); setTimeout(() => setToast(null), 3500); };

    // ---- Carga ----
    const loadMaps = async () => {
        setLoading(true);
        try {
            const data = await fetch(`${API}/curriculum-maps`).then(r => r.json());
            let list = Array.isArray(data) ? data : [];
            const myColegio = userData?.colegio_id;
            if (myColegio) list = list.filter(m => !m.colegio_id || String(m.colegio_id) === String(myColegio));
            setMaps(list);
            dispatch({ type: 'set_curriculum_maps', payload: list });
        } catch (e) {
            console.error(e);
            notify('No se pudieron cargar las mallas', 'error');
        } finally { setLoading(false); }
    };
    useEffect(() => { if (accepted) loadMaps(); }, [accepted]);

    // ---- Filtros ----
    const subjects = useMemo(() => [...new Set(maps.map(m => m.Subject).filter(Boolean))].sort(), [maps]);
    const grades = useMemo(() => [...new Set(maps.filter(m => !fSubject || m.Subject === fSubject).map(m => m.Grade).filter(Boolean))], [maps, fSubject]);
    const filtered = useMemo(() => maps.filter(m =>
        (!fSubject || m.Subject === fSubject) &&
        (!fGrade || m.Grade === fGrade) &&
        (!search || `${m.Name} ${m.Subject} ${m.Grade}`.toLowerCase().includes(search.toLowerCase()))
    ), [maps, fSubject, fGrade, search]);

    // ---- Cambios ----
    const changes = useMemo(() => (original && draft ? diffPaths(original, draft) : []), [original, draft]);
    const changedSet = useMemo(() => {
        const s = new Set();
        changes.forEach(c => {
            // marca la ruta y todos sus padres (para que el periodo/bloque se vea "modificado")
            for (let i = 1; i <= c.path.length; i++) s.add(pathKey(c.path.slice(0, i)));
        });
        return s;
    }, [changes]);
    const dirty = changes.length > 0;

    const selected = maps.find(m => m.id === selectedId);

    const openMap = (m) => {
        if (dirty && !window.confirm('Tienes cambios sin guardar en esta malla. ¿Descartarlos?')) return;
        const json = safeParse(m.Content_JSON);
        setSelectedId(m.id);
        setOriginal(json);
        setDraft(json ? clone(json) : null);
        setTab('general');
    };

    const update = (path, value) => setDraft(d => setIn(d, path, value));
    const removeItem = (path, index) => {
        const arr = getIn(draft, path);
        const preview = typeof arr[index] === 'object' ? 'este elemento completo' : `"${String(arr[index]).slice(0, 80)}"`;
        if (!window.confirm(`¿Seguro que quieres quitar ${preview}?\nLumi dejará de verlo.`)) return;
        setDraft(d => setIn(d, path, getIn(d, path).filter((_, i) => i !== index)));
    };
    const addItem = (path) => {
        const arr = getIn(draft, path) || [];
        const template = arr.length ? blankLike(arr[arr.length - 1]) : '';
        setDraft(d => setIn(d, path, [...(getIn(d, path) || []), template]));
    };

    const downloadBackup = () => {
        if (!selected) return;
        const blob = new Blob([JSON.stringify(original, null, 2)], { type: 'application/json' });
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = `respaldo_malla_${selected.ID_Map}_${selected.Subject}_${selected.Grade}.json`.replace(/\s+/g, '_');
        a.click();
        URL.revokeObjectURL(a.href);
    };

    const save = async () => {
        if (!selected || !dirty) return;
        setSaving(true);
        try {
            const resp = await fetch(`${API}/curriculum-maps/${selected.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ Content_JSON: JSON.stringify(draft) })
            });
            const data = await resp.json();
            if (!resp.ok || data.status !== 'success') throw new Error(data.message || 'Error al guardar');
            const updated = data.data;
            const newList = maps.map(m => (m.id === updated.id ? updated : m));
            setMaps(newList);
            dispatch({ type: 'set_curriculum_maps', payload: newList });
            setOriginal(clone(draft));
            setShowReview(false);
            notify('Malla guardada. Lumi ya usa la versión nueva.');
        } catch (e) {
            notify(e.message, 'error');
        } finally { setSaving(false); }
    };

    if (!accepted) return <BrainGate onEnter={() => setAccepted(true)} onExit={onExit} />;

    // Pestañas: General (todo menos los periodos) + un tab por periodo + JSON
    const terms = Array.isArray(draft?.terms) ? draft.terms : [];
    const generalEntries = draft && typeof draft === 'object' ? Object.entries(draft).filter(([k]) => k !== 'terms') : [];
    const ctx = { draft, changedSet, update, removeItem, addItem };

    return (
        <div className="cm-wrap">
            {toast && <div className={`cm-toast ${toast.type}`}>{toast.message}</div>}

            <header className="cm-head">
                <div className="cm-head-icon"><Brain size={26} /></div>
                <div>
                    <h1>Mallas curriculares</h1>
                    <p>El cerebro de Lumi · edita con cuidado, todo lo que cambies afecta las planeaciones nuevas.</p>
                </div>
            </header>

            <div className="cm-filters">
                <div className="cm-search"><Search size={16} /><input placeholder="Buscar malla…" value={search} onChange={e => setSearch(e.target.value)} /></div>
                <select value={fSubject} onChange={e => { setFSubject(e.target.value); setFGrade(''); }}>
                    <option value="">Todas las materias</option>
                    {subjects.map(s => <option key={s}>{s}</option>)}
                </select>
                <select value={fGrade} onChange={e => setFGrade(e.target.value)}>
                    <option value="">Todos los grados</option>
                    {grades.map(g => <option key={g}>{g}</option>)}
                </select>
                <span className="cm-count"><strong>{filtered.length}</strong> mallas</span>
            </div>

            <div className="cm-layout">
                {/* ---- Lista ---- */}
                <aside className="cm-list">
                    {loading && <div className="cm-empty">Cargando mallas…</div>}
                    {!loading && !filtered.length && <div className="cm-empty">No hay mallas con ese filtro.</div>}
                    {filtered.map(m => (
                        <button key={m.id} className={`cm-map ${m.id === selectedId ? 'on' : ''}`} onClick={() => openMap(m)}>
                            <span className="cm-map-subject">{m.Subject || '—'}</span>
                            <strong>{m.Grade || 'Sin grado'}</strong>
                            <small>{m.Name}</small>
                        </button>
                    ))}
                </aside>

                {/* ---- Editor ---- */}
                <section className="cm-editor">
                    {!selected && (
                        <div className="cm-placeholder">
                            <BookMarked size={44} />
                            <h3>Elige una malla</h3>
                            <p>Filtra por materia y grado, y abre la que necesitas corregir.</p>
                        </div>
                    )}

                    {selected && !draft && (
                        <div className="cm-placeholder error">
                            <AlertTriangle size={40} />
                            <h3>El JSON de esta malla está dañado</h3>
                            <p>No se puede mostrar de forma ordenada. Revísalo en “Datos en tabla”.</p>
                        </div>
                    )}

                    {selected && draft && (
                        <>
                            <div className="cm-ed-head">
                                <div>
                                    <div className="cm-tags"><span>{selected.Subject}</span><span>{selected.Grade}</span><span>ID {selected.ID_Map}</span></div>
                                    <h2>{selected.Name}</h2>
                                </div>
                                <div className="cm-ed-actions">
                                    <button className="cm-btn ghost" onClick={downloadBackup}><Download size={15} /> Respaldo</button>
                                    <button className="cm-btn ghost" disabled={!dirty} onClick={() => window.confirm('¿Descartar todos los cambios?') && setDraft(clone(original))}><RotateCcw size={15} /> Descartar</button>
                                    <button className="cm-btn primary" disabled={!dirty} onClick={() => setShowReview(true)}>
                                        <Save size={15} /> Guardar {dirty ? `(${changes.length})` : ''}
                                    </button>
                                </div>
                            </div>

                            <nav className="cm-tabs">
                                <button className={tab === 'general' ? 'on' : ''} onClick={() => setTab('general')}>General</button>
                                {terms.map((t, i) => (
                                    <button key={i} className={`${tab === i ? 'on' : ''} ${changedSet.has(pathKey(['terms', i])) ? 'dirty' : ''}`} onClick={() => setTab(i)}>
                                        Periodo {t?.term_number ?? i + 1}
                                    </button>
                                ))}
                                <button className={tab === 'json' ? 'on' : ''} onClick={() => setTab('json')}><Code2 size={14} /> JSON</button>
                            </nav>

                            <div className="cm-body">
                                {tab === 'general' && (generalEntries.length
                                    ? generalEntries.map(([k, v]) => <FieldNode key={k} name={k} value={v} path={[k]} ctx={ctx} depth={0} />)
                                    : <div className="cm-empty">Esta malla no tiene datos generales.</div>)}

                                {typeof tab === 'number' && terms[tab] && Object.entries(terms[tab]).map(([k, v]) => (
                                    <FieldNode key={`${tab}-${k}`} name={k} value={v} path={['terms', tab, k]} ctx={ctx} depth={0} />
                                ))}

                                {tab === 'json' && (
                                    <pre className="cm-json">{JSON.stringify(draft, null, 2)}</pre>
                                )}
                            </div>
                        </>
                    )}
                </section>
            </div>

            {/* ---- Revisión de cambios antes de guardar ---- */}
            {showReview && (
                <div className="cm-modal-bg" onClick={() => !saving && setShowReview(false)}>
                    <div className="cm-modal" onClick={e => e.stopPropagation()}>
                        <button className="cm-modal-x" onClick={() => setShowReview(false)}><X size={18} /></button>
                        <div className="cm-modal-icon"><Brain size={30} /></div>
                        <h3>Revisa tus cambios</h3>
                        <p>Vas a modificar <strong>{changes.length}</strong> {changes.length === 1 ? 'dato' : 'datos'} de <strong>{selected?.Subject} · {selected?.Grade}</strong>. Lumi usará esto desde la próxima planeación.</p>
                        <ul className="cm-changes">
                            {changes.map((c, i) => {
                                const before = getIn(original, c.path);
                                const after = getIn(draft, c.path);
                                const show = (v) => (v === undefined ? '—' : typeof v === 'object' ? '(bloque completo)' : String(v));
                                return (
                                    <li key={i} className={c.type}>
                                        <span className="cm-change-type">{c.type === 'add' ? 'Agregado' : c.type === 'remove' ? 'Quitado' : 'Editado'}</span>
                                        <strong>{pathLabel(original || draft, c.path)}</strong>
                                        {c.type === 'edit' && (
                                            <div className="cm-change-diff">
                                                <span className="old">{show(before)}</span>
                                                <span className="new">{show(after)}</span>
                                            </div>
                                        )}
                                    </li>
                                );
                            })}
                        </ul>
                        <div className="cm-modal-actions">
                            <button className="cm-btn ghost" onClick={downloadBackup}><Download size={15} /> Descargar respaldo</button>
                            <button className="cm-btn primary" disabled={saving} onClick={save}>{saving ? 'Guardando…' : 'Sí, guardar cambios'}</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default CurriculumEditor;
