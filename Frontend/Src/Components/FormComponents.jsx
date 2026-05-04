/**
 * FORM COMPONENTS - INTRANET V2
 * Extended form components for professional data entry
 * 
 * Components:
 * - Select (dropdown)
 * - Textarea (multiline input)
 * - Checkbox
 * - Radio
 * - DatePicker
 * - FileUpload
 * - AutoComplete
 * - FormGroup
 */

import React, { useState, useRef } from 'react';
import { colors, spacing, typography, borderRadius, shadows } from './DesignSystem';

// ============================================================================
// SELECT COMPONENT
// ============================================================================

export const Select = ({
  label,
  options = [],
  value,
  onChange,
  error,
  helpText,
  fullWidth = true,
  size = 'md',
  disabled = false,
  required = false,
  placeholder = 'Select an option...',
  ...props
}) => {
  const selectStyles = {
    width: fullWidth ? '100%' : 'auto',
    padding: size === 'sm' ? spacing.sm : spacing.md,
    fontSize: size === 'sm' ? typography.fontSize.sm : typography.fontSize.base,
    fontFamily: typography.fontFamily.sans,
    border: `1px solid ${error ? colors.error.main : colors.gray[300]}`,
    borderRadius: borderRadius.md,
    backgroundColor: disabled ? colors.gray[100] : 'white',
    color: colors.gray[900],
    transition: 'all 0.2s ease-in-out',
    outline: 'none',
    cursor: disabled ? 'not-allowed' : 'pointer',
  };

  return (
    <div style={{ marginBottom: spacing.md }}>
      {label && (
        <label style={{
          display: 'block',
          marginBottom: spacing.xs,
          fontSize: typography.fontSize.sm,
          fontWeight: typography.fontWeight.medium,
          color: colors.gray[700],
        }}>
          {label}
          {required && <span style={{ color: colors.error.main, marginLeft: '4px' }}>*</span>}
        </label>
      )}

      <select
        value={value}
        onChange={onChange}
        disabled={disabled}
        style={selectStyles}
        {...props}
      >
        <option value="" disabled>{placeholder}</option>
        {options.map((option, index) => (
          <option
            key={option.value || index}
            value={option.value}
            disabled={option.disabled}
          >
            {option.label}
          </option>
        ))}
      </select>

      {error && (
        <p style={{
          margin: `${spacing.xs} 0 0 0`,
          fontSize: typography.fontSize.sm,
          color: colors.error.main,
        }}>
          {error}
        </p>
      )}

      {helpText && !error && (
        <p style={{
          margin: `${spacing.xs} 0 0 0`,
          fontSize: typography.fontSize.sm,
          color: colors.gray[500],
        }}>
          {helpText}
        </p>
      )}
    </div>
  );
};

// ============================================================================
// TEXTAREA COMPONENT
// ============================================================================

export const Textarea = ({
  label,
  error,
  helpText,
  fullWidth = true,
  rows = 4,
  disabled = false,
  required = false,
  maxLength,
  showCount = false,
  ...props
}) => {
  const [charCount, setCharCount] = useState(props.value?.length || 0);

  const textareaStyles = {
    width: fullWidth ? '100%' : 'auto',
    padding: spacing.md,
    fontSize: typography.fontSize.base,
    fontFamily: typography.fontFamily.sans,
    border: `1px solid ${error ? colors.error.main : colors.gray[300]}`,
    borderRadius: borderRadius.md,
    backgroundColor: disabled ? colors.gray[100] : 'white',
    color: colors.gray[900],
    transition: 'all 0.2s ease-in-out',
    outline: 'none',
    resize: 'vertical',
    minHeight: `${rows * 1.5}em`,
  };

  const handleChange = (e) => {
    setCharCount(e.target.value.length);
    if (props.onChange) {
      props.onChange(e);
    }
  };

  return (
    <div style={{ marginBottom: spacing.md }}>
      {label && (
        <label style={{
          display: 'block',
          marginBottom: spacing.xs,
          fontSize: typography.fontSize.sm,
          fontWeight: typography.fontWeight.medium,
          color: colors.gray[700],
        }}>
          {label}
          {required && <span style={{ color: colors.error.main, marginLeft: '4px' }}>*</span>}
        </label>
      )}

      <textarea
        rows={rows}
        disabled={disabled}
        maxLength={maxLength}
        style={textareaStyles}
        onChange={handleChange}
        {...props}
      />

      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: spacing.xs }}>
        <div>
          {error && (
            <p style={{
              margin: 0,
              fontSize: typography.fontSize.sm,
              color: colors.error.main,
            }}>
              {error}
            </p>
          )}

          {helpText && !error && (
            <p style={{
              margin: 0,
              fontSize: typography.fontSize.sm,
              color: colors.gray[500],
            }}>
              {helpText}
            </p>
          )}
        </div>

        {showCount && maxLength && (
          <span style={{
            fontSize: typography.fontSize.sm,
            color: charCount >= maxLength ? colors.error.main : colors.gray[500],
          }}>
            {charCount}/{maxLength}
          </span>
        )}
      </div>
    </div>
  );
};

