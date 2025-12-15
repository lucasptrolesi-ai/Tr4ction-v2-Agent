'use client';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { Sidebar } from '@/components/Sidebar';

export default function FounderLayout({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedRoute allowedRoles={['founder', 'admin']}>
      <div className="flex min-h-screen bg-background">
        <Sidebar />
        <main className="flex-1">{children}</main>
      </div>
    </ProtectedRoute>
  );
}
