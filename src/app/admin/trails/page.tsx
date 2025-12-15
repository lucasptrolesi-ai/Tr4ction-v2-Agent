'use client';
import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { BookOpen, Loader2 } from 'lucide-react';
import { getAdminTrails } from '@/lib/api';
import { Trail } from '@/lib/types';

export default function TrailsPage() {
  const [trails, setTrails] = useState<Trail[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadTrails = async () => {
      try {
        const data = await getAdminTrails();
        setTrails(data);
      } catch (err) {
        console.error('Erro ao carregar trilhas:', err);
      } finally {
        setIsLoading(false);
      }
    };
    loadTrails();
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <header className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <BookOpen className="w-8 h-8 text-primary" />
          <h1 className="text-2xl font-bold">Trilhas</h1>
        </div>
        <p className="text-muted-foreground">Visualize as trilhas de aceleração</p>
      </header>

      <div className="grid md:grid-cols-2 gap-4">
        {trails.length === 0 ? (
          <p className="text-muted-foreground">Nenhuma trilha encontrada</p>
        ) : (
          trails.map((trail) => (
            <Card key={trail.id}>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Badge>{trail.id}</Badge>
                  {trail.name}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground text-sm">{trail.description}</p>
                {trail.steps && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {trail.steps.map((step) => (
                      <Badge key={step.id} variant="outline">{step.name}</Badge>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
