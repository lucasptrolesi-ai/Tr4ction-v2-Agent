'use client';

// =====================================================
//   UPLOAD FORM - TR4CTION FRONTEND
// =====================================================

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Upload, FileText, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { uploadDocument, ApiError } from '@/lib/api';

interface UploadFormProps {
  onSuccess?: () => void;
}

const TRAILS = [
  { id: 'Q1_Marketing', name: 'Q1 - Marketing' },
  { id: 'Q2_Sales', name: 'Q2 - Vendas' },
  { id: 'Q3_Product', name: 'Q3 - Produto' },
  { id: 'Q4_Finance', name: 'Q4 - Finanças' },
];

const STEPS = [
  { id: 'ICP', name: 'ICP - Perfil do Cliente Ideal' },
  { id: 'Persona', name: 'Persona' },
  { id: 'SWOT', name: 'Análise SWOT' },
  { id: 'GTM', name: 'Go-to-Market' },
  { id: 'Pitch', name: 'Pitch Deck' },
];

export function UploadForm({ onSuccess }: UploadFormProps) {
  const [file, setFile] = useState<File | null>(null);
  const [trailId, setTrailId] = useState('');
  const [stepId, setStepId] = useState('');
  const [version, setVersion] = useState('1.0');
  const [description, setDescription] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError('');
      setSuccess(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!file || !trailId || !stepId) {
      setError('Por favor, preencha todos os campos obrigatórios.');
      return;
    }

    setIsLoading(true);
    setError('');
    setSuccess(false);

    try {
      await uploadDocument(file, trailId, stepId, version, description);
      setSuccess(true);
      setFile(null);
      setDescription('');
      onSuccess?.();
      
      // Reset form
      const fileInput = document.getElementById('file-upload') as HTMLInputElement;
      if (fileInput) fileInput.value = '';
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Erro ao fazer upload do arquivo.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Upload className="w-5 h-5" />
          Upload de Documento
        </CardTitle>
        <CardDescription>
          Adicione documentos à base de conhecimento do TR4CTION Agent
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* File Upload */}
          <div className="space-y-2">
            <Label htmlFor="file-upload">Arquivo *</Label>
            <div className="flex items-center gap-4">
              <Input
                id="file-upload"
                type="file"
                accept=".pdf,.docx,.pptx,.txt,.md"
                onChange={handleFileChange}
                className="flex-1"
              />
            </div>
            {file && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <FileText className="w-4 h-4" />
                {file.name} ({(file.size / 1024).toFixed(1)} KB)
              </div>
            )}
            <p className="text-xs text-muted-foreground">
              Formatos aceitos: PDF, DOCX, PPTX, TXT, MD
            </p>
          </div>

          {/* Trail Selection */}
          <div className="space-y-2">
            <Label htmlFor="trail">Trilha *</Label>
            <select
              id="trail"
              value={trailId}
              onChange={(e) => setTrailId(e.target.value)}
              className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              <option value="">Selecione uma trilha</option>
              {TRAILS.map((trail) => (
                <option key={trail.id} value={trail.id}>
                  {trail.name}
                </option>
              ))}
            </select>
          </div>

          {/* Step Selection */}
          <div className="space-y-2">
            <Label htmlFor="step">Etapa *</Label>
            <select
              id="step"
              value={stepId}
              onChange={(e) => setStepId(e.target.value)}
              className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              <option value="">Selecione uma etapa</option>
              {STEPS.map((step) => (
                <option key={step.id} value={step.id}>
                  {step.name}
                </option>
              ))}
            </select>
          </div>

          {/* Version */}
          <div className="space-y-2">
            <Label htmlFor="version">Versão</Label>
            <Input
              id="version"
              value={version}
              onChange={(e) => setVersion(e.target.value)}
              placeholder="Ex: 1.0, 2.1"
            />
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="description">Descrição</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Descreva o conteúdo do documento..."
              rows={3}
            />
          </div>

          {/* Error Alert */}
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Success Alert */}
          {success && (
            <Alert className="border-green-500 bg-green-50 dark:bg-green-950">
              <CheckCircle className="h-4 w-4 text-green-600" />
              <AlertDescription className="text-green-600">
                Documento enviado com sucesso!
              </AlertDescription>
            </Alert>
          )}

          {/* Submit Button */}
          <Button type="submit" disabled={isLoading} className="w-full">
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Enviando...
              </>
            ) : (
              <>
                <Upload className="w-4 h-4 mr-2" />
                Fazer Upload
              </>
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
