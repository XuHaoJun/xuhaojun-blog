import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { DarkModeToggle } from '@/components/dark-mode-toggle';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Blog Agent - AI Conversation to Blog',
  description: 'Transform AI conversations into structured blog posts',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-TW" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                const theme = localStorage.getItem('theme') || 
                  (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
                if (theme === 'dark') {
                  document.documentElement.classList.add('dark');
                }
              })();
            `,
          }}
        />
      </head>
      <body className={inter.className}>
        <div className="fixed top-4 right-4 z-50">
          <DarkModeToggle />
        </div>
        {children}
      </body>
    </html>
  );
}

