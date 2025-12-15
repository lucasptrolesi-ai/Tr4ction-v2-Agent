"use client";

import { useState } from "react";
import { HelpCircle, AlertCircle, CheckCircle } from "lucide-react";

/**
 * Componente de renderização dinâmica de campos baseado no schema
 * Suporta: text, email, tel, number, date, url, textarea, select
 */
export default function DynamicField({ 
  field, 
  value, 
  onChange, 
  onAskAI,
  showValidation = false,
  disabled = false 
}) {
  const [touched, setTouched] = useState(false);
  const [focused, setFocused] = useState(false);

  const {
    name,
    key,
    label,
    type = "text",
    placeholder = "",
    required = false,
    options = [],
    help,
    minLength,
    maxLength,
    min,
    max,
    pattern
  } = field;

  const fieldName = name || key;
  const isEmpty = !value || value.toString().trim() === "";
  const isValid = !required || !isEmpty;
  const showError = showValidation && touched && !isValid;
  const showSuccess = touched && !isEmpty && isValid;

  // Estilos dinâmicos baseados no estado
  const getBorderColor = () => {
    if (focused) return "var(--primary)";
    if (showError) return "#ef4444";
    if (showSuccess) return "#10b981";
    return "var(--border)";
  };

  const baseInputStyle = {
    width: "100%",
    padding: "12px 16px",
    border: `2px solid ${getBorderColor()}`,
    borderRadius: "8px",
    fontSize: "0.95rem",
    fontFamily: "inherit",
    transition: "border-color 0.2s, box-shadow 0.2s",
    outline: "none",
    boxShadow: focused ? `0 0 0 3px ${showError ? "rgba(239,68,68,0.1)" : "rgba(27,166,178,0.1)"}` : "none",
    background: disabled ? "#f9fafb" : "#fff"
  };

  const handleBlur = () => {
    setTouched(true);
    setFocused(false);
  };

  const handleFocus = () => {
    setFocused(true);
  };

  const handleChange = (e) => {
    onChange(fieldName, e.target.value);
  };

  const renderInput = () => {
    switch (type) {
      case "textarea":
        return (
          <textarea
            id={fieldName}
            name={fieldName}
            value={value || ""}
            onChange={handleChange}
            onBlur={handleBlur}
            onFocus={handleFocus}
            placeholder={placeholder}
            required={required}
            disabled={disabled}
            minLength={minLength}
            maxLength={maxLength}
            rows={5}
            style={{
              ...baseInputStyle,
              resize: "vertical",
              minHeight: "120px"
            }}
          />
        );

      case "select":
        return (
          <select
            id={fieldName}
            name={fieldName}
            value={value || ""}
            onChange={handleChange}
            onBlur={handleBlur}
            onFocus={handleFocus}
            required={required}
            disabled={disabled}
            style={{
              ...baseInputStyle,
              cursor: "pointer",
              appearance: "none",
              backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23666' d='M6 8L1 3h10z'/%3E%3C/svg%3E")`,
              backgroundRepeat: "no-repeat",
              backgroundPosition: "right 12px center",
              paddingRight: "36px"
            }}
          >
            <option value="">Selecione...</option>
            {options.map((opt, idx) => {
              const optValue = typeof opt === "object" ? opt.value : opt;
              const optLabel = typeof opt === "object" ? opt.label : opt;
              return (
                <option key={idx} value={optValue}>
                  {optLabel}
                </option>
              );
            })}
          </select>
        );

      case "number":
        return (
          <input
            type="number"
            id={fieldName}
            name={fieldName}
            value={value || ""}
            onChange={handleChange}
            onBlur={handleBlur}
            onFocus={handleFocus}
            placeholder={placeholder}
            required={required}
            disabled={disabled}
            min={min}
            max={max}
            style={baseInputStyle}
          />
        );

      case "date":
        return (
          <input
            type="date"
            id={fieldName}
            name={fieldName}
            value={value || ""}
            onChange={handleChange}
            onBlur={handleBlur}
            onFocus={handleFocus}
            required={required}
            disabled={disabled}
            style={baseInputStyle}
          />
        );

      case "email":
        return (
          <input
            type="email"
            id={fieldName}
            name={fieldName}
            value={value || ""}
            onChange={handleChange}
            onBlur={handleBlur}
            onFocus={handleFocus}
            placeholder={placeholder || "exemplo@email.com"}
            required={required}
            disabled={disabled}
            style={baseInputStyle}
          />
        );

      case "tel":
        return (
          <input
            type="tel"
            id={fieldName}
            name={fieldName}
            value={value || ""}
            onChange={handleChange}
            onBlur={handleBlur}
            onFocus={handleFocus}
            placeholder={placeholder || "(00) 00000-0000"}
            required={required}
            disabled={disabled}
            pattern={pattern}
            style={baseInputStyle}
          />
        );

      case "url":
        return (
          <input
            type="url"
            id={fieldName}
            name={fieldName}
            value={value || ""}
            onChange={handleChange}
            onBlur={handleBlur}
            onFocus={handleFocus}
            placeholder={placeholder || "https://exemplo.com"}
            required={required}
            disabled={disabled}
            style={baseInputStyle}
          />
        );

      default: // text
        return (
          <input
            type="text"
            id={fieldName}
            name={fieldName}
            value={value || ""}
            onChange={handleChange}
            onBlur={handleBlur}
            onFocus={handleFocus}
            placeholder={placeholder}
            required={required}
            disabled={disabled}
            minLength={minLength}
            maxLength={maxLength}
            pattern={pattern}
            style={baseInputStyle}
          />
        );
    }
  };

  return (
    <div 
      className="dynamic-field"
      style={{
        marginBottom: "24px",
        opacity: disabled ? 0.7 : 1
      }}
    >
      {/* Label + Badge Obrigatório + Botão IA */}
      <div style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        marginBottom: "8px"
      }}>
        <label 
          htmlFor={fieldName}
          style={{
            fontWeight: 600,
            fontSize: "0.95rem",
            color: "var(--text-primary)",
            display: "flex",
            alignItems: "center",
            gap: "8px"
          }}
        >
          {label}
          {required && (
            <span style={{
              fontSize: "0.75rem",
              padding: "2px 6px",
              background: "#fef2f2",
              color: "#dc2626",
              borderRadius: "4px",
              fontWeight: 500
            }}>
              Obrigatório
            </span>
          )}
        </label>

        {onAskAI && (
          <button
            type="button"
            onClick={() => onAskAI(field)}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "4px",
              padding: "4px 8px",
              fontSize: "0.8rem",
              color: "var(--primary)",
              background: "transparent",
              border: "1px solid var(--primary)",
              borderRadius: "6px",
              cursor: "pointer",
              transition: "all 0.2s"
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.background = "var(--primary)";
              e.currentTarget.style.color = "#fff";
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.background = "transparent";
              e.currentTarget.style.color = "var(--primary)";
            }}
          >
            <HelpCircle size={14} />
            Perguntar à IA
          </button>
        )}
      </div>

      {/* Help text */}
      {help && (
        <p style={{
          fontSize: "0.85rem",
          color: "var(--text-muted)",
          marginBottom: "10px",
          display: "flex",
          alignItems: "flex-start",
          gap: "6px"
        }}>
          💡 {help}
        </p>
      )}

      {/* Input */}
      {renderInput()}

      {/* Validation message */}
      {showError && (
        <div style={{
          display: "flex",
          alignItems: "center",
          gap: "6px",
          marginTop: "8px",
          color: "#dc2626",
          fontSize: "0.85rem"
        }}>
          <AlertCircle size={14} />
          Este campo é obrigatório
        </div>
      )}

      {/* Character count for textarea */}
      {type === "textarea" && maxLength && (
        <div style={{
          textAlign: "right",
          fontSize: "0.8rem",
          color: "var(--text-muted)",
          marginTop: "4px"
        }}>
          {(value || "").length} / {maxLength}
        </div>
      )}
    </div>
  );
}
