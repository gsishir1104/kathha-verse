import type {ReactNode} from 'react';
import {BookOpen, ArrowUpRight} from 'lucide-react';
import './public-pages.css';

export default function PublicLayout({children}: {children: ReactNode}) {
  return <div className="kv-public">
    <a className="public-skip" href="#public-content">Skip to content</a>
    <header className="public-header">
      <a className="public-brand" href="/" aria-label="KathhaVerse home"><BookOpen size={25} aria-hidden="true"/>KathhaVerse</a>
      <nav aria-label="Main navigation"><a href="/for-writers">For writers</a><a href="/for-beta-readers">For beta readers</a><a href="/guides">Guides</a><a className="public-signin" href="/?signin=1">Sign in <ArrowUpRight size={15} aria-hidden="true"/></a></nav>
    </header>
    <main id="public-content">{children}</main>
    <footer className="public-footer">
      <div><a className="public-brand" href="/">KathhaVerse</a><p>Every chapter. A new perspective.</p></div>
      <nav aria-label="Footer navigation"><a href="/for-writers">For writers</a><a href="/for-beta-readers">For beta readers</a><a href="/guides">Writing guides</a><a href="/#privacy">Manuscript privacy</a></nav>
    </footer>
  </div>;
}