// ============================================================================
// CHECKBOX COMPONENT
// ============================================================================

export const Checkbox = ({
  label,
  checked,
  onChange,
  disabled = false,
  error,
  ...props
}) => {
  return (
    <div style={{ marginBottom: spacing.sm }}>
      <label style={{
        display: 'flex',
        alignItems: 'center',
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.6 : 1,
      }}>
        <input
          type="checkbox"
          checked={checked}
          onChange={onChange}
          disabled={disabled}
          style={{
            width: '18px',
            height: '18px',
            marginRight: spacing.sm,
            cursor: disabled ? 'not-allowed' : 'pointer',
            accentColor: colors.primary[600],
          }}
          {...props}
        />
        <span style={{
          fontSize: typography.fontSize.base,
          color: colors.gray[900],
        }}>
          {label}
        </span>
      </label>

      {error && (
        <p style={{
          margin: `${spacing.xs} 0 0 0`,
          paddingLeft: '26px',
          fontSize: typography.fontSize.sm,
          color: colors.error.main,
        }}>
          {error}
        </p>
      )}
    </div>
  );
};

// ============================================================================
// RADIO COMPONENT
// ============================================================================

export const Radio = ({
  name,
  options = [],
  value,
  onChange,
  disabled = false,
  error,
  label,
  required = false,
  ...props
}) => {
  return (
    <div style={{ marginBottom: spacing.md }}>
      {label && (
        <label style={{
          display: 'block',
          marginBottom: spacing.sm,
          fontSize: typography.fontSize.sm,
          fontWeight: typography.fontWeight.medium,
          color: colors.gray[700],
        }}>
          {label}
          {required && <span style={{ color: colors.error.main, marginLeft: '4px' }}>*</span>}
        </label>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: spacing.sm }}>
        {options.map((option, index) => (
          <label
            key={option.value || index}
            style={{
              display: 'flex',
              alignItems: 'center',
              cursor: disabled || option.disabled ? 'not-allowed' : 'pointer',
              opacity: disabled || option.disabled ? 0.6 : 1,
            }}
          >
            <input
              type="radio"
              name={name}
              value={option.value}
              checked={value === option.value}
              onChange={onChange}
              disabled={disabled || option.disabled}
              style={{
                width: '18px',
                height: '18px',
                marginRight: spacing.sm,
                cursor: disabled || option.disabled ? 'not-allowed' : 'pointer',
                accentColor: colors.primary[600],
              }}
              {...props}
            />
            <span style={{
              fontSize: typography.fontSize.base,
              color: colors.gray[900],
            }}>
              {option.label}
            </span>
          </label>
        ))}
      </div>

      {error && (
        <p style={{
          margin: `${spacing.xs} 0 0 0`,
          fontSize: typography.fontSize.sm,
          color: colors.error.main,
        }}>
          {error}
        </p>
      )}
    </div>
  );
};

// ============================================================================
// DATE PICKER COMPONENT
// ============================================================================

