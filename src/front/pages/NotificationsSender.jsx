import React, { useState, useEffect, useMemo } from 'react';
import useGlobalReducer from '../hooks/useGlobalReducer';
import '../Styles/notificationsSender.css';
import { Send, X, Search, Check, Users, History } from 'lucide-react';

const norm = (v) => String(v || '').trim().toUpperCase();
const fmtDate = (iso) => { 
    if (!iso) return ''; 
    const d = new Date(iso); 
    return isNaN(d) ? '' : d.toLocaleDateString('es', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }); 
};

const QUICK = [
    "Profe, aún no has subido los datos de la actividad. ¿Puedes revisarlo?",
    "Profe, no me has reportado si los estudiantes avanzaron o no en nivelación.",
    "Recuerda registrar las asignaciones de tus estudiantes en alerta esta semana.",
    "Por favor actualiza el veredicto de tus estudiantes de acompañamiento.",
];

export const NotificationsSender = ({ userData, onClose, onNotificationSent }) => {
    const { store, dispatch } = useGlobalReducer();
    const senderName = String(userData.Teacher_Name || userData.User_Key || '').trim();

    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');
    const [selectedKeys, setSelectedKeys] = useState([]); // User_Keys destino
    const [message, setMessage] = useState('');
    const [sending, setSending] = useState(false);
    const [tab, setTab] = useState('send');

    // Cargar docentes y notificaciones desde el backend usando las nuevas rutas
    useEffect(() => {
        const loadData = async () => {
            setLoading(true);
            try {
                const [respTeachers, respNotifications] = await Promise.all([
                    fetch(process.env.BACKEND_URL + '/api/teachers-users'),
                    fetch(process.env.BACKEND_URL + '/api/teacher-notifications')
                ]);

                const teachersData = await respTeachers.json();
                const notificationsData = await respNotifications.json();

                if (teachersData.status === 'success') {
                    dispatch({ type: 'set_teachers', payload: teachersData.data });
                }

                if (notificationsData.status === 'success') {
                    dispatch({ type: 'set_notifications', payload: notificationsData.data });
                }
            } catch (e) { 
                console.error('Error cargando datos:', e); 
            } finally {
                setLoading(false);
            }
        };
        loadData();
    }, [dispatch]);

    // Filtrar solo profesores con ENGLISH en Assigned_Subject utilizando el store global
    const teachers = useMemo(() => {
        const allTeachers = Array.isArray(store.teachers) ? store.teachers : [];
        return allTeachers.filter(t => norm(t.Assigned_Subject).includes('ENGLISH'));
    }, [store.teachers]);

    const filtered = useMemo(() => {
        if (!search) return teachers;
        return teachers.filter(t => norm(t.Teacher_Name).includes(norm(search)) || norm(t.User_Key).includes(norm(search)));
    }, [teachers, search]);

    const sent = Array.isArray(store.notifications) ? store.notifications : [];

    const toggleTeacher = (userKey) => {
        setSelectedKeys(prev => prev.includes(userKey) ? prev.filter(k => k !== userKey) : [...prev, userKey]);
    };

    const send = async () => {
        if (!message.trim() || selectedKeys.length === 0) return;
        setSending(true);
        const targets = teachers.filter(t => selectedKeys.includes(String(t.User_Key).trim()));

        try {
            // Enviar peticiones POST paralelas a la nueva ruta de notificaciones
            await Promise.all(targets.map(t => fetch(process.env.BACKEND_URL + '/api/teacher-notifications', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    Target_User_Key: String(t.User_Key).trim(),
                    Target_Teacher_Name: t.Teacher_Name,
                    Message: message.trim(),
                    Sender: senderName
                })
            })));

            // Volver a consultar o sincronizar el historial actualizado
            const resp = await fetch(process.env.BACKEND_URL + '/api/teacher-notifications');
            const result = await resp.json();
            if (result.status === 'success') {
                dispatch({ type: 'set_notifications', payload: result.data });
            }

            // Notificar al dashboard que se envió con éxito
            if (onNotificationSent) {
                await onNotificationSent();
            }

        } catch (e) { 
            console.error('Error enviando notificaciones:', e); 
        } finally {
            setMessage('');
            setSelectedKeys([]);
            setSending(false);
            setTab('history');
        }
    };

    return (
        <div className="ns-overlay" onClick={onClose}>
            <div className="ns-modal" onClick={e => e.stopPropagation()}>
                <div className="ns-head">
                    <div>
                        <span className="ns-eyebrow">COORDINACIÓN → DOCENTES</span>
                        <h3>Enviar notificación</h3>
                    </div>
                    <button className="ns-close" onClick={onClose}><X size={18} /></button>
                </div>

                <div className="ns-tabs">
                    <button className={tab === 'send' ? 'on' : ''} onClick={() => setTab('send')}><Send size={14} /> Enviar</button>
                    <button className={tab === 'history' ? 'on' : ''} onClick={() => setTab('history')}><History size={14} /> Historial</button>
                </div>

                {tab === 'send' && (
                    <div className="ns-body">
                        {/* Selección de docentes */}
                        <div className="ns-block">
                            <label><Users size={14} /> Docentes de inglés {selectedKeys.length > 0 && <span className="ns-sel-count">{selectedKeys.length} seleccionados</span>}</label>
                            <div className="ns-search">
                                <Search size={14} />
                                <input placeholder="Buscar docente…" value={search} onChange={e => setSearch(e.target.value)} />
                            </div>
                            <div className="ns-teacher-list">
                                {loading ? <p className="ns-mini-empty">Cargando…</p> : filtered.length === 0 ? <p className="ns-mini-empty">Sin docentes de inglés.</p> : filtered.map(t => {
                                    const key = String(t.User_Key).trim();
                                    const on = selectedKeys.includes(key);
                                    return (
                                        <button key={key} className={`ns-teacher ${on ? 'on' : ''}`} onClick={() => toggleTeacher(key)}>
                                            <span className="ns-check">{on && <Check size={13} />}</span>
                                            <span className="ns-teacher-name">{t.Teacher_Name}</span>
                                            <span className="ns-teacher-key">{t.User_Key}</span>
                                        </button>
                                    );
                                })}
                            </div>
                        </div>

                        {/* Mensaje */}
                        <div className="ns-block">
                            <label>Mensaje</label>
                            <textarea rows={3} placeholder="Escribe tu notificación…" value={message} onChange={e => setMessage(e.target.value)} />
                            <div className="ns-quick">
                                {QUICK.map((q, i) => (
                                    <button key={i} onClick={() => setMessage(q)}>{q.length > 42 ? q.slice(0, 42) + '…' : q}</button>
                                ))}
                            </div>
                        </div>

                        <button className="ns-send" onClick={send} disabled={sending || !message.trim() || selectedKeys.length === 0}>
                            <Send size={16} /> {sending ? 'Enviando…' : `Enviar a ${selectedKeys.length || ''} docente(s)`}
                        </button>
                    </div>
                )}

                {tab === 'history' && (
                    <div className="ns-body">
                        {sent.length === 0 ? (
                            <p className="ns-mini-empty">Aún no has enviado notificaciones.</p>
                        ) : (
                            <div className="ns-history">
                                {[...sent].sort((a, b) => new Date(b.Created_At) - new Date(a.Created_At)).map(n => (
                                    <div key={n.ID_Notification} className="ns-hist-item">
                                        <div className="ns-hist-top">
                                            <strong>{n.Target_Teacher_Name}</strong>
                                            <span className={`ns-status ${n.Status === 'read' ? 'read' : 'unread'}`}>{n.Status === 'read' ? 'Leída' : 'No leída'}</span>
                                        </div>
                                        <p>{n.Message}</p>
                                        <small>{fmtDate(n.Created_At)}</small>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

export default NotificationsSender;