'use client';
import { ChatBox } from '@/components/ChatBox';
import { MessageSquare } from 'lucide-react';

export default function ChatPage() {
  return (
    <div className="flex flex-col h-screen">
      <header className="border-b px-6 py-4 flex items-center gap-3 bg-card">
        <MessageSquare className="w-6 h-6 text-primary" />
        <div>
          <h1 className="text-xl font-semibold">Chat com TR4CTION Agent</h1>
          <p className="text-sm text-muted-foreground">Tire suas dúvidas sobre estratégia de negócios</p>
        </div>
      </header>
      <ChatBox className="flex-1" />
    </div>
  );
}
