'use client';
import { useState, useEffect } from 'react';
import { UploadForm } from '@/components/UploadForm';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { FolderOpen, FileText, Trash2, RefreshCw, Loader2, AlertCircle } from 'lucide-react';
import { getDocuments, deleteDocument, reindexKnowledge, ApiError } from '@/lib/api';
import { Document } from '@/lib/types';
import { Alert, AlertDescription } from '@/components/ui/alert';

export default function KnowledgePage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isReindexing, setIsReindexing] = useState(false);
  const [error, setError] = useState('');

  const loadDocuments = async () => {
    try {
      setIsLoading(true);
      const docs = await getDocuments();
      setDocuments(docs);
      setError('');
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Erro ao carregar documentos');
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDocuments();
  }, []);

  const handleDelete = async (id: string) => {
    if (!confirm('Tem certeza que deseja remover este documento?')) return;
    try {
      await deleteDocument(id);
      await loadDocuments();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      }
    }
  };

  const handleReindex = async () => {
    try {
      setIsReindexing(true);
      await reindexKnowledge();
      await loadDocuments();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      }
    } finally {
      setIsReindexing(false);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <header className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <FolderOpen className="w-8 h-8 text-primary" />
          <h1 className="text-2xl font-bold">Knowledge Base</h1>
        </div>
        <p className="text-muted-foreground">Gerencie os documentos da base de conhecimento do TR4CTION Agent</p>
      </header>

      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="grid lg:grid-cols-2 gap-6">
        <UploadForm onSuccess={loadDocuments} />

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <FileText className="w-5 h-5" />
                Documentos ({documents.length})
              </CardTitle>
              <Button variant="outline" size="sm" onClick={handleReindex} disabled={isReindexing}>
                {isReindexing ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
                <span className="ml-2">Reindexar</span>
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[400px]">
              {isLoading ? (
                <div className="flex items-center justify-center h-32">
                  <Loader2 className="w-6 h-6 animate-spin" />
                </div>
              ) : documents.length === 0 ? (
                <div className="text-center text-muted-foreground py-8">Nenhum documento encontrado</div>
              ) : (
                <div className="space-y-3">
                  {documents.map((doc) => (
                    <div key={doc.id} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex-1 min-w-0">
                        <p className="font-medium truncate">{doc.filename}</p>
                        <div className="flex gap-2 mt-1">
                          <Badge variant="secondary">{doc.trail_id}</Badge>
                          <Badge variant="outline">{doc.step_id}</Badge>
                          <Badge variant="outline">v{doc.version}</Badge>
                        </div>
                      </div>
                      <Button variant="ghost" size="icon" onClick={() => handleDelete(doc.id)}>
                        <Trash2 className="w-4 h-4 text-destructive" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
