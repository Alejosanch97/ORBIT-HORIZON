import React, { useState, useEffect } from 'react';
import '../Styles/superadmin.css';
import { UserPlus, Check, Users } from 'lucide-react';

const API = `${import.meta.env.VITE_BACKEND_URL}/api`;

const ROLES = ['teacher', 'admin', 'Super Admin'];

export const SuperAdminUsers = ({ userData }) => {
    const [colegios, setColegios] = useState([]);
    const [selectedColegio, setSelectedColegio] = useState(
        localStorage.getItem('sa_selected_colegio') || ''
    );
    const [teachers, setTeachers] = useState([]);
    const [saving, setSaving] = useState(false);
    const [toast, setToast] = useState(null);
    const [form, setForm] = useState({
        User_Key: '', Teacher_Name: '', Password: '',
        Assigned_Grade: '', Assigned_Subject: '', ROL: 'teacher'
    });

    const showToast = (message, type = 'success') => {
        setToast({ message, type });
        setTimeout(() => setToast(null), 3000);
    };

    useEffect(() => {
        (async () => {
            try {
                const resp = await fetch(`${API}/admin/colegios`);
                const result = await resp.json();
                if (result.status === 'success') setColegios(result.data);
            } catch (e) { console.error(e); }
        })();
    }, []);

    // Cargar los usuarios de la empresa seleccionada
    useEffect(() => {
        if (!selectedColegio) { setTeachers([]); return; }
        localStorage.setItem('sa_selected_colegio', selectedColegio);
        (async () => {
            try {
                const resp = await fetch(`${API}/teachers-users`);
                const result = await resp.json();
                const all = result?.data || [];
                setTeachers(all.filter(t => String(t.colegio_id) === String(selectedColegio)));
            } catch (e) { console.error(e); }
        })();
    }, [selectedColegio]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!selectedColegio) { showToast('Selecciona una empresa primero', 'error'); return; }
        if (!form.User_Key.trim() || !form.Password.trim() || !form.Teacher_Name.trim()) {
            showToast('Usuario, nombre y contraseña son obligatorios', 'error'); return;
        }
        setSaving(true);
        try {
            const resp = await fetch(`${API}/admin/users`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ data: { ...form, colegio_id: Number(selectedColegio) } })
            });
            const result = await resp.json();
            if (result.status === 'success') {
                setTeachers(prev => [...prev, result.data]);
                setForm({ User_Key: '', Teacher_Name: '', Password: '', Assigned_Grade: '', Assigned_Subject: '', ROL: 'teacher' });
                showToast('Usuario creado correctamente');
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
                <div className="sa-head-icon"><UserPlus size={22} strokeWidth={2} /></div>
                <div>
                    <h2 className="sa-title">Usuarios</h2>
                    <p className="sa-subtitle">Crea docentes y administradores por empresa</p>
                </div>
            </div>

            {/* Selector de empresa */}
            <div className="sa-company-selector">
                <label>Empresa activa</label>
                <select value={selectedColegio} onChange={e => setSelectedColegio(e.target.value)}>
                    <option value="">— Selecciona una empresa —</option>
                    {colegios.map(c => (
                        <option key={c.id} value={c.id}>{c.nombre}</option>
                    ))}
                </select>
            </div>

            {!selectedColegio ? (
                <div className="sa-placeholder">
                    <Users size={40} strokeWidth={1.5} />
                    <p>Selecciona una empresa para gestionar sus usuarios.</p>
                </div>
            ) : (
                <div className="sa-grid">
                    {/* Formulario */}
                    <section className="sa-panel">
                        <h3 className="sa-panel-title"><UserPlus size={16} strokeWidth={2.4} /> Nuevo usuario</h3>
                        <form className="sa-form" onSubmit={handleSubmit}>
                            <div className="sa-field-row">
                                <div className="sa-field">
                                    <label>User Key <em>*</em></label>
                                    <input type="text" value={form.User_Key}
                                        onChange={e => setForm(f => ({ ...f, User_Key: e.target.value }))}
                                        placeholder="User" required />
                                </div>
                                <div className="sa-field">
                                    <label>Contraseña <em>*</em></label>
                                    <input type="text" value={form.Password}
                                        onChange={e => setForm(f => ({ ...f, Password: e.target.value }))}
                                        placeholder="••••••" required />
                                </div>
                            </div>
                            <div className="sa-field">
                                <label>Nombre completo <em>*</em></label>
                                <input type="text" value={form.Teacher_Name}
                                    onChange={e => setForm(f => ({ ...f, Teacher_Name: e.target.value }))}
                                    placeholder="Nombre" required />
                            </div>
                            <div className="sa-field-row">
                                <div className="sa-field">
                                    <label>Grado asignado</label>
                                    <input type="text" value={form.Assigned_Grade}
                                        onChange={e => setForm(f => ({ ...f, Assigned_Grade: e.target.value }))}
                                        placeholder="Grade" />
                                </div>
                                <div className="sa-field">
                                    <label>Materia asignada</label>
                                    <input type="text" value={form.Assigned_Subject}
                                        onChange={e => setForm(f => ({ ...f, Assigned_Subject: e.target.value }))}
                                        placeholder="Subject" />
                                </div>
                            </div>
                            <div className="sa-field">
                                <label>Rol</label>
                                <select value={form.ROL}
                                    onChange={e => setForm(f => ({ ...f, ROL: e.target.value }))}>
                                    {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
                                </select>
                            </div>
                            <button type="submit" className="sa-btn primary" disabled={saving}>
                                {saving ? 'Guardando...' : 'Crear usuario'}
                            </button>
                        </form>
                    </section>

                    {/* Lista */}
                    <section className="sa-panel">
                        <h3 className="sa-panel-title"><Users size={16} strokeWidth={2.4} /> Usuarios ({teachers.length})</h3>
                        {teachers.length === 0 ? (
                            <p className="sa-empty">Esta empresa no tiene usuarios aún.</p>
                        ) : (
                            <div className="sa-user-list">
                                {teachers.map(t => (
                                    <div key={t.id} className="sa-user-card">
                                        <div className="sa-user-avatar">{t.Teacher_Name?.charAt(0)}</div>
                                        <div className="sa-user-info">
                                            <strong>{t.Teacher_Name}</strong>
                                            <span className="sa-user-key">@{t.User_Key}</span>
                                            <div className="sa-user-meta">
                                                {t.Assigned_Grade && <span>{t.Assigned_Grade}</span>}
                                                {t.Assigned_Subject && <span>{t.Assigned_Subject}</span>}
                                            </div>
                                        </div>
                                        <span className={`sa-role-badge ${String(t.ROL).toLowerCase().replace(' ', '-')}`}>
                                            {t.ROL}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </section>
                </div>
            )}

            {toast && (
                <div className={`sa-toast ${toast.type}`}>
                    {toast.type === 'success' && <Check size={15} strokeWidth={3} />}
                    {toast.message}
                </div>
            )}
        </div>
    );
};

export default SuperAdminUsers;