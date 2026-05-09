

import React from 'react';

// ============================================================================// DESIGNTOKENS// ============================================================================
export const colors = {
  // PrimaryBrandColors  primary: {
    50: '#f0f9ff',
    100: '#e0f2fe',
    200: '#bae6fd',
    300: '#7dd3fc',
    400: '#38bdf8',
    500: '#0ea5e9',
    600: '#0284c7',
    700: '#0369a1',
    800: '#075985',
    900: '#0c4a6e',
  },
  
  // SecondaryColors  secondary: {
    50: '#faf5ff',
    100: '#f3e8ff',
    200: '#e9d5ff',
    300: '#d8b4fe',
    400: '#c084fc',
    500: '#a855f7',
    600: '#9333ea',
    700: '#7e22ce',
    800: '#6b21a8',
    900: '#581c87',
  },
  
  // Neutral/GrayScale  gray: {
    50: '#f9fafb',
    100: '#f3f4f6',
    200: '#e5e7eb',
    300: '#d1d5db',
    400: '#9ca3af',
    500: '#6b7280',
    600: '#4b5563',
    700: '#374151',
    800: '#1f2937',
    900: '#111827',
  },
  
  // SemanticColors  success: {
    light: '#d1fae5',
    main: '#10b981',
    dark: '#059669',
  },
  warning: {
    light: '#fef3c7',
    main: '#f59e0b',
    dark: '#d97706',
  },
  error: {
    light: '#fee2e2',
    main: '#ef4444',
    dark: '#dc2626',
  },
  info: {
    light: '#dbeafe',
    main: '#3b82f6',
    dark: '#2563eb',
  },
};

