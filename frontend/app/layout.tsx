import './globals.css';
import type { Metadata } from 'next';
export const metadata: Metadata = { title: 'Kathha Verse — Your story, through their eyes', description: 'Write, verify your story universe, and understand real beta readers.', icons: {icon:'/favicon.svg'} };
export default function RootLayout({children}: Readonly<{children: React.ReactNode}>) {return <html lang="en"><body>{children}</body></html>}
