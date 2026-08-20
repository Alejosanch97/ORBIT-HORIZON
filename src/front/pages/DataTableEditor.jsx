import React, { useState, useEffect, useRef } from 'react';
import '../Styles/datatable.css';
import { Table, Save, Plus, Trash2, ClipboardPaste, Database, FileJson, X, Upload } from 'lucide-react';

const API = `${import.meta.env.VITE_BACKEND_URL}/api`;

const EMPTY_ROWS = 8; // filas vacías iniciales para pegar

export const DataTableEditor = ({ userData }) => {
    const [colegios, setColegios] = useState([]);
    const [selectedColegio, setSelectedColegio] = useState(
        localStorage.getItem('sa_selected_colegio') || ''
    );
    const [tables, setTables] = useState([]);
    const [selectedTable, setSelectedTable] = useState('');
    const [columns, setColumns] = useState([]);
    const [existingRows, setExistingRows] = useState([]);
    const [newRows, setNewRows] = useState([]);
    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [toast, setToast] = useState(null);

    // --- Import JSON ---
    const [showJsonModal, setShowJsonModal] = useState(false);
    const [jsonText, setJsonText] = useState('');
    const [jsonBatchRange, setJsonBatchRange] = useState('0-200'); // Lote por defecto
    const fileInputRef = useRef(null);

    const showToast = (message, type = 'success') => {
        setToast({ message, type });
        setTimeout(() => setToast(null), 3200);
    };

    // Cargar empresas y catálogo de tablas al montar
    useEffect(() => {
        (async () => {
            try {
                const [colResp, tblResp] = await Promise.all([
                    fetch(`${API}/admin/colegios`).then(r => r.json()),
                    fetch(`${API}/admin/tables`).then(r => r.json()),
                ]);
                if (colResp.status === 'success') setColegios(colResp.data);
                if (tblResp.status === 'success') setTables(tblResp.tables);
            } catch (e) { console.error(e); }
        })();
    }, []);

    useEffect(() => {
        if (selectedColegio) localStorage.setItem('sa_selected_colegio', selectedColegio);
        // Si ya hay una tabla abierta, recárgala con el filtro de la nueva empresa
        if (selectedTable) {
            reloadRows(selectedTable, selectedColegio);
        }
    }, [selectedColegio]);

    // Carga las filas de una tabla para un colegio dado (recibe el id como parámetro,
    // así nunca usa un valor viejo del estado)
    const reloadRows = async (tableName, colegioId) => {
        if (!tableName) { setColumns([]); setExistingRows([]); setNewRows([]); return; }
        setLoading(true);
        try {
            const url = colegioId
                ? `${API}/admin/table/${tableName}?colegio_id=${colegioId}`
                : `${API}/admin/table/${tableName}`;
            const resp = await fetch(url);
            const result = await resp.json();
            if (result.status === 'success') {
                const cols = (result.columns || []).filter(c => c !== 'colegio_id');
                setColumns(cols);
                setExistingRows(result.rows || []);
                setNewRows(Array.from({ length: EMPTY_ROWS }, () => makeEmptyRow(cols)));
            } else {
                showToast(result.message || 'No se pudo cargar la tabla', 'error');
            }
        } catch (e) {
            console.error(e);
            showToast('Error de conexión', 'error');
        }
        setLoading(false);
    };

    // Al elegir tabla desde el select
    const loadTable = (tableName) => {
        setSelectedTable(tableName);
        reloadRows(tableName, selectedColegio);
    };

    const makeEmptyRow = (cols) => {
        const r = {};
        cols.forEach(c => { r[c] = ''; });
        return r;
    };

    // Editar una celda nueva
    const updateCell = (rowIdx, col, value) => {
        setNewRows(prev => {
            const copy = [...prev];
            copy[rowIdx] = { ...copy[rowIdx], [col]: value };
            return copy;
        });
    };

    // PEGADO MASIVO desde Excel: respeta tabs (columnas) y saltos de línea (filas)
    // Parser TSV que respeta comillas: los \n y \t dentro de "..." NO separan
    const parseClipboard = (text) => {
        const rows = [];
        let row = [];
        let cell = '';
        let inQuotes = false;
        let i = 0;

        while (i < text.length) {
            const char = text[i];
            const next = text[i + 1];

            if (inQuotes) {
                if (char === '"' && next === '"') {
                    // Comilla escapada ("") → una comilla literal
                    cell += '"';
                    i += 2;
                    continue;
                }
                if (char === '"') {
                    // Cierra el bloque entre comillas
                    inQuotes = false;
                    i++;
                    continue;
                }
                // Cualquier otra cosa (incluye \n y \t) es contenido de la celda
                cell += char;
                i++;
                continue;
            }

            // Fuera de comillas
            if (char === '"') {
                inQuotes = true;
                i++;
                continue;
            }
            if (char === '\t') {
                row.push(cell);
                cell = '';
                i++;
                continue;
            }
            if (char === '\r') {
                i++; // ignora retornos de carro
                continue;
            }
            if (char === '\n') {
                row.push(cell);
                rows.push(row);
                row = [];
                cell = '';
                i++;
                continue;
            }
            cell += char;
            i++;
        }
        // Última celda/fila pendiente
        row.push(cell);
        rows.push(row);

        // Descarta una última fila totalmente vacía (por el \n final típico de Excel)
        if (rows.length > 1) {
            const last = rows[rows.length - 1];
            if (last.length === 1 && last[0].trim() === '') rows.pop();
        }
        return rows;
    };

    // PEGADO MASIVO desde Excel: respeta celdas multilínea entre comillas
    const handlePaste = (e, startRowIdx, startColIdx) => {
        const text = e.clipboardData.getData('text/plain');
        if (!text) return;
        // Si es una sola celda simple sin tabs ni saltos, deja el pegado normal del input
        if (!text.includes('\t') && !text.includes('\n') && !text.includes('"')) return;

        e.preventDefault();
        const parsed = parseClipboard(text);

        setNewRows(prev => {
            const copy = [...prev];
            parsed.forEach((cells, r) => {
                const targetRow = startRowIdx + r;
                while (copy.length <= targetRow) copy.push(makeEmptyRow(columns));
                cells.forEach((val, c) => {
                    const targetCol = columns[startColIdx + c];
                    if (targetCol) {
                        copy[targetRow] = { ...copy[targetRow], [targetCol]: val };
                    }
                });
            });
            return copy;
        });
    };

    // ---------- IMPORTAR JSON ----------

    // Normaliza una clave: minúsculas, sin acentos, espacios/guiones -> _
    const normalizeKey = (k) =>
        String(k).trim()
            .toLowerCase()
            .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
            .replace(/%/g, 'percent')
            .replace(/[\s\-]+/g, '_')
            .replace(/_+/g, '_');

    // Mapea las claves del JSON a las columnas reales de la tabla.
    // Maneja "Vocabulary Big 5" -> Big_5, "% Status" -> Percent_Status, etc.
    const buildColLookup = () => {
        const colByNorm = {};
        columns.forEach(col => { colByNorm[normalizeKey(col)] = col; });
        // Alias manuales para claves que no coinciden por normalización
        const aliases = {
            'vocabulary_big_5': 'Big_5',
            'vocabulary_big5': 'Big_5',
            'big5': 'Big_5',
            'big_5': 'Big_5',
            'percent_status': 'Percent_Status',
            'status': 'Percent_Status',
        };
        return { colByNorm, aliases };
    };

    const mapJsonRowToColumns = (obj, lookup) => {
        const { colByNorm, aliases } = lookup;
        const row = makeEmptyRow(columns);
        Object.entries(obj).forEach(([rawKey, val]) => {
            const nk = normalizeKey(rawKey);
            const targetCol = colByNorm[nk] || aliases[nk];
            if (targetCol && columns.includes(targetCol)) {
                row[targetCol] = (val !== null && typeof val === 'object')
                    ? JSON.stringify(val)
                    : (val ?? '');
            }
        });
        return row;
    };

    // Procesa el texto JSON (array de objetos o un solo objeto) y llena newRows por lotes
    const importJson = () => {
        if (!selectedTable) { showToast('Selecciona una tabla primero', 'error'); return; }
        let data;
        try {
            data = JSON.parse(jsonText);
        } catch (e) {
            showToast('JSON inválido, revisa el formato', 'error');
            return;
        }
        const arr = Array.isArray(data) ? data : [data];
        if (arr.length === 0) { showToast('El JSON está vacío', 'error'); return; }

        const lookup = buildColLookup();
        const mapped = arr.map(o => mapJsonRowToColumns(o, lookup));

        // Filtrar por el rango de lotes seleccionado
        let finalRows = mapped;
        if (jsonBatchRange !== 'all') {
            const [start, end] = jsonBatchRange.split('-').map(Number);
            finalRows = mapped.slice(start, end);
        }

        // Reemplaza las filas nuevas
        setNewRows(finalRows);
        setShowJsonModal(false);
        showToast(`${finalRows.length} fila(s) cargadas (${jsonBatchRange}). Revisa y presiona Guardar.`);
    };

    const handleFileUpload = (e) => {
        const file = e.target.files?.[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (ev) => setJsonText(ev.target.result);
        reader.onerror = () => showToast('No se pudo leer el archivo', 'error');
        reader.readAsText(file);
        e.target.value = ''; // permite re-subir el mismo archivo
    };

    const addEmptyRows = () => {
        setNewRows(prev => [...prev, ...Array.from({ length: 5 }, () => makeEmptyRow(columns))]);
    };

    const removeNewRow = (idx) => {
        setNewRows(prev => prev.filter((_, i) => i !== idx));
    };

    const clearNewRows = () => {
        setNewRows(Array.from({ length: EMPTY_ROWS }, () => makeEmptyRow(columns)));
    };

    // Guardar: filtra filas con algún dato y las manda al backend
    const handleSave = async () => {
        if (!selectedTable) { showToast('Selecciona una tabla', 'error'); return; }
        const rowsToSave = newRows.filter(r =>
            Object.values(r).some(v => String(v).trim() !== '')
        );
        if (rowsToSave.length === 0) { showToast('No hay filas nuevas para guardar', 'error'); return; }

        setSaving(true);
        try {
            const resp = await fetch(`${API}/admin/table/${selectedTable}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    colegio_id: selectedColegio ? Number(selectedColegio) : null,
                    rows: rowsToSave
                })
            });
            const result = await resp.json();
            if (result.status === 'success') {
                showToast(`${result.created} fila(s) guardada(s)`);
                await reloadRows(selectedTable, selectedColegio); // recarga con el filtro de empresa
            } else {
                showToast(result.message || 'Error al guardar', 'error');
            }
        } catch (e) {
            console.error(e);
            showToast('Error de conexión', 'error');
        }
        setSaving(false);
    };

    return (
        <div className="dt-container">
            <div className="dt-head">
                <div className="dt-head-icon"><Table size={22} strokeWidth={2} /></div>
                <div>
                    <h2 className="dt-title">Datos en tabla</h2>
                    <p className="dt-subtitle">Carga masiva estilo Excel. Pega con Ctrl+V directo desde tu hoja de cálculo o importa un JSON.</p>
                </div>
            </div>

            {/* Selectores */}
            <div className="dt-selectors">
                <div className="dt-select-group">
                    <label>Empresa</label>
                    <select value={selectedColegio} onChange={e => setSelectedColegio(e.target.value)}>
                        <option value="">— Todas / sin filtro —</option>
                        {colegios.map(c => <option key={c.id} value={c.id}>{c.nombre}</option>)}
                    </select>
                </div>
                <div className="dt-select-group">
                    <label>Tabla</label>
                    <select value={selectedTable} onChange={e => loadTable(e.target.value)}>
                        <option value="">— Selecciona una tabla —</option>
                        {tables.map(t => <option key={t.name} value={t.name}>{t.name}</option>)}
                    </select>
                </div>
            </div>

            {!selectedTable ? (
                <div className="dt-placeholder">
                    <Database size={40} strokeWidth={1.5} />
                    <p>Selecciona una tabla para ver y cargar datos.</p>
                </div>
            ) : loading ? (
                <div className="dt-placeholder"><p>Cargando tabla...</p></div>
            ) : (
                <>
                    {/* Barra de acciones */}
                    <div className="dt-toolbar">
                        <span className="dt-count">
                            <Database size={13} /> {existingRows.length} existentes
                        </span>
                        <div className="dt-toolbar-actions">
                            <button className="dt-btn ghost" onClick={() => setShowJsonModal(true)}>
                                <FileJson size={14} /> Subir JSON
                            </button>
                            <button className="dt-btn ghost" onClick={addEmptyRows}>
                                <Plus size={14} /> Más filas
                            </button>
                            <button className="dt-btn ghost" onClick={clearNewRows}>
                                Limpiar nuevas
                            </button>
                            <button className="dt-btn primary" onClick={handleSave} disabled={saving}>
                                <Save size={14} /> {saving ? 'Guardando...' : 'Guardar'}
                            </button>
                        </div>
                    </div>

                    <div className="dt-paste-hint">
                        <ClipboardPaste size={14} />
                        Haz clic en la primera celda vacía y pega (Ctrl+V) — las columnas y filas se llenan solas.
                    </div>

                    {/* Mini-Excel */}
                    <div className="dt-table-wrap">
                        <table className="dt-table">
                            <thead>
                                <tr>
                                    <th className="dt-rownum">#</th>
                                    {columns.map(col => <th key={col}>{col}</th>)}
                                    <th className="dt-actions-col"></th>
                                </tr>
                            </thead>
                            <tbody>
                                {/* Filas existentes (solo lectura) */}
                                {existingRows.map((row, i) => (
                                    <tr key={`ex-${row.id || i}`} className="dt-row-existing">
                                        <td className="dt-rownum">{i + 1}</td>
                                        {columns.map(col => (
                                            <td key={col} title={row[col]}>
                                                <div className="dt-cell-readonly">{row[col]}</div>
                                            </td>
                                        ))}
                                        <td className="dt-actions-col"></td>
                                    </tr>
                                ))}

                                {/* Separador visual */}
                                <tr className="dt-divider-row">
                                    <td colSpan={columns.length + 2}>
                                        <span>↓ Filas nuevas (pega aquí) ↓</span>
                                    </td>
                                </tr>

                                {/* Filas nuevas (editables) */}
                                {newRows.map((row, rIdx) => (
                                    <tr key={`new-${rIdx}`} className="dt-row-new">
                                        <td className="dt-rownum">{existingRows.length + rIdx + 1}</td>
                                        {columns.map((col, cIdx) => (
                                            <td key={col}>
                                                <input
                                                    className="dt-cell-input"
                                                    value={row[col] || ''}
                                                    onChange={e => updateCell(rIdx, col, e.target.value)}
                                                    onPaste={e => handlePaste(e, rIdx, cIdx)}
                                                />
                                            </td>
                                        ))}
                                        <td className="dt-actions-col">
                                            <button className="dt-del-row" onClick={() => removeNewRow(rIdx)} title="Quitar fila">
                                                <Trash2 size={13} />
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </>
            )}

            {/* Modal Importar JSON */}
            {showJsonModal && (
                <div className="dt-modal-overlay" onClick={() => setShowJsonModal(false)}>
                    <div className="dt-modal" onClick={e => e.stopPropagation()}>
                        <div className="dt-modal-head">
                            <div className="dt-modal-title">
                                <FileJson size={18} /> Importar JSON
                            </div>
                            <button className="dt-modal-close" onClick={() => setShowJsonModal(false)}>
                                <X size={18} />
                            </button>
                        </div>

                        <p className="dt-modal-hint">
                            Pega un arreglo JSON o sube un archivo <code>.json</code>. Las claves se mapean
                            automáticamente a las columnas (ej. <code>Vocabulary Big 5</code> → <code>Big_5</code>,
                            <code> % Status</code> → <code>Percent_Status</code>). Los objetos anidados se
                            guardan como texto JSON.
                        </p>

                        <div className="dt-modal-actions-top" style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap', marginBottom: '10px' }}>
                            <button className="dt-btn ghost" onClick={() => fileInputRef.current?.click()}>
                                <Upload size={14} /> Subir archivo .json
                            </button>
                            <input
                                ref={fileInputRef}
                                type="file"
                                accept=".json,application/json"
                                style={{ display: 'none' }}
                                onChange={handleFileUpload}
                            />
                            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px' }}>
                                <label style={{ fontWeight: '500' }}>Lote:</label>
                                <select 
                                    value={jsonBatchRange} 
                                    onChange={e => setJsonBatchRange(e.target.value)}
                                    style={{ padding: '4px 8px', borderRadius: '4px', border: '1px solid #ccc' }}
                                >
                                    <option value="0-200">Filas 1 - 200</option>
                                    <option value="200-400">Filas 201 - 400</option>
                                    <option value="400-600">Filas 401 - 600</option>
                                    <option value="600-800">Filas 601 - 800</option>
                                    <option value="800-1000">Filas 801 - 1000</option>
                                    <option value="1000-1200">Filas 1001 - 1200</option>
                                    <option value="1200-1400">Filas 1201 - 1400</option>
                                    <option value="1400-1700">Filas 1401 - 1700</option>
                                    <option value="all">Todo completo (Sin corte)</option>
                                </select>
                            </div>
                        </div>

                        <textarea
                            className="dt-json-textarea"
                            value={jsonText}
                            onChange={e => setJsonText(e.target.value)}
                            placeholder='[ { "ID_Setup": "...", "Grade": "...", "Vocabulary Big 5": "..." } ]'
                            rows={10}
                        />

                        <div className="dt-modal-footer">
                            <button className="dt-btn ghost" onClick={() => { setJsonText(''); }}>
                                Limpiar
                            </button>
                            <button className="dt-btn primary" onClick={importJson}>
                                <FileJson size={14} /> Cargar en la tabla
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {toast && (
                <div className={`dt-toast ${toast.type}`}>{toast.message}</div>
            )}
        </div>
    );
};

export default DataTableEditor;