export const spacing = {
  xs: '0.25rem',    // 4px  sm: '0.5rem',     // 8px  md: '1rem',       // 16px  lg: '1.5rem',     // 24px  xl: '2rem',       // 32px  '2xl': '3rem',    // 48px  '3xl': '4rem',    // 64px};

export const typography = {
  fontFamily: {
    sans: "'Inter', 'SegoeUI', 'Roboto', Sans-Serif",
    mono: "'FiraCode', 'Consolas', Monospace",
  },
  fontSize: {
    xs: '0.75rem',      // 12px    sm: '0.875rem',     // 14px    base: '1rem',       // 16px    lg: '1.125rem',     // 18px    xl: '1.25rem',      // 20px    '2xl': '1.5rem',    // 24px    '3xl': '1.875rem',  // 30px    '4xl': '2.25rem',   // 36px  },
  fontWeight: {
    light: 300,
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
};

export const shadows = {
  sm: '01px2px0Rgba(0, 0, 0, 0.05)',
  md: '04px6px -1pxRgba(0, 0, 0, 0.1), 02px4px -1pxRgba(0, 0, 0, 0.06)',
  lg: '010px15px -3pxRgba(0, 0, 0, 0.1), 04px6px -2pxRgba(0, 0, 0, 0.05)',
  xl: '020px25px -5pxRgba(0, 0, 0, 0.1), 010px10px -5pxRgba(0, 0, 0, 0.04)',
};

export const borderRadius = {
  sm: '0.25rem',
  md: '0.375rem',
  lg: '0.5rem',
  xl: '0.75rem',
  full: '9999px',
};

// ============================================================================// BUTTONCOMPONENT// ============================================================================
export const Button = ({
  children,
  variant = 'primary',
  size = 'md',
  fullWidth = false,
  disabled = false,
  loading = false,
  leftIcon,
  rightIcon,
  onClick,
  type = 'button',
  className = '',
  ...props
}) => {
  const baseStyles = {
    display: 'Inline-Flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontFamily: typography.fontFamily.sans,
    fontWeight: typography.fontWeight.medium,
    borderRadius: borderRadius.md,
    border: 'none',
    cursor: disabled || loading ? 'Not-Allowed' : 'pointer',
    transition: 'All0.2sEase-In-Out',
    opacity: disabled || loading ? 0.6 : 1,
    width: fullWidth ? '100%' : 'auto',
  };

  const variants = {
    primary: {
      backgroundColor: colors.primary[600],
      color: 'white',
      ':hover': { backgroundColor: colors.primary[700] },
    },
    secondary: {
      backgroundColor: colors.gray[200],
      color: colors.gray[900],
      ':hover': { backgroundColor: colors.gray[300] },
    },
    success: {
      backgroundColor: colors.success.main,
      color: 'white',
      ':hover': { backgroundColor: colors.success.dark },
    },
    danger: {
      backgroundColor: colors.error.main,
      color: 'white',
      ':hover': { backgroundColor: colors.error.dark },
    },
    outline: {
      backgroundColor: 'transparent',
      color: colors.primary[600],
      border: `2px solid ${colors.primary[600]}`,
      ':hover': { backgroundColor: colors.primary[50] },
    },
    ghost: {
      backgroundColor: 'transparent',
      color: colors.gray[700],
      ':hover': { backgroundColor: colors.gray[100] },
    },
  };

  const sizes = {
    sm: {
      padding: `${spacing.xs} ${spacing.sm}`,
      fontSize: typography.fontSize.sm,
      gap: spacing.xs,
    },
    md: {
      padding: `${spacing.sm} ${spacing.md}`,
      fontSize: typography.fontSize.base,
      gap: spacing.sm,
    },
    lg: {
      padding: `${spacing.md} ${spacing.lg}`,
      fontSize: typography.fontSize.lg,
      gap: spacing.sm,
    },
  };

  const styles = {
    ...baseStyles,
    ...variants[variant],
    ...sizes[size],
  };

  return (
    <button
      type={type}
      disabled={disabled || loading}
      onClick={onClick}
      style={styles}
      className={className}
      {...props}
    >
      {loading && <Spinner size={size === 'sm' ? 'xs' : 'sm'} />}
      {!loading && leftIcon && leftIcon}
      {children}
      {!loading && rightIcon && rightIcon}
    </button>
  );
};

// ============================================================================// CARDCOMPONENT// ============================================================================
export const Card = ({
  children,
  title,
  subtitle,
  headerActions,
  padding = 'md',
  hoverable = false,
  className = '',
  ...props
}) => {
  const styles = {
    backgroundColor: 'white',
    borderRadius: borderRadius.lg,
    boxShadow: shadows.md,
    transition: 'All0.2sEase-In-Out',
    cursor: hoverable ? 'pointer' : 'default',
    ':hover': hoverable ? { boxShadow: shadows.lg } : {},
  };

  const paddingMap = {
    none: '0',
    sm: spacing.sm,
    md: spacing.md,
    lg: spacing.lg,
    xl: spacing.xl,
  };

  return (
    <div style={styles} className={className} {...props}>
      {(title || subtitle || headerActions) && (
        <div style={{
          padding: paddingMap[padding],
          borderBottom: `1px solid ${colors.gray[200]}`,
          display: 'flex',
          justifyContent: 'Space-Between',
          alignItems: 'center',
        }}>
          <div>
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
                margin: '4px000',
                fontSize: typography.fontSize.sm,
                color: colors.gray[600],
              }}>
                {subtitle}
              </p>
            )}
          </div>
          {headerActions && <div>{headerActions}</div>}
        </div>
      )}
      <div style={{ padding: paddingMap[padding] }}>
        {children}
      </div>
    </div>
  );
};

