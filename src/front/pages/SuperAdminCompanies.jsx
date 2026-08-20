import React, { useState, useEffect } from 'react';
import '../Styles/superadmin.css';
import { Building2, Plus, Check, MapPin, Phone, Mail } from 'lucide-react';

const API = `${import.meta.env.VITE_BACKEND_URL}/api`;

export const SuperAdminCompanies = ({ userData }) => {
    const [colegios, setColegios] = useState([]);
    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [toast, setToast] = useState(null);
    const [form, setForm] = useState({
        nombre: '', direccion: '', ciudad: '', telefono: '', email_contacto: ''
    });

    const showToast = (message, type = 'success') => {
        setToast({ message, type });
        setTimeout(() => setToast(null), 3000);
    };

    const fetchColegios = async () => {
        setLoading(true);
        try {
            const resp = await fetch(`${API}/admin/colegios`);
            const result = await resp.json();
            if (result.status === 'success') setColegios(result.data);
        } catch (e) { console.error(e); }
        setLoading(false);
    };

    useEffect(() => { fetchColegios(); }, []);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!form.nombre.trim()) { showToast('El nombre es obligatorio', 'error'); return; }
        setSaving(true);
        try {
            const resp = await fetch(`${API}/admin/colegios`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ data: form })
            });
            const result = await resp.json();
            if (result.status === 'success') {
                setColegios(prev => [...prev, result.data]);
                setForm({ nombre: '', direccion: '', ciudad: '', telefono: '', email_contacto: '' });
                showToast('Empresa creada correctamente');
            } else {
                showToast(result.message || 'No se pudo crear', 'error');
            }
        } catch (e) {
            console.error(e);
            showToast('Error de conexión', 'error');
        }
        setSaving(false);
    };

    return (
        <div className="sa-container">
            <div className="sa-head">
                <div className="sa-head-icon"><Building2 size={22} strokeWidth={2} /></div>
                <div>
                    <h2 className="sa-title">Empresas</h2>
                    <p className="sa-subtitle">Crea y administra las instituciones de la plataforma</p>
                </div>
            </div>

            <div className="sa-grid">
                {/* Formulario */}
                <section className="sa-panel">
                    <h3 className="sa-panel-title"><Plus size={16} strokeWidth={2.4} /> Nueva empresa</h3>
                    <form className="sa-form" onSubmit={handleSubmit}>
                        <div className="sa-field">
                            <label>Nombre <em>*</em></label>
                            <input type="text" value={form.nombre}
                                onChange={e => setForm(f => ({ ...f, nombre: e.target.value }))}
                                placeholder="Empresa" required />
                        </div>
                        <div className="sa-field">
                            <label>Ciudad</label>
                            <input type="text" value={form.ciudad}
                                onChange={e => setForm(f => ({ ...f, ciudad: e.target.value }))}
                                placeholder="Ciudad" />
                        </div>
                        <div className="sa-field">
                            <label>Dirección</label>
                            <input type="text" value={form.direccion}
                                onChange={e => setForm(f => ({ ...f, direccion: e.target.value }))}
                                placeholder="Dirección" />
                        </div>
                        <div className="sa-field-row">
                            <div className="sa-field">
                                <label>Teléfono</label>
                                <input type="text" value={form.telefono}
                                    onChange={e => setForm(f => ({ ...f, telefono: e.target.value }))}
                                    placeholder="+57 300 000 0000" />
                            </div>
                            <div className="sa-field">
                                <label>Email de contacto</label>
                                <input type="email" value={form.email_contacto}
                                    onChange={e => setForm(f => ({ ...f, email_contacto: e.target.value }))}
                                    placeholder="contacto@colegio.edu.co" />
                            </div>
                        </div>
                        <button type="submit" className="sa-btn primary" disabled={saving}>
                            {saving ? 'Guardando...' : 'Crear empresa'}
                        </button>
                    </form>
                </section>

                {/* Lista */}
                <section className="sa-panel">
                    <h3 className="sa-panel-title"><Building2 size={16} strokeWidth={2.4} /> Empresas registradas ({colegios.length})</h3>
                    {loading ? (
                        <p className="sa-empty">Cargando...</p>
                    ) : colegios.length === 0 ? (
                        <p className="sa-empty">Aún no hay empresas. Crea la primera.</p>
                    ) : (
                        <div className="sa-company-list">
                            {colegios.map(c => (
                                <div key={c.id} className="sa-company-card">
                                    <div className="sa-company-avatar">{c.nombre?.charAt(0)}</div>
                                    <div className="sa-company-info">
                                        <strong>{c.nombre}</strong>
                                        <div className="sa-company-meta">
                                            {c.ciudad && <span><MapPin size={11} /> {c.ciudad}</span>}
                                            {c.telefono && <span><Phone size={11} /> {c.telefono}</span>}
                                            {c.email_contacto && <span><Mail size={11} /> {c.email_contacto}</span>}
                                        </div>
                                    </div>
                                    <span className="sa-company-id">ID {c.id}</span>
                                </div>
                            ))}
                        </div>
                    )}
                </section>
            </div>

            {toast && (
                <div className={`sa-toast ${toast.type}`}>
                    {toast.type === 'success' && <Check size={15} strokeWidth={3} />}
                    {toast.message}
                </div>
            )}
        </div>
    );
};

export default SuperAdminCompanies;