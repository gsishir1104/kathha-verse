import './globals.css';
import type { Metadata } from 'next';

const siteTitle = 'KathhaVerse | Novel Writing & Beta Reader Feedback';
const siteDescription = 'Write your novel, organize your story universe, and get chapter-by-chapter feedback from beta readers. Build stronger stories with KathhaVerse.';
const siteUrl = 'https://www.kathhaverse.org/';

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {default: siteTitle, template: '%s | KathhaVerse'},
  description: siteDescription,
  applicationName: 'KathhaVerse',
  keywords: ['novel writing', 'beta readers', 'manuscript feedback', 'writing platform', 'story planning', 'reader feedback'],
  alternates: {canonical: siteUrl},
  robots: {index: true, follow: true},
  openGraph: {type: 'website', locale: 'en_US', url: siteUrl, siteName: 'KathhaVerse', title: siteTitle, description: siteDescription},
  twitter: {card: 'summary', title: siteTitle, description: siteDescription},
  icons: {icon: '/favicon.svg'},
};

const websiteSchema = {
  '@context': 'https://schema.org',
  '@type': 'WebSite',
  name: 'KathhaVerse',
  alternateName: 'Kathha Verse',
  url: siteUrl,
  description: siteDescription,
  inLanguage: 'en',
};

export default function RootLayout({children}: Readonly<{children: React.ReactNode}>) {
  return <html lang="en"><body><script type="application/ld+json" dangerouslySetInnerHTML={{__html: JSON.stringify(websiteSchema).replace(/</g, '\\u003c')}}/>{children}</body></html>;
}
