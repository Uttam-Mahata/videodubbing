import { ReactNode } from 'react';
import { Navigation } from './Navigation';

interface LayoutProps {
  children: ReactNode;
  showNav?: boolean;
}

export function Layout({ children, showNav = true }: LayoutProps) {
  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      {showNav && <Navigation />}
      <main className="flex-1">{children}</main>
      <footer className="bg-white border-t border-gray-200 mt-auto">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="text-center text-gray-600 text-sm">
            <p>
              Video Dubbing Platform - Powered by Google Gemini AI & ADK
            </p>
            <p className="mt-1 text-gray-500">
              &copy; {new Date().getFullYear()} All rights reserved
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
