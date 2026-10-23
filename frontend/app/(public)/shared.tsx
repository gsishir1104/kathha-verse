import type {Metadata} from 'next';
import type {ReactNode} from 'react';
import {ArrowRight} from 'lucide-react';

export const origin = 'https://www.kathhaverse.org';
export function publicMetadata(title: string, description: string, path: string, keywords: string[], article = false): Metadata {
  return {title, description, keywords, alternates: {canonical: origin + path}, robots: {index: true, follow: true},
    openGraph: {title: `${title} | KathhaVerse`, description, url: origin + path, siteName: 'KathhaVerse', type: article ? 'article' : 'website', locale: 'en_US'},
    twitter: {card: 'summary', title: `${title} | KathhaVerse`, description}};
}
export function ActionLink({role, children}: {role: 'writer' | 'beta'; children: ReactNode}) {
  return <a className="public-button" href={`/?join=${role}`}>{children}<ArrowRight size={18} aria-hidden="true"/></a>;
}
export function ClosingNote({role, title, children}: {role: 'writer' | 'beta'; title: string; children: ReactNode}) {
  return <section className="public-closing"><div><p className="public-kicker">YOUR NEXT CHAPTER</p><h2>{title}</h2><p>{children}</p></div><ActionLink role={role}>{role === 'writer' ? 'Start writing' : 'Become a beta reader'}</ActionLink></section>;
}
export const guides = [
  {href: '/guides/how-to-find-beta-readers', title: 'How to find beta readers for your novel', description: 'Choose the right readers, make a clear invitation, and start with a manageable first chapter.', label: 'BUILD YOUR READING CIRCLE'},
  {href: '/guides/questions-to-ask-beta-readers', title: 'Questions to ask your beta readers', description: 'Ask about attention, characters, clarity, and expectations without steering the answers.', label: 'GET USEFUL FEEDBACK'},
];
export function GuideCards() {
  return <div className="public-guide-grid">{guides.map(guide => <a className="public-guide-card" key={guide.href} href={guide.href}><span className="public-kicker">{guide.label}</span><h3>{guide.title}</h3><p>{guide.description}</p><span className="public-text-link">Read the guide <ArrowRight size={17} aria-hidden="true"/></span></a>)}</div>;
}
export function GuideArticle({title, description, path, sections, children}: {title: string; description: string; path: string; sections: {id: string; title: string}[]; children: ReactNode}) {
  const structuredData = {'@context': 'https://schema.org', '@graph': [
    {'@type': 'Article', headline: title, description, mainEntityOfPage: origin + path, author: {'@type': 'Organization', name: 'KathhaVerse', url: origin}, publisher: {'@type': 'Organization', name: 'KathhaVerse', url: origin}, inLanguage: 'en'},
    {'@type': 'BreadcrumbList', itemListElement: [
      {'@type': 'ListItem', position: 1, name: 'Home', item: origin + '/'},
      {'@type': 'ListItem', position: 2, name: 'Writing guides', item: origin + '/guides'},
      {'@type': 'ListItem', position: 3, name: title, item: origin + path},
    ]},
  ]};
  return <>
    <script type="application/ld+json" dangerouslySetInnerHTML={{__html: JSON.stringify(structuredData).replace(/</g, '\\u003c')}}/>
    <div className="public-breadcrumb"><a href="/">Home</a><span>/</span><a href="/guides">Writing guides</a></div>
    <header className="public-article-heading"><p className="public-kicker">THE KATHHAVERSE WRITING DESK</p><h1>{title}</h1><p className="public-intro">{description}</p><p className="public-byline">A practical guide from KathhaVerse</p></header>
    <div className="public-article-layout"><aside className="public-toc"><nav aria-label="On this page"><p className="public-kicker">IN THIS GUIDE</p>{sections.map(section => <a href={`#${section.id}`} key={section.id}>{section.title}</a>)}</nav></aside><article className="public-prose">{children}</article></div>
  </>;
}
