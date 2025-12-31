/**
 * /founder/templates/[templateId]/page.jsx
 * =========================================
 * 
 * Example page for rendering a single template.
 * This demonstrates the complete integration:
 * - Load template schema from backend
 * - Render TemplateCanvas component
 * - Handle save and export
 * - Integrate AI mentor chat
 * 
 * URL: /founder/templates/persona_01
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import TemplateCanvas from '@/components/TemplateCanvas';
import AIMentorChat from '@/components/AIMentorChat';
import { apiCall } from '@/lib/api';

/**
 * Template Page Component
 */
export default function TemplatePage() {
  const params = useParams();
  const templateId = params?.templateId?.toString() || '';

  // State
  const [schema, setSchema] = useState(null);
  const [backgroundImage, setBackgroundImage] = useState(null);
  const [savedData, setSavedData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentData, setCurrentData] = useState({});
  const [showAIMentor, setShowAIMentor] = useState(false);
  const [aiMentorContext, setAiMentorContext] = useState(null);
  const [exportLoading, setExportLoading] = useState(false);

  // Load template on mount
  useEffect(() => {
    loadTemplate();
  }, [templateId]);

  // Load template schema and saved data
  const loadTemplate = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch template schema + saved data
      const response = await apiCall(`/founder/templates/${templateId}`, {
        method: 'GET',
      });

      if (!response.ok) {
        throw new Error(`Failed to load template: ${response.statusText}`);
      }

      const templateData = await response.json();

      setSchema(templateData.schema);
      setSavedData(templateData.saved_data);

      // Load background image
      // In production, this would be a pre-generated screenshot of the Excel sheet
      // For demo purposes, we generate a placeholder
      generatePlaceholderImage(templateData.schema);

      // Initialize current data
      if (templateData.saved_data?.data) {
        setCurrentData(templateData.saved_data.data);
      }
    } catch (err) {
      console.error('Error loading template:', err);
      setError(err.message || 'Failed to load template');
    } finally {
      setLoading(false);
    }
  };

  // Generate placeholder image (in production, use actual Excel screenshot)
  const generatePlaceholderImage = (schema) => {
    // Create a canvas to draw a placeholder Excel-like grid
    const canvas = document.createElement('canvas');
    const { sheet_width, sheet_height } = schema;

    // Scale canvas for better quality
    const scale = window.devicePixelRatio || 1;
    canvas.width = sheet_width * scale;
    canvas.height = sheet_height * scale;

    const ctx = canvas.getContext('2d');
    ctx.scale(scale, scale);

    // Background
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, sheet_width, sheet_height);

    // Header
    ctx.fillStyle = '#0066cc';
    ctx.fillRect(0, 0, sheet_width, 40);
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 18px Arial';
    ctx.fillText(schema.title || schema.sheet_name, 20, 28);

    // Grid lines (simulating Excel cells)
    ctx.strokeStyle = '#d0d0d0';
    ctx.lineWidth = 1;

    const cellWidth = 150;
    const cellHeight = 30;
    const startY = 50;

    for (let x = 0; x < sheet_width; x += cellWidth) {
      ctx.beginPath();
      ctx.moveTo(x, startY);
      ctx.lineTo(x, sheet_height);
      ctx.stroke();
    }

    for (let y = startY; y < sheet_height; y += cellHeight) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(sheet_width, y);
      ctx.stroke();
    }

    // Field labels
    ctx.fillStyle = '#333333';
    ctx.font = '12px Arial';
    schema.fields.slice(0, 10).forEach((field, idx) => {
      const y = startY + idx * cellHeight + 20;
      ctx.fillText(field.label, 10, y);
    });

    // Convert to image
    const imageUrl = canvas.toDataURL('image/png');
    setBackgroundImage(imageUrl);
  };

  // Handle form data change
  const handleDataChange = useCallback((data) => {
    setCurrentData(data);
  }, []);

  // Handle save
  const handleSave = useCallback(async (data) => {
    try {
      const response = await apiCall(`/founder/templates/${templateId}`, {
        method: 'POST',
        body: JSON.stringify({ data }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          errorData.detail?.message || `Save failed: ${response.statusText}`
        );
      }

      const savedResponse = await response.json();
      setSavedData(savedResponse);

      // Show success feedback
      return true;
    } catch (err) {
      console.error('Save error:', err);
      throw err;
    }
  }, [templateId]);

  // Handle export
  const handleExport = async () => {
    try {
      setExportLoading(true);

      const response = await apiCall(`/founder/templates/${templateId}/export`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error('Export failed');
      }

      const exportData = await response.json();

      // Download file
      const downloadUrl = exportData.file_url;
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = `${templateId}_filled.xlsx`;
      link.click();
    } catch (err) {
      console.error('Export error:', err);
      alert(`Export failed: ${err.message}`);
    } finally {
      setExportLoading(false);
    }
  };

  // Handle AI mentor click
  const handleAIMentorClick = async (fieldKey, field) => {
    try {
      const response = await apiCall(
        `/founder/templates/${templateId}/ai-mentor?current_field=${fieldKey}`,
        { method: 'POST' }
      );

      if (!response.ok) {
        throw new Error('Failed to load AI mentor context');
      }

      const mentorContext = await response.json();
      setAiMentorContext({
        ...mentorContext,
        field,
      });
      setShowAIMentor(true);
    } catch (err) {
      console.error('AI mentor error:', err);
    }
  };

  // Render
  if (loading) {
    return (
      <div className="template-page loading">
        <div className="spinner" />
        <p>Loading template...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="template-page error">
        <div className="error-card">
          <h2>Error Loading Template</h2>
          <p>{error}</p>
          <button onClick={loadTemplate} className="btn btn-primary">
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!schema) {
    return (
      <div className="template-page error">
        <div className="error-card">
          <h2>Template Not Found</h2>
          <p>The requested template could not be loaded.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="template-page">
      <div className="template-container">
        {/* Main Content */}
        <div className="template-main">
          <TemplateCanvas
            schema={schema}
            backgroundImage={backgroundImage}
            savedData={savedData}
            onDataChange={handleDataChange}
            onSave={handleSave}
            onAIMentorClick={handleAIMentorClick}
          />

          {/* Action Buttons */}
          <div className="template-actions">
            <button onClick={handleExport} disabled={exportLoading} className="btn btn-secondary">
              {exportLoading ? 'Exporting...' : '📊 Export to Excel'}
            </button>
            <button
              onClick={() => setShowAIMentor(!showAIMentor)}
              className="btn btn-secondary"
            >
              ✨ AI Mentor
            </button>
          </div>
        </div>

        {/* AI Mentor Sidebar */}
        {showAIMentor && aiMentorContext && (
          <div className="template-sidebar">
            <AIMentorChat
              templateContext={aiMentorContext}
              onClose={() => setShowAIMentor(false)}
            />
          </div>
        )}
      </div>

      <style jsx>{`
        .template-page {
          min-height: 100vh;
          background: #f5f5f5;
          padding: 20px;
        }

        .template-page.loading {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 16px;
        }

        .spinner {
          width: 40px;
          height: 40px;
          border: 4px solid #e0e0e0;
          border-top-color: #0066cc;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          to {
            transform: rotate(360deg);
          }
        }

        .template-page.error {
          display: flex;
          align-items: center;
          justify-content: center;
          min-height: 400px;
        }

        .error-card {
          background: white;
          padding: 40px;
          border-radius: 8px;
          text-align: center;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
          max-width: 500px;
        }

        .error-card h2 {
          color: #d32f2f;
          margin-top: 0;
        }

        .error-card p {
          color: #666;
          margin: 12px 0;
        }

        .template-container {
          display: grid;
          grid-template-columns: 1fr 350px;
          gap: 20px;
          max-width: 1600px;
          margin: 0 auto;
        }

        @media (max-width: 1200px) {
          .template-container {
            grid-template-columns: 1fr;
          }

          .template-sidebar {
            order: 2;
          }
        }

        .template-main {
          display: flex;
          flex-direction: column;
          gap: 20px;
        }

        .template-actions {
          display: flex;
          gap: 12px;
          justify-content: center;
          padding: 20px;
          background: white;
          border-radius: 8px;
          border: 1px solid #ddd;
        }

        .btn {
          padding: 10px 20px;
          border: none;
          border-radius: 6px;
          font-size: 14px;
          cursor: pointer;
          font-weight: 500;
          transition: all 0.2s ease;
        }

        .btn-primary {
          background: #0066cc;
          color: white;
        }

        .btn-primary:hover:not(:disabled) {
          background: #0052a3;
        }

        .btn-secondary {
          background: #f0f0f0;
          color: #333;
          border: 1px solid #ddd;
        }

        .btn-secondary:hover:not(:disabled) {
          background: #e0e0e0;
        }

        .btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .template-sidebar {
          background: white;
          border-radius: 8px;
          border: 1px solid #ddd;
          overflow: hidden;
          display: flex;
          flex-direction: column;
          height: fit-content;
          position: sticky;
          top: 20px;
        }
      `}</style>
    </div>
  );
}
