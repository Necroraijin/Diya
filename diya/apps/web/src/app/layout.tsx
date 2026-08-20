import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'DIYA - Infrastructure Conflict Resolution',
  description: 'Multi-Agent Infrastructure Conflict Resolution System for Municipal Coordination',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-diya-bg">
        {children}
      </body>
    </html>
  );
}
