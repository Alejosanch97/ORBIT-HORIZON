import React, { useState, useEffect, useRef } from 'react';
import '../Styles/datatable.css';
import { Table, Save, Plus, Trash2, ClipboardPaste, Database } from 'lucide-react';

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
                    <p className="dt-subtitle">Carga masiva estilo Excel. Pega con Ctrl+V directo desde tu hoja de cálculo.</p>
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

            {toast && (
                <div className={`dt-toast ${toast.type}`}>{toast.message}</div>
            )}
        </div>
    );
};

export default DataTableEditor;