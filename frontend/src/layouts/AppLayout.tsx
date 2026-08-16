import React from 'react';
import { Outlet } from 'react-router-dom';
import { Navbar } from '../components/layout/Navbar';
import { Footer } from '../components/layout/Footer';

export const AppLayout: React.FC = () => {
  return (
    <div className="flex min-h-screen flex-col bg-[#f0f2f8] text-[#181534] selection:bg-[#5b5dfa]/20 selection:text-[#5b5dfa]">
      <Navbar />
      <main className="flex-1">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
          <Outlet />
        </div>
      </main>
      <Footer />
    </div>
  );
};