export const DatePicker = ({
  label,
  value,
  onChange,
  error,
  helpText,
  fullWidth = true,
  size = 'md',
  disabled = false,
  required = false,
  min,
  max,
  ...props
}) => {
  const inputStyles = {
    width: fullWidth ? '100%' : 'auto',
    padding: size === 'sm' ? spacing.sm : spacing.md,
    fontSize: size === 'sm' ? typography.fontSize.sm : typography.fontSize.base,
    fontFamily: typography.fontFamily.sans,
    border: `1px solid ${error ? colors.error.main : colors.gray[300]}`,
    borderRadius: borderRadius.md,
    backgroundColor: disabled ? colors.gray[100] : 'white',
    color: colors.gray[900],
    transition: 'all 0.2s ease-in-out',
    outline: 'none',
  };

  return (
    <div style={{ marginBottom: spacing.md }}>
      {label && (
        <label style={{
          display: 'block',
          marginBottom: spacing.xs,
          fontSize: typography.fontSize.sm,
          fontWeight: typography.fontWeight.medium,
          color: colors.gray[700],
        }}>
          {label}
          {required && <span style={{ color: colors.error.main, marginLeft: '4px' }}>*</span>}
        </label>
      )}

      <input
        type="date"
        value={value}
        onChange={onChange}
        disabled={disabled}
        min={min}
        max={max}
        style={inputStyles}
        {...props}
      />

      {error && (
        <p style={{
          margin: `${spacing.xs} 0 0 0`,
          fontSize: typography.fontSize.sm,
          color: colors.error.main,
        }}>
          {error}
        </p>
      )}

      {helpText && !error && (
        <p style={{
          margin: `${spacing.xs} 0 0 0`,
          fontSize: typography.fontSize.sm,
          color: colors.gray[500],
        }}>
          {helpText}
        </p>
      )}
    </div>
  );
};

// ============================================================================
// FILE UPLOAD COMPONENT
// ============================================================================

export const FileUpload = ({
  label,
  onChange,
  error,
  helpText,
  accept,
  multiple = false,
  disabled = false,
  required = false,
  maxSize, // in MB
  ...props
}) => {
  const [fileName, setFileName] = useState('');
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      // Check file size if maxSize is specified
      if (maxSize) {
        const fileSizeMB = files[0].size / (1024 * 1024);
        if (fileSizeMB > maxSize) {
          alert(`File size must be less than ${maxSize}MB`);
          return;
        }
      }

      if (multiple) {
        setFileName(`${files.length} file(s) selected`);
      } else {
        setFileName(files[0].name);
      }

      if (onChange) {
        onChange(e);
      }
    }
  };

  const handleButtonClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div style={{ marginBottom: spacing.md }}>
      {label && (
        <label style={{
          display: 'block',
          marginBottom: spacing.xs,
          fontSize: typography.fontSize.sm,
          fontWeight: typography.fontWeight.medium,
          color: colors.gray[700],
        }}>
          {label}
          {required && <span style={{ color: colors.error.main, marginLeft: '4px' }}>*</span>}
        </label>
      )}

      <div style={{ display: 'flex', gap: spacing.sm, alignItems: 'center' }}>
        <input
          ref={fileInputRef}
          type="file"
          onChange={handleFileChange}
          accept={accept}
          multiple={multiple}
          disabled={disabled}
          style={{ display: 'none' }}
          {...props}
        />

        <button
          type="button"
          onClick={handleButtonClick}
          disabled={disabled}
          style={{
            padding: `${spacing.sm} ${spacing.md}`,
            fontSize: typography.fontSize.base,
            fontWeight: typography.fontWeight.medium,
            borderRadius: borderRadius.md,
            border: `1px solid ${colors.gray[300]}`,
            backgroundColor: disabled ? colors.gray[100] : 'white',
            color: colors.gray[700],
            cursor: disabled ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s ease-in-out',
          }}
        >
          Choose File
        </button>

        <span style={{
          fontSize: typography.fontSize.sm,
          color: colors.gray[600],
        }}>
          {fileName || 'No file chosen'}
        </span>
      </div>

      {error && (
        <p style={{
          margin: `${spacing.xs} 0 0 0`,
          fontSize: typography.fontSize.sm,
          color: colors.error.main,
        }}>
          {error}
        </p>
      )}

      {helpText && !error && (
        <p style={{
          margin: `${spacing.xs} 0 0 0`,
          fontSize: typography.fontSize.sm,
          color: colors.gray[500],
        }}>
          {helpText}
        </p>
      )}
    </div>
  );
};

// ============================================================================
// AUTOCOMPLETE COMPONENT
// ============================================================================

