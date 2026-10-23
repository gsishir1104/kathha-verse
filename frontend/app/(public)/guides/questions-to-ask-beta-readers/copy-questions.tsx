'use client';
import {useState} from 'react';

export default function CopyQuestions({text}: {text: string}) {
  const [status, setStatus] = useState('');
  return <div><button className="public-copy" type="button" onClick={async () => {try {await navigator.clipboard.writeText(text);setStatus('Questions copied. Paste them into your reading brief.');} catch {setStatus('Copy is unavailable here. You can select and copy the questions above.');}}}>Copy the starter questions</button><p className="public-copy-status" role="status" aria-live="polite">{status}</p></div>;
}
