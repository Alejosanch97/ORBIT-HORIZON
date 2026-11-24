import React, { useState } from 'react';
import '../Styles/groqkey.css';
import { KeyRound, ExternalLink, Eye, EyeOff, CheckCircle2, X, Trash2, Sparkles } from 'lucide-react';

const API = `${import.meta.env.VITE_BACKEND_URL}/api`;
const GROQ_URL = 'https://console.groq.com/home';

/* Pop up para que cada docente conecte SU propia API key de Groq.
   - status: { has_key, hint } (lo trae el Dashboard)
   - onSaved(status): se llama al guardar o quitar la key
   - onLater(): cerrar sin configurar (vuelve a salir en el próximo ingreso) */
export const GroqKeyModal = ({ userKey, status, onSaved, onLater, onClose }) => {
    const [key, setKey] = useState('');
    const [show, setShow] = useState(false);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');
    const [done, setDone] = useState(false);
    const [replacing, setReplacing] = useState(!status?.has_key);

    const save = async () => {
        const clean = key.trim();
        if (!clean.startsWith('gsk_')) { setError('La API key de Groq empieza por gsk_. Revisa que la copiaste completa.'); return; }
        setSaving(true); setError('');
        try {
            const resp = await fetch(`${API}/teachers-users/${encodeURIComponent(userKey)}/groq-key`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ api_key: clean })
            });
            const data = await resp.json();
            if (!resp.ok || data.status !== 'success') throw new Error(data.message || 'No se pudo guardar');
            setKey('');
            setDone(true);
            onSaved && onSaved({ has_key: data.has_key, hint: data.hint });
        } catch (e) {
            setError(e.message);
        } finally { setSaving(false); }
    };

    const remove = async () => {
        if (!window.confirm('¿Quitar tu API key? Lumi usará las del colegio, que se pueden agotar.')) return;
        setSaving(true); setError('');
        try {
            const resp = await fetch(`${API}/teachers-users/${encodeURIComponent(userKey)}/groq-key`, { method: 'DELETE' });
            const data = await resp.json();
            if (!resp.ok || data.status !== 'success') throw new Error(data.message || 'No se pudo quitar');
            onSaved && onSaved({ has_key: false, hint: null });
            setReplacing(true);
        } catch (e) { setError(e.message); } finally { setSaving(false); }
    };

    return (
        <div className="gk-bg">
            <div className="gk-card">
                {onClose && <button className="gk-x" onClick={onClose} aria-label="Cerrar"><X size={18} /></button>}

                <div className="gk-head">
                    <div className="gk-icon"><KeyRound size={30} /></div>
                    <div>
                        <span className="gk-kicker">Tu energía para Lumi</span>
                        <h2>{done ? '¡Listo! Lumi ya usa tu key' : !replacing ? 'Tu API key de Groq' : 'Conecta tu propia API key'}</h2>
                    </div>
                </div>

                {done ? (
                    <div className="gk-done">
                        <CheckCircle2 size={46} />
                        <p>Tu key quedó guardada y protegida. Desde ahora, cuando planees con Lumi se usarán <strong>tus propios tokens</strong>. Si algún día se agotan, Lumi usa automáticamente las del colegio.</p>
                        <button className="gk-btn primary" onClick={onClose || onLater}>Empezar a planear</button>
                    </div>
                ) : !replacing ? (
                    <div className="gk-done">
                        <CheckCircle2 size={40} />
                        <p>Ya tienes una API key conectada <code>{status?.hint}</code>. Lumi la usa primero cada vez que planeas.</p>
                        <div className="gk-actions">
                            <button className="gk-btn ghost" onClick={remove} disabled={saving}><Trash2 size={15} /> Quitar</button>
                            <button className="gk-btn primary" onClick={() => setReplacing(true)}>Reemplazar por otra</button>
                        </div>
                        {error && <div className="gk-error">{error}</div>}
                    </div>
                ) : (
                    <>
                        <p className="gk-lead">
                            Para que Lumi nunca se quede sin energía, cada docente usa su propia cuenta gratuita de Groq.
                            Toma 2 minutos y se hace una sola vez.
                        </p>

                        <ol className="gk-steps">
                            <li>
                                <span>1</span>
                                <div>
                                    <strong>Entra a Groq con el correo del colegio</strong>
                                    <p>Abre la consola e inicia sesión con <em>Continuar con Google</em> usando tu cuenta institucional.</p>
                                    <a className="gk-link" href={GROQ_URL} target="_blank" rel="noreferrer">Abrir console.groq.com <ExternalLink size={14} /></a>
                                </div>
                            </li>
                            <li>
                                <span>2</span>
                                <div>
                                    <strong>Crea la API key</strong>
                                    <p>Arriba ve a <b>API Keys</b> → <b>Create API Key</b>. Ponle de nombre <b>Lumi</b>, en Expiration deja <b>No expiration</b> y dale <b>Submit</b>.</p>
                                </div>
                            </li>
                            <li>
                                <span>3</span>
                                <div>
                                    <strong>Cópiala y pégala aquí</strong>
                                    <p>Groq la muestra <b>una sola vez</b> (empieza por <code>gsk_</code>). Cópiala completa y pégala abajo.</p>
                                </div>
                            </li>
                        </ol>

                        <div className="gk-input">
                            <KeyRound size={17} />
                            <input
                                type={show ? 'text' : 'password'}
                                placeholder="gsk_..."
                                value={key}
                                autoComplete="off"
                                spellCheck={false}
                                onChange={e => { setKey(e.target.value); setError(''); }}
                                onKeyDown={e => e.key === 'Enter' && save()}
                            />
                            <button onClick={() => setShow(!show)} title={show ? 'Ocultar' : 'Mostrar'}>
                                {show ? <EyeOff size={17} /> : <Eye size={17} />}
                            </button>
                        </div>
                        {error && <div className="gk-error">{error}</div>}
                        <p className="gk-note"><Sparkles size={13} /> Tu key se guarda protegida: nadie en la plataforma puede verla, ni los administradores.</p>

                        <div className="gk-actions">
                            {onLater && <button className="gk-btn ghost" onClick={onLater}>Más tarde</button>}
                            <button className="gk-btn primary" onClick={save} disabled={saving || !key.trim()}>
                                {saving ? 'Verificando con Groq…' : 'Guardar mi key'}
                            </button>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};

export default GroqKeyModal;