export const AutoComplete = ({
  label,
  options = [],
  value,
  onChange,
  onSelect,
  error,
  helpText,
  fullWidth = true,
  size = 'md',
  disabled = false,
  required = false,
  placeholder = 'Type to search...',
  ...props
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [filteredOptions, setFilteredOptions] = useState(options);

  const handleInputChange = (e) => {
    const inputValue = e.target.value;
    onChange(e);

    // Filter options based on input
    const filtered = options.filter(option =>
      option.label.toLowerCase().includes(inputValue.toLowerCase())
    );
    setFilteredOptions(filtered);
    setIsOpen(filtered.length > 0);
  };

  const handleOptionClick = (option) => {
    if (onSelect) {
      onSelect(option);
    }
    setIsOpen(false);
  };

  const inputStyles = {
    width: fullWidth ? '100%' : 'auto',
    padding: size === 'sm' ? spacing.sm : spacing.md,
    fontSize: size === 'sm' ? typography.fontSize.sm : typography.fontSize.base,
    fontFamily: typography.fontFamily.sans,
    border: `1px solid ${error ? colors.error.main : colors.gray[300]}`,
    borderRadius: borderRadius.md,
    backgroundColor: disabled ? colors.gray[100] : 'white',
    color: colors.gray[900],
    transition: 'all 0.2s ease-in-out',
    outline: 'none',
  };

  return (
    <div style={{ marginBottom: spacing.md, position: 'relative' }}>
      {label && (
        <label style={{
          display: 'block',
          marginBottom: spacing.xs,
          fontSize: typography.fontSize.sm,
          fontWeight: typography.fontWeight.medium,
          color: colors.gray[700],
        }}>
          {label}
          {required && <span style={{ color: colors.error.main, marginLeft: '4px' }}>*</span>}
        </label>
      )}

      <input
        type="text"
        value={value}
        onChange={handleInputChange}
        onFocus={() => setIsOpen(filteredOptions.length > 0)}
        onBlur={() => setTimeout(() => setIsOpen(false), 200)}
        disabled={disabled}
        placeholder={placeholder}
        style={inputStyles}
        {...props}
      />

      {isOpen && filteredOptions.length > 0 && (
        <div style={{
          position: 'absolute',
          top: '100%',
          left: 0,
          right: 0,
          marginTop: spacing.xs,
          backgroundColor: 'white',
          border: `1px solid ${colors.gray[300]}`,
          borderRadius: borderRadius.md,
          boxShadow: shadows.lg,
          maxHeight: '200px',
          overflowY: 'auto',
          zIndex: 1000,
        }}>
          {filteredOptions.map((option, index) => (
            <div
              key={option.value || index}
              onClick={() => handleOptionClick(option)}
              style={{
                padding: spacing.md,
                cursor: 'pointer',
                borderBottom: index < filteredOptions.length - 1 ? `1px solid ${colors.gray[200]}` : 'none',
                transition: 'background-color 0.2s ease',
              }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = colors.gray[50]}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'white'}
            >
              {option.label}
            </div>
          ))}
        </div>
      )}

      {error && (
        <p style={{
          margin: `${spacing.xs} 0 0 0`,
          fontSize: typography.fontSize.sm,
          color: colors.error.main,
        }}>
          {error}
        </p>
      )}

      {helpText && !error && (
        <p style={{
          margin: `${spacing.xs} 0 0 0`,
          fontSize: typography.fontSize.sm,
          color: colors.gray[500],
        }}>
          {helpText}
        </p>
      )}
    </div>
  );
};

// ============================================================================
// FORM GROUP COMPONENT
// ============================================================================

export const FormGroup = ({
  children,
  title,
  subtitle,
  columns = 1,
  gap = spacing.md,
}) => {
  const gridStyles = {
    display: 'grid',
    gridTemplateColumns: `repeat(${columns}, 1fr)`,
    gap: gap,
  };

  return (
    <div style={{ marginBottom: spacing.xl }}>
      {(title || subtitle) && (
        <div style={{ marginBottom: spacing.md }}>
          {title && (
            <h3 style={{
              margin: 0,
              fontSize: typography.fontSize.lg,
              fontWeight: typography.fontWeight.semibold,
              color: colors.gray[900],
            }}>
              {title}
            </h3>
          )}
          {subtitle && (
            <p style={{
              margin: '4px 0 0 0',
              fontSize: typography.fontSize.sm,
              color: colors.gray[600],
            }}>
              {subtitle}
            </p>
          )}
        </div>
      )}

      <div style={gridStyles}>
        {children}
      </div>
    </div>
  );
};

export default {
  Select,
  Textarea,
  Checkbox,
  Radio,
  DatePicker,
  FileUpload,
  AutoComplete,
  FormGroup,
};
