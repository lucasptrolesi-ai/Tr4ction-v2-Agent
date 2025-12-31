/**
 * TemplateCanvas Component
 * =======================
 * 
 * Renders an Excel-based template as an image background with absolute-positioned
 * input overlays. All positioning comes from the backend JSON schema.
 * 
 * Features:
 * - Renders background image (Excel screenshot)
 * - Positions inputs based on JSON schema
 * - Synchronizes values with parent component
 * - Responsive zoom/scale
 * - Validation feedback
 * - Auto-save to backend
 * 
 * Props:
 *   - schema: TemplateSchema from backend
 *   - backgroundImage: URL or base64 of Excel sheet image
 *   - savedData: Previous response (optional)
 *   - onDataChange: Callback when form changes
 *   - onSave: Callback when user clicks save
 *   - onAIMentorClick: Callback to open AI mentor for a field
 * 
 * Usage:
 *   <TemplateCanvas
 *     schema={templateSchema}
 *     backgroundImage="/images/persona_01.png"
 *     savedData={previousResponse}
 *     onDataChange={handleChange}
 *     onSave={handleSave}
 *   />
 */

'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import Image from 'next/image';

/**
 * TemplateCanvas - Main component
 */
export default function TemplateCanvas({
  schema,
  backgroundImage,
  savedData,
  onDataChange,
  onSave,
  onAIMentorClick,
  zoomLevel = 1.0,
}) {
  // State management
  const [formData, setFormData] = useState({});
  const [errors, setErrors] = useState({});
  const [touchedFields, setTouchedFields] = useState(new Set());
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [focusedField, setFocusedField] = useState(null);
  const [scale, setScale] = useState(zoomLevel);
  const containerRef = useRef(null);

  // Initialize form with saved data
  useEffect(() => {
    if (savedData?.data) {
      setFormData(savedData.data);
    }
  }, [savedData]);

  // Validate single field
  const validateField = useCallback(
    (field, value) => {
      if (field.required && !value) {
        return `${field.label} is required`;
      }

      const rules = field.validation_rules || {};

      if (value && rules.min && value.toString().length < rules.min) {
        return `Minimum length is ${rules.min}`;
      }

      if (value && rules.max && value.toString().length > rules.max) {
        return `Maximum length is ${rules.max}`;
      }

      if (value && rules.pattern) {
        const regex = new RegExp(rules.pattern);
        if (!regex.test(value.toString())) {
          return `Invalid format`;
        }
      }

      if (value && rules.enum && !rules.enum.includes(value)) {
        return `Must be one of: ${rules.enum.join(', ')}`;
      }

      return undefined;
    },
    []
  );

  // Handle field change
  const handleFieldChange = useCallback(
    (fieldKey, field, value) => {
      // Update form data
      const newData = { ...formData, [fieldKey]: value };
      setFormData(newData);

      // Validate
      const error = validateField(field, value);
      setErrors((prev) => {
        if (error) {
          return { ...prev, [fieldKey]: error };
        } else {
          const { [fieldKey]: _, ...rest } = prev;
          return rest;
        }
      });

      // Mark as touched
      setTouchedFields((prev) => new Set([...prev, fieldKey]));

      // Notify parent
      if (onDataChange) {
        onDataChange(newData);
      }
    },
    [formData, validateField, onDataChange]
  );

  // Handle field blur
  const handleFieldBlur = useCallback((fieldKey) => {
    setTouchedFields((prev) => new Set([...prev, fieldKey]));
  }, []);

  // Handle save
  const handleSave = useCallback(async () => {
    if (!onSave) return;

    setIsSaving(true);
    setSaveSuccess(false);

    try {
      await onSave(formData);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (error) {
      console.error('Save error:', error);
    } finally {
      setIsSaving(false);
    }
  }, [formData, onSave]);

  // Get field by key
  const getField = (key) => {
    return schema.fields.find((f) => f.key === key);
  };

  // Calculate pixel scale (for responsive sizing)
  const containerWidth = containerRef.current?.offsetWidth || schema.sheet_width;
  const calculatedScale = (containerWidth / schema.sheet_width) * scale;

  // Group fields by section for UI organization
  const fieldsBySection = {};
  schema.fields.forEach((field) => {
    const section = field.section || 'General';
    if (!fieldsBySection[section]) {
      fieldsBySection[section] = [];
    }
    fieldsBySection[section].push(field);
  });

  return (
    <div className="template-canvas-wrapper">
      {/* Header */}
      <div className="template-header">
        <div>
          <h1>{schema.title || schema.sheet_name}</h1>
          {schema.description && <p className="description">{schema.description}</p>}
        </div>
        <div className="header-actions">
          <button
            onClick={handleSave}
            disabled={isSaving || Object.keys(errors).length > 0}
            className="btn btn-primary"
          >
            {isSaving ? 'Saving...' : 'Save Progress'}
          </button>
          {saveSuccess && <span className="save-success">✓ Saved</span>}
        </div>
      </div>

      {/* Main Canvas Container */}
      <div
        ref={containerRef}
        className="template-canvas"
        style={{
          width: '100%',
          maxWidth: '1200px',
          position: 'relative',
          margin: '0 auto',
          aspectRatio: `${schema.sheet_width} / ${schema.sheet_height}`,
        }}
      >
        {/* Background Image */}
        <div
          className="canvas-background"
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            backgroundImage: `url(${backgroundImage})`,
            backgroundSize: 'contain',
            backgroundRepeat: 'no-repeat',
            backgroundPosition: 'top left',
            zIndex: 0,
          }}
        />

        {/* Input Overlays */}
        <div className="canvas-inputs" style={{ position: 'absolute', width: '100%', height: '100%', zIndex: 1 }}>
          {schema.fields.map((field) => (
            <TemplateFieldInput
              key={field.key}
              field={field}
              value={formData[field.key] ?? ''}
              error={errors[field.key]}
              isTouched={touchedFields.has(field.key)}
              isFocused={focusedField === field.key}
              scale={calculatedScale}
              schemaWidth={schema.sheet_width}
              schemaHeight={schema.sheet_height}
              containerWidth={containerWidth}
              onChange={(value) => handleFieldChange(field.key, field, value)}
              onBlur={() => handleFieldBlur(field.key)}
              onFocus={() => setFocusedField(field.key)}
              onAIMentorClick={
                onAIMentorClick ? () => onAIMentorClick(field.key, field) : undefined
              }
            />
          ))}
        </div>
      </div>

      {/* Summary Section */}
      {Object.keys(fieldsBySection).length > 0 && (
        <div className="template-summary">
          <h2>Form Summary</h2>
          {Object.entries(fieldsBySection).map(([section, fields]) => (
            <div key={section} className="summary-section">
              <h3>{section}</h3>
              <div className="section-grid">
                {fields.map((field) => (
                  <div key={field.key} className="summary-item">
                    <label>{field.label}</label>
                    <p className={formData[field.key] ? 'filled' : 'empty'}>
                      {formData[field.key] || '(not filled)'}
                    </p>
                    {errors[field.key] && (
                      <span className="error-badge">{errors[field.key]}</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Styles */}
      <style jsx>{`
        .template-canvas-wrapper {
          padding: 20px;
          background: #f5f5f5;
          border-radius: 8px;
        }

        .template-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
          padding-bottom: 20px;
          border-bottom: 2px solid #e0e0e0;
        }

        .template-header h1 {
          margin: 0;
          font-size: 24px;
          font-weight: 600;
          color: #333;
        }

        .template-header .description {
          margin: 8px 0 0 0;
          font-size: 14px;
          color: #666;
        }

        .header-actions {
          display: flex;
          gap: 12px;
          align-items: center;
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

        .btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .save-success {
          color: #4caf50;
          font-size: 14px;
          font-weight: 500;
        }

        .template-canvas {
          background: white;
          border: 1px solid #ddd;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
          border-radius: 8px;
          overflow: hidden;
        }

        .canvas-background {
          filter: brightness(1.1);
        }

        .template-summary {
          margin-top: 30px;
          padding: 20px;
          background: white;
          border-radius: 8px;
          border: 1px solid #ddd;
        }

        .template-summary h2 {
          margin-top: 0;
          font-size: 18px;
          color: #333;
        }

        .summary-section {
          margin-top: 20px;
        }

        .summary-section h3 {
          font-size: 14px;
          color: #666;
          margin: 0 0 12px 0;
          text-transform: uppercase;
          font-weight: 600;
        }

        .section-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 16px;
        }

        .summary-item {
          padding: 12px;
          background: #f9f9f9;
          border-radius: 6px;
          border: 1px solid #eee;
        }

        .summary-item label {
          display: block;
          font-size: 12px;
          font-weight: 600;
          color: #666;
          margin-bottom: 6px;
        }

        .summary-item p {
          margin: 0;
          font-size: 14px;
          color: #333;
          word-break: break-word;
        }

        .summary-item p.empty {
          color: #999;
          font-style: italic;
        }

        .error-badge {
          display: inline-block;
          margin-top: 6px;
          font-size: 11px;
          color: #d32f2f;
          background: #ffebee;
          padding: 4px 8px;
          border-radius: 4px;
        }
      `}</style>
    </div>
  );
}

/**
 * TemplateFieldInput - Individual field renderer
 * Positions input absolutely using pixel values from schema
 */
function TemplateFieldInput({
  field,
  value,
  error,
  isTouched,
  isFocused,
  scale,
  schemaWidth,
  containerWidth,
  onChange,
  onBlur,
  onFocus,
  onAIMentorClick,
}) {
  const pixelToPercent = (px) => (px / schemaWidth) * 100;

  const position = field.position;
  const top = pixelToPercent(position.top);
  const left = pixelToPercent(position.left);
  const width = pixelToPercent(position.width);
  const height = pixelToPercent(position.height);

  const isTextarea = field.type === 'textarea';
  const isSelect = field.type === 'enum' || field.type === 'boolean';

  return (
    <div
      className={`template-field ${isFocused ? 'focused' : ''} ${error && isTouched ? 'error' : ''}`}
      style={{
        position: 'absolute',
        top: `${top}%`,
        left: `${left}%`,
        width: `${width}%`,
        height: `${height}%`,
      }}
      title={field.help_text}
    >
      {isSelect ? (
        <select
          value={value || ''}
          onChange={(e) => onChange(e.target.value)}
          onBlur={onBlur}
          onFocus={onFocus}
          className="field-input"
          aria-label={field.label}
        >
          <option value="">{field.placeholder || `Select ${field.label}`}</option>
          {field.validation_rules?.enum?.map((opt) => (
            <option key={opt} value={opt}>
              {opt}
            </option>
          ))}
        </select>
      ) : isTextarea ? (
        <textarea
          value={value || ''}
          onChange={(e) => onChange(e.target.value)}
          onBlur={onBlur}
          onFocus={onFocus}
          placeholder={field.placeholder}
          className="field-input field-textarea"
          aria-label={field.label}
        />
      ) : (
        <input
          type={getInputType(field.type)}
          value={value || ''}
          onChange={(e) => onChange(e.target.value)}
          onBlur={onBlur}
          onFocus={onFocus}
          placeholder={field.placeholder}
          className="field-input"
          aria-label={field.label}
          required={field.required}
        />
      )}

      {error && isTouched && <div className="field-error-tooltip">{error}</div>}

      {onAIMentorClick && (
        <button
          className="ai-mentor-btn"
          onClick={onAIMentorClick}
          title="Ask AI mentor about this field"
          aria-label={`Ask about ${field.label}`}
        >
          ✨
        </button>
      )}

      <style jsx>{`
        .template-field {
          padding: 4px;
          border-radius: 4px;
          transition: all 0.2s ease;
          z-index: 2;
        }

        .template-field.focused {
          background: rgba(0, 102, 204, 0.1);
          border: 2px solid #0066cc;
        }

        .template-field.error {
          border: 2px solid #d32f2f;
          background: rgba(211, 47, 47, 0.05);
        }

        .field-input {
          width: 100%;
          height: 100%;
          padding: 4px 6px;
          border: 1px solid #ccc;
          border-radius: 3px;
          font-size: 12px;
          font-family: inherit;
          background: rgba(255, 255, 255, 0.95);
          color: #333;
          outline: none;
          transition: border-color 0.2s ease;
          box-sizing: border-box;
          resize: none;
        }

        .field-input:focus {
          border-color: #0066cc;
          box-shadow: 0 0 0 2px rgba(0, 102, 204, 0.2);
        }

        .field-textarea {
          font-size: 11px;
          line-height: 1.3;
        }

        .field-error-tooltip {
          position: absolute;
          bottom: -20px;
          left: 0;
          background: #d32f2f;
          color: white;
          font-size: 11px;
          padding: 4px 8px;
          border-radius: 3px;
          white-space: nowrap;
          z-index: 10;
          pointer-events: none;
        }

        .ai-mentor-btn {
          position: absolute;
          top: 2px;
          right: 2px;
          width: 20px;
          height: 20px;
          padding: 0;
          background: rgba(255, 193, 7, 0.9);
          border: 1px solid #fbc02d;
          border-radius: 50%;
          cursor: pointer;
          font-size: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.2s ease;
          z-index: 5;
        }

        .ai-mentor-btn:hover {
          background: #fbc02d;
          transform: scale(1.1);
        }
      `}</style>
    </div>
  );
}

/**
 * Helper: Map field type to HTML input type
 */
function getInputType(fieldType) {
  const typeMap = {
    text: 'text',
    email: 'email',
    phone: 'tel',
    url: 'url',
    number: 'number',
    decimal: 'number',
    currency: 'number',
    percentage: 'number',
    date: 'date',
    boolean: 'checkbox',
  };
  return typeMap[fieldType] || 'text';
}