// ============================================================================// INPUTCOMPONENT// ============================================================================
export const Input = ({
  label,
  error,
  helpText,
  leftIcon,
  rightIcon,
  fullWidth = true,
  size = 'md',
  disabled = false,
  required = false,
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
    transition: 'All0.2sEase-In-Out',
    outline: 'none',
    ':focus': {
      borderColor: error ? colors.error.main : colors.primary[500],
      boxShadow: `0 0 0 3px ${error ? colors.error.light : colors.primary[100]}`,
    },
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
      
      <div style={{ position: 'relative' }}>
        {leftIcon && (
          <div style={{
            position: 'absolute',
            left: spacing.sm,
            top: '50%',
            transform: 'TranslateY(-50%)',
            color: colors.gray[400],
          }}>
            {leftIcon}
          </div>
        )}
        
        <input
          style={{
            ...inputStyles,
            paddingLeft: leftIcon ? '2.5rem' : inputStyles.padding,
            paddingRight: rightIcon ? '2.5rem' : inputStyles.padding,
          }}
          disabled={disabled}
          {...props}
        />
        
        {rightIcon && (
          <div style={{
            position: 'absolute',
            right: spacing.sm,
            top: '50%',
            transform: 'TranslateY(-50%)',
            color: colors.gray[400],
          }}>
            {rightIcon}
          </div>
        )}
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

// ============================================================================// BADGECOMPONENT// ============================================================================
export const Badge = ({
  children,
  variant = 'default',
  size = 'md',
  ...props
}) => {
  const variants = {
    default: {
      backgroundColor: colors.gray[200],
      color: colors.gray[800],
    },
    primary: {
      backgroundColor: colors.primary[100],
      color: colors.primary[800],
    },
    success: {
      backgroundColor: colors.success.light,
      color: colors.success.dark,
    },
    warning: {
      backgroundColor: colors.warning.light,
      color: colors.warning.dark,
    },
    error: {
      backgroundColor: colors.error.light,
      color: colors.error.dark,
    },
  };

  const sizes = {
    sm: {
      padding: `2px ${spacing.xs}`,
      fontSize: typography.fontSize.xs,
    },
    md: {
      padding: `${spacing.xs} ${spacing.sm}`,
      fontSize: typography.fontSize.sm,
    },
  };

  const styles = {
    display: 'Inline-Flex',
    alignItems: 'center',
    fontWeight: typography.fontWeight.medium,
    borderRadius: borderRadius.full,
    ...variants[variant],
    ...sizes[size],
  };

  return <span style={styles} {...props}>{children}</span>;
};

// ============================================================================// SPINNERCOMPONENT// ============================================================================
export const Spinner = ({ size = 'md', color = colors.primary[600] }) => {
  const sizes = {
    xs: '12px',
    sm: '16px',
    md: '24px',
    lg: '32px',
    xl: '48px',
  };

  return (
    <div
      style={{
        width: sizes[size],
        height: sizes[size],
        border: `2px solid ${colors.gray[200]}`,
        borderTopColor: color,
        borderRadius: '50%',
        animation: 'Spin0.8sLinearInfinite',
      }}
    />
  );
};

// ============================================================================// ALERTCOMPONENT// ============================================================================
export const Alert = ({
  children,
  variant = 'info',
  title,
  onClose,
  ...props
}) => {
  const variants = {
    info: {
      backgroundColor: colors.info.light,
      borderColor: colors.info.main,
      color: colors.info.dark,
    },
    success: {
      backgroundColor: colors.success.light,
      borderColor: colors.success.main,
      color: colors.success.dark,
    },
    warning: {
      backgroundColor: colors.warning.light,
      borderColor: colors.warning.main,
      color: colors.warning.dark,
    },
    error: {
      backgroundColor: colors.error.light,
      borderColor: colors.error.main,
      color: colors.error.dark,
    },
  };

  const styles = {
    padding: spacing.md,
    borderRadius: borderRadius.md,
    borderLeft: `4px solid`,
    display: 'flex',
    justifyContent: 'Space-Between',
    alignItems: 'Flex-Start',
    ...variants[variant],
  };

  return (
    <div style={styles} {...props}>
      <div style={{ flex: 1 }}>
        {title && (
          <h4 style={{
            margin: 0,
            marginBottom: spacing.xs,
            fontWeight: typography.fontWeight.semibold,
            fontSize: typography.fontSize.base,
          }}>
            {title}
          </h4>
        )}
        <div style={{ fontSize: typography.fontSize.sm }}>
          {children}
        </div>
      </div>
      {onClose && (
        <button
          onClick={onClose}
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            padding: spacing.xs,
            marginLeft: spacing.md,
          }}
        >
          ×
        </button>
      )}
    </div>
  );
};

