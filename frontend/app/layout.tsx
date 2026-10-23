import './globals.css';
import type { Metadata } from 'next';
export const metadata: Metadata = { metadataBase: new URL('https://www.kathhaverse.org'), alternates: {canonical: '/'}, title: 'KathhaVerse — Every chapter. A new perspective.', description: 'Write, verify your story universe, and understand real beta readers.', icons: {icon:'/favicon.svg'} };
export default function RootLayout({children}: Readonly<{children: React.ReactNode}>) {return <html lang="en"><body>{children}</body></html>}
