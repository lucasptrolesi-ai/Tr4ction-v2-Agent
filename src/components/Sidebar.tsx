'use client';

// =====================================================
//   SIDEBAR - TR4CTION FRONTEND
// =====================================================

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import { cn } from '@/lib/utils';
import {
  MessageSquare,
  FolderOpen,
  LogOut,
  
  BookOpen,
  
  Bot,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Separator } from '@/components/ui/separator';

const founderLinks = [
  { href: '/founder/chat', label: 'Chat AI', icon: MessageSquare },
];

const adminLinks = [
  { href: '/admin/knowledge', label: 'Knowledge Base', icon: FolderOpen },
  { href: '/admin/trails', label: 'Trilhas', icon: BookOpen },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  const links = user?.role === 'admin' ? adminLinks : founderLinks;

  return (
    <aside className="w-64 bg-card border-r border-border flex flex-col h-screen sticky top-0">
      {/* Logo */}
      <div className="p-6">
        <Link href="/" className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
            <Bot className="w-6 h-6 text-primary-foreground" />
          </div>
          <div>
            <h1 className="font-bold text-lg text-foreground">TR4CTION</h1>
            <p className="text-xs text-muted-foreground">Agent V2</p>
          </div>
        </Link>
      </div>

      <Separator />

      {/* Navigation */}
      <nav className="flex-1 p-4">
        <div className="space-y-1">
          {links.map((link) => {
            const Icon = link.icon;
            const isActive = pathname === link.href;

            return (
              <Link key={link.href} href={link.href}>
                <Button
                  variant={isActive ? 'secondary' : 'ghost'}
                  className={cn(
                    'w-full justify-start gap-3',
                    isActive && 'bg-secondary'
                  )}
                >
                  <Icon className="w-5 h-5" />
                  {link.label}
                </Button>
              </Link>
            );
          })}
        </div>
      </nav>

      <Separator />

      {/* User Info */}
      <div className="p-4">
        <div className="flex items-center gap-3 mb-4">
          <Avatar>
            <AvatarFallback className="bg-primary text-primary-foreground">
              {user?.email?.[0]?.toUpperCase() || 'U'}
            </AvatarFallback>
          </Avatar>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{user?.email}</p>
            <p className="text-xs text-muted-foreground capitalize">
              {user?.role === 'admin' ? 'Administrador' : 'Founder'}
            </p>
          </div>
        </div>

        <Button
          variant="outline"
          className="w-full justify-start gap-3"
          onClick={logout}
        >
          <LogOut className="w-4 h-4" />
          Sair
        </Button>
      </div>
    </aside>
  );
}
