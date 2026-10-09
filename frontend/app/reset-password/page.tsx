'use client';
import {useEffect,useState} from 'react';
import {api} from '../types';

export default function ResetPassword(){
 const [token,setToken]=useState(''),[password,setPassword]=useState(''),[confirm,setConfirm]=useState(''),[busy,setBusy]=useState(false),[done,setDone]=useState(false),[error,setError]=useState('');
 useEffect(()=>{setToken(new URLSearchParams(window.location.hash.slice(1)).get('token')||'');window.history.replaceState(null,'',window.location.pathname)},[]);
 return <main style={{maxWidth:520,margin:'60px auto',padding:24}}><h1>Reset your password</h1>{done?<><p>Your password has been updated. Please sign in again.</p><a href="/">Return to sign in</a></>:<form className="form-stack" onSubmit={async e=>{e.preventDefault();if(password!==confirm){setError('Passwords do not match.');return}setBusy(true);setError('');try{await api('/auth/password-reset','POST',{token,password});setToken('');setPassword('');setConfirm('');setDone(true)}catch(e){setError(e instanceof Error?e.message:'Unable to reset password.')}finally{setBusy(false)}}}><p>Choose a new password of at least 10 characters.</p>{!token&&<p>Open the reset link from your support email. If it has expired, request a new one.</p>}<label>New password<input type="password" autoComplete="new-password" minLength={10} maxLength={128} required value={password} onChange={e=>setPassword(e.target.value)}/></label><label>Confirm password<input type="password" autoComplete="new-password" minLength={10} maxLength={128} required value={confirm} onChange={e=>setConfirm(e.target.value)}/></label>{error&&<p role="alert">{error}</p>}<button className="button primary" disabled={busy||!token}>{busy?'Updating…':'Update password'}</button><a href="/">Return to KathhaVerse</a></form>}</main>;
}

