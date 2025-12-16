// components/auth/AuthLayout.tsx
import { ReactNode } from 'react';
import Link from 'next/link';

interface Props {
  title: string;
  children: ReactNode;
  footerText: string;
  footerLink: string;
  footerHref: string;
}

export default function AuthLayout({ title, children, footerText, footerLink, footerHref }: Props) {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm p-8">
        <h1 className="text-3xl font-bold text-slate-800 mb-6 text-center">
          {title}
        </h1>
        {children}
        <p className="mt-6 text-center text-sm text-slate-500">
          {footerText}
          {/* Color principal: text-indigo-600 */}
          <Link href={footerHref} className="text-indigo-600 hover:text-indigo-700 font-semibold ml-1">
            {footerLink}
          </Link>
        </p>
      </div>
    </div>
  );
}