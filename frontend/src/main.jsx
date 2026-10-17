import React, {useState} from 'react';
import {createRoot} from 'react-dom/client';
import './style.css';

const empty = {name:'', email:'', phone:'', password:'', confirm:''};
function App() {
  const [form, setForm] = useState(empty);
  const [errors, setErrors] = useState({});
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [success, setSuccess] = useState(null);
  function validate() {
    const e = {};
    if(form.name.trim().length < 2 || form.name.trim().length > 80 || !/\p{L}/u.test(form.name)) e.name = 'Enter a name with 2–80 characters and at least one letter.';
    if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim())) e.email = 'Enter a valid email address.';
    if(!/^03[0-9]{9}$/.test(form.phone.trim())) e.phone = 'Use 11 digits, for example 03001234567.';
    if(form.password.length < 8 || form.password.length > 128 || !/[A-Za-z]/.test(form.password) || !/[0-9]/.test(form.password)) e.password = 'Use 8–128 characters, including a letter and number.';
    if(form.confirm !== form.password) e.confirm = 'Passwords must match.';
    return e;
  }
  async function submit(event) {
    event.preventDefault();
    if(busy) return;
    setMessage(''); setSuccess(null);
    const e = validate(); setErrors(e);
    if(Object.keys(e).length) return;
    setBusy(true);
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    try {
      const {confirm, ...payload} = form;
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/register`, {
        method:'POST', headers:{'Content-Type':'application/json'},
        body:JSON.stringify(payload), signal:controller.signal
      });
      const data = await response.json();
      if(response.status === 422 && Array.isArray(data.detail)) {
        const fields = {};
        for(const error of data.detail) fields[error.loc.at(-1)] = error.msg.replace(/^Value error, /, '');
        setErrors(fields); return;
      }
      if(!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Unable to save your registration.');
      setSuccess(data); setForm(empty);
    } catch(error) {
      setMessage(error.name === 'AbortError' ? 'Request timed out. Your registration may have saved; retrying will check for a duplicate email.' : error.message === 'Failed to fetch' ? 'Cannot connect to the API. Check that the backend is running.' : error.message);
    } finally { clearTimeout(timeout); setBusy(false); }
  }
  const fields = [ ['name','Full name','text','Muhammad Danial','name'], ['email','Email address','email','you@example.com','email'], ['phone','Mobile number','tel','03001234567','tel'], ['password','Password','password','At least 8 characters','new-password'], ['confirm','Confirm password','password','Repeat your password','new-password'] ];
  return <main><aside><div className="brand"><span className="mark">F</span> Formspace</div><div><span className="tag">YOUR FIRST FULL STACK FORM</span><h1>A small form.<br/>A complete workflow.</h1><p>Enter your details, validate your information and create a record in your database.</p><div className="steps"><div><b>01</b><span>React interface</span></div><div><b>02</b><span>FastAPI validation</span></div><div><b>03</b><span>PostgreSQL storage</span></div></div></div><small>Built with React + Python</small></aside><section><div className="card"><span className="tag blue">LET’S GET STARTED</span><h2>Create your account</h2><p className="intro">Fill in your details below.</p>{success && <div className="success" role="status">Registration saved! Your record ID is <strong>{success.id}</strong>.</div>}{message && <div className="alert" role="alert">{message}</div>}<form onSubmit={submit} noValidate>{fields.map(([key,label,type,placeholder,autoComplete]) => <div className="field" key={key}><label htmlFor={key}>{label}</label><input id={key} type={type} autoComplete={autoComplete} placeholder={placeholder} value={form[key]} disabled={busy} maxLength={key === 'name' ? 80 : key === 'email' ? 254 : key === 'phone' ? 11 : 128} aria-invalid={!!errors[key]} aria-describedby={errors[key] ? `${key}-error` : undefined} onChange={event=>setForm({...form,[key]:event.target.value})}/>{errors[key] && <small className="error" id={`${key}-error`}>{errors[key]}</small>}</div>)}<p className="hint">Password: at least one letter and one number.</p><button disabled={busy}>{busy ? 'Saving your account…' : 'Create account →'}</button></form><p className="foot">Your password is stored as an Argon2 hash.</p></div></section></main>;
}
createRoot(document.getElementById('root')).render(<App/>);
