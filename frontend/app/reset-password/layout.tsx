import type {Metadata} from 'next';

export const metadata: Metadata = {
  title: 'Reset your password',
  description: 'Reset your KathhaVerse account password and return to your writing or beta reading workspace.',
  keywords: [],
  alternates: {canonical: 'https://www.kathhaverse.org/reset-password.html'},
  robots: {index: false, follow: true},
  openGraph: {title: 'Reset your password | KathhaVerse', description: 'Reset your KathhaVerse account password.', url: 'https://www.kathhaverse.org/reset-password.html'},
  twitter: {card: 'summary', title: 'Reset your password | KathhaVerse', description: 'Reset your KathhaVerse account password.'},
};

export default function ResetPasswordLayout({children}: Readonly<{children: React.ReactNode}>) {
  return children;
}