// ============================================================================// MODALCOMPONENT// ============================================================================
export const Modal = ({
  isOpen,
  onClose,
  title,
  children,
  footer,
  size = 'md',
  ...props
}) => {
  if (!isOpen) return null;

  const sizes = {
    sm: '400px',
    md: '600px',
    lg: '800px',
    xl: '1200px',
    full: '90vw',
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'Rgba(0, 0, 0, 0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
        padding: spacing.md,
      }}
      onClick={onClose}
    >
      <div
        style={{
          backgroundColor: 'white',
          borderRadius: borderRadius.lg,
          boxShadow: shadows.xl,
          maxWidth: sizes[size],
          width: '100%',
          maxHeight: '90vh',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
        }}
        onClick={(e) => e.stopPropagation()}
        {...props}
      >
        {/* Header */}
        <div
          style={{
            padding: spacing.lg,
            borderBottom: `1px solid ${colors.gray[200]}`,
            display: 'flex',
            justifyContent: 'Space-Between',
            alignItems: 'center',
          }}
        >
          <h2 style={{
            margin: 0,
            fontSize: typography.fontSize['2xl'],
            fontWeight: typography.fontWeight.semibold,
          }}>
            {title}
          </h2>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '24px',
              cursor: 'pointer',
              color: colors.gray[500],
              padding: spacing.xs,
            }}
          >
            ×
          </button>
        </div>

        {/* Body */}
        <div style={{
          padding: spacing.lg,
          overflow: 'auto',
          flex: 1,
        }}>
          {children}
        </div>

        {/* Footer */}
        {footer && (
          <div style={{
            padding: spacing.lg,
            borderTop: `1px solid ${colors.gray[200]}`,
            display: 'flex',
            justifyContent: 'Flex-End',
            gap: spacing.sm,
          }}>
            {footer}
          </div>
        )}
      </div>
    </div>
  );
};

// ============================================================================// TABLECOMPONENT// ============================================================================
export const Table = ({ columns, data, onRowClick, striped = true }) => {
  return (
    <div style={{ overflow: 'auto' }}>
      <table style={{
        width: '100%',
        borderCollapse: 'collapse',
        fontSize: typography.fontSize.sm,
      }}>
        <thead>
          <tr style={{
            backgroundColor: colors.gray[50],
            borderBottom: `2px solid ${colors.gray[200]}`,
          }}>
            {columns.map((column, index) => (
              <th
                key={index}
                style={{
                  padding: spacing.md,
                  textAlign: column.align || 'left',
                  fontWeight: typography.fontWeight.semibold,
                  color: colors.gray[700],
                }}
              >
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, rowIndex) => (
            <tr
              key={rowIndex}
              onClick={() => onRowClick && onRowClick(row)}
              style={{
                backgroundColor: striped && rowIndex % 2 === 1 ? colors.gray[50] : 'white',
                cursor: onRowClick ? 'pointer' : 'default',
                borderBottom: `1px solid ${colors.gray[200]}`,
                transition: 'Background-Color0.2sEase',
                ':hover': onRowClick ? { backgroundColor: colors.gray[100] } : {},
              }}
            >
              {columns.map((column, colIndex) => (
                <td
                  key={colIndex}
                  style={{
                    padding: spacing.md,
                    textAlign: column.align || 'left',
                  }}
                >
                  {column.render ? column.render(row) : row[column.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

// ============================================================================// TABSCOMPONENT// ============================================================================
export const Tabs = ({ tabs, activeTab, onChange }) => {
  return (
    <div>
      <div style={{
        borderBottom: `2px solid ${colors.gray[200]}`,
        display: 'flex',
        gap: spacing.md,
      }}>
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => onChange(tab.key)}
            style={{
              padding: `${spacing.sm} ${spacing.md}`,
              background: 'none',
              border: 'none',
              borderBottom: `2px solid ${activeTab === tab.key ? colors.primary[600] : 'transparent'}`,
              color: activeTab === tab.key ? colors.primary[600] : colors.gray[600],
              fontWeight: activeTab === tab.key ? typography.fontWeight.semibold : typography.fontWeight.normal,
              cursor: 'pointer',
              transition: 'All0.2sEase',
              marginBottom: '-2px',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div style={{ padding: spacing.lg }}>
        {tabs.find(tab => tab.key === activeTab)?.content}
      </div>
    </div>
  );
};

// AddCSSAnimations
if (typeof document !== 'undefined') {
  const style = document.createElement('style');
  style.textContent = `
    @keyframes spin {
      to { transform: rotate(360deg); }
    }
  `;
  document.head.appendChild(style);
}

export default {
  colors,
  spacing,
  typography,
  shadows,
  borderRadius,
  Button,
  Card,
  Input,
  Badge,
  Spinner,
  Alert,
  Modal,
  Table,
  Tabs,
};
