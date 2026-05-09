
import React, { useState, useEffect } from 'react';
import { colors, spacing, typography, borderRadius, shadows } from './DesignSystem';

// ============================================================================// BREADCRUMBCOMPONENT// ============================================================================
export const Breadcrumb = ({ items = [], separator = '/' }) => {
  return (
    <nav style={{
      display: 'flex',
      alignItems: 'center',
      gap: spacing.sm,
      marginBottom: spacing.md,
      fontSize: typography.fontSize.sm,
    }}>
      {items.map((item, index) => (
        <React.Fragment key={index}>
          {index > 0 && (
            <span style={{ color: colors.gray[400] }}>{separator}</span>
          )}
          {item.href ? (
            <a
              href={item.href}
              onClick={item.onClick}
              style={{
                color: index === items.length - 1 ? colors.gray[900] : colors.primary[600],
                textDecoration: 'none',
                fontWeight: index === items.length - 1 ? typography.fontWeight.semibold : typography.fontWeight.normal,
              }}
            >
              {item.label}
            </a>
          ) : (
            <span style={{
              color: colors.gray[900],
              fontWeight: typography.fontWeight.semibold,
            }}>
              {item.label}
            </span>
          )}
        </React.Fragment>
      ))}
    </nav>
  );
};

// ============================================================================// PAGINATIONCOMPONENT// ============================================================================
export const Pagination = ({
  currentPage,
  totalPages,
  onPageChange,
  showFirstLast = true,
  maxVisible = 7,
}) => {
  const getPageNumbers = () => {
    const pages = [];
    const halfVisible = Math.floor(maxVisible / 2);
    
    let startPage = Math.max(1, currentPage - halfVisible);
    let endPage = Math.min(totalPages, currentPage + halfVisible);
    
    if (currentPage <= halfVisible) {
      endPage = Math.min(totalPages, maxVisible);
    }
    if (currentPage + halfVisible >= totalPages) {
      startPage = Math.max(1, totalPages - maxVisible + 1);
    }
    
    for (let i = startPage; i <= endPage; i++) {
      pages.push(i);
    }
    
    return pages;
  };

  const buttonStyles = (isActive = false, isDisabled = false) => ({
    padding: `${spacing.xs} ${spacing.sm}`,
    margin: `0 ${spacing.xs}`,
    fontSize: typography.fontSize.sm,
    fontWeight: isActive ? typography.fontWeight.semibold : typography.fontWeight.normal,
    border: `1px solid ${isActive ? colors.primary[600] : colors.gray[300]}`,
    borderRadius: borderRadius.md,
    backgroundColor: isActive ? colors.primary[600] : 'white',
    color: isActive ? 'white' : isDisabled ? colors.gray[400] : colors.gray[700],
    cursor: isDisabled ? 'Not-Allowed' : 'pointer',
    transition: 'All0.2sEase',
    minWidth: '36px',
    opacity: isDisabled ? 0.5 : 1,
  });

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: spacing.xs,
      marginTop: spacing.lg,
    }}>
      {showFirstLast && (
        <button
          onClick={() => onPageChange(1)}
          disabled={currentPage === 1}
          style={buttonStyles(false, currentPage === 1)}
        >
          First
        </button>
      )}

      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        style={buttonStyles(false, currentPage === 1)}
      >
        ‹
      </button>

      {getPageNumbers().map(page => (
        <button
          key={page}
          onClick={() => onPageChange(page)}
          style={buttonStyles(page === currentPage)}
        >
          {page}
        </button>
      ))}

      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        style={buttonStyles(false, currentPage === totalPages)}
      >
        ›
      </button>

      {showFirstLast && (
        <button
          onClick={() => onPageChange(totalPages)}
          disabled={currentPage === totalPages}
          style={buttonStyles(false, currentPage === totalPages)}
        >
          Last
        </button>
      )}
    </div>
  );
};

// ============================================================================// TOASTNOTIFICATIONCOMPONENT// ============================================================================
export const Toast = ({ message, type = 'info', onClose, duration = 5000 }) => {
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => {
        setIsVisible(false);
        if (onClose) onClose();
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [duration, onClose]);

  if (!isVisible) return null;

  const variants = {
    success: {
      backgroundColor: colors.success.light,
      borderColor: colors.success.main,
      color: colors.success.dark,
      icon: '✓',
    },
    error: {
      backgroundColor: colors.error.light,
      borderColor: colors.error.main,
      color: colors.error.dark,
      icon: '✕',
    },
    warning: {
      backgroundColor: colors.warning.light,
      borderColor: colors.warning.main,
      color: colors.warning.dark,
      icon: '⚠',
    },
    info: {
      backgroundColor: colors.info.light,
      borderColor: colors.info.main,
      color: colors.info.dark,
      icon: 'ℹ',
    },
  };

  const variant = variants[type];

  return (
    <div style={{
      position: 'fixed',
      top: spacing.lg,
      right: spacing.lg,
      zIndex: 9999,
      minWidth: '300px',
      maxWidth: '500px',
      padding: spacing.md,
      backgroundColor: variant.backgroundColor,
      border: `1px solid ${variant.borderColor}`,
      borderLeft: `4px solid ${variant.borderColor}`,
      borderRadius: borderRadius.md,
      boxShadow: shadows.lg,
      display: 'flex',
      alignItems: 'Flex-Start',
      gap: spacing.sm,
      animation: 'SlideInRight0.3sEase-Out',
    }}>
      <span style={{
        fontSize: typography.fontSize.lg,
        fontWeight: typography.fontWeight.bold,
      }}>
        {variant.icon}
      </span>
      <p style={{
        flex: 1,
        margin: 0,
        fontSize: typography.fontSize.sm,
        color: variant.color,
      }}>
        {message}
      </p>
      <button
        onClick={() => {
          setIsVisible(false);
          if (onClose) onClose();
        }}
        style={{
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          fontSize: typography.fontSize.lg,
          color: variant.color,
          padding: spacing.xs,
        }}
      >
        ×
      </button>
    </div>
  );
};

// ============================================================================// PROGRESSBARCOMPONENT// ============================================================================
export const Progress = ({
  value = 0,
  max = 100,
  size = 'md',
  variant = 'primary',
  showLabel = true,
  label,
}) => {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100));

  const sizes = {
    sm: '6px',
    md: '10px',
    lg: '14px',
  };

  const variants = {
    primary: colors.primary[600],
    success: colors.success.main,
    warning: colors.warning.main,
    error: colors.error.main,
  };

  return (
    <div style={{ marginBottom: spacing.md }}>
      {showLabel && (
        <div style={{
          display: 'flex',
          justifyContent: 'Space-Between',
          marginBottom: spacing.xs,
          fontSize: typography.fontSize.sm,
          color: colors.gray[700],
        }}>
          <span>{label || 'Progress'}</span>
          <span>{Math.round(percentage)}%</span>
        </div>
      )}
      <div style={{
        width: '100%',
        height: sizes[size],
        backgroundColor: colors.gray[200],
        borderRadius: borderRadius.full,
        overflow: 'hidden',
      }}>
        <div style={{
          width: `${percentage}%`,
          height: '100%',
          backgroundColor: variants[variant],
          transition: 'Width0.3sEase',
          borderRadius: borderRadius.full,
        }} />
      </div>
    </div>
  );
};

// ============================================================================// AVATARCOMPONENT// ============================================================================
export const Avatar = ({
  src,
  alt,
  name,
  size = 'md',
  variant = 'circle',
  showStatus,
  status = 'offline',
}) => {
  const sizes = {
    xs: '24px',
    sm: '32px',
    md: '40px',
    lg: '64px',
    xl: '96px',
  };

  const statusColors = {
    online: colors.success.main,
    offline: colors.gray[400],
    away: colors.warning.main,
    busy: colors.error.main,
  };

  const getInitials = (name) => {
    if (!name) return '?';
    const parts = name.split(' ');
    if (parts.length >= 2) {
      return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
  };

  const avatarStyles = {
    width: sizes[size],
    height: sizes[size],
    borderRadius: variant === 'circle' ? '50%' : borderRadius.md,
    backgroundColor: colors.primary[100],
    color: colors.primary[700],
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: size === 'xs' || size === 'sm' ? typography.fontSize.xs : typography.fontSize.base,
    fontWeight: typography.fontWeight.semibold,
    position: 'relative',
    overflow: 'hidden',
  };

  return (
    <div style={avatarStyles}>
      {src ? (
        <img src={src} alt={alt || name} style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
        }} />
      ) : (
        <span>{getInitials(name)}</span>
      )}

      {showStatus && (
        <span style={{
          position: 'absolute',
          bottom: 0,
          right: 0,
          width: size === 'xs' ? '6px' : size === 'sm' ? '8px' : '10px',
          height: size === 'xs' ? '6px' : size === 'sm' ? '8px' : '10px',
          backgroundColor: statusColors[status],
          border: '2pxSolidWhite',
          borderRadius: '50%',
        }} />
      )}
    </div>
  );
};

// ============================================================================// TOOLTIPCOMPONENT// ============================================================================
export const Tooltip = ({ children, text, position = 'top' }) => {
  const [isVisible, setIsVisible] = useState(false);

  const positions = {
    top: { bottom: '100%', left: '50%', transform: 'TranslateX(-50%)', marginBottom: spacing.xs },
    bottom: { top: '100%', left: '50%', transform: 'TranslateX(-50%)', marginTop: spacing.xs },
    left: { right: '100%', top: '50%', transform: 'TranslateY(-50%)', marginRight: spacing.xs },
    right: { left: '100%', top: '50%', transform: 'TranslateY(-50%)', marginLeft: spacing.xs },
  };

  return (
    <div
      style={{ position: 'relative', display: 'Inline-Block' }}
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
    >
      {children}
      {isVisible && (
        <div style={{
          position: 'absolute',
          zIndex: 1000,
          padding: `${spacing.xs} ${spacing.sm}`,
          backgroundColor: colors.gray[900],
          color: 'white',
          fontSize: typography.fontSize.sm,
          borderRadius: borderRadius.md,
          whiteSpace: 'nowrap',
          boxShadow: shadows.lg,
          ...positions[position],
        }}>
          {text}
        </div>
      )}
    </div>
  );
};

// ============================================================================// EMPTYSTATECOMPONENT// ============================================================================
export const EmptyState = ({
  icon,
  title,
  description,
  action,
  actionText,
}) => {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: spacing['3xl'],
      textAlign: 'center',
    }}>
      {icon && (
        <div style={{
          fontSize: '48px',
          marginBottom: spacing.md,
          color: colors.gray[400],
        }}>
          {icon}
        </div>
      )}

      {title && (
        <h3 style={{
          margin: 0,
          marginBottom: spacing.sm,
          fontSize: typography.fontSize.xl,
          fontWeight: typography.fontWeight.semibold,
          color: colors.gray[900],
        }}>
          {title}
        </h3>
      )}

      {description && (
        <p style={{
          margin: 0,
          marginBottom: spacing.lg,
          fontSize: typography.fontSize.base,
          color: colors.gray[600],
          maxWidth: '400px',
        }}>
          {description}
        </p>
      )}

      {action && actionText && (
        <button
          onClick={action}
          style={{
            padding: `${spacing.sm} ${spacing.lg}`,
            fontSize: typography.fontSize.base,
            fontWeight: typography.fontWeight.medium,
            borderRadius: borderRadius.md,
            border: 'none',
            backgroundColor: colors.primary[600],
            color: 'white',
            cursor: 'pointer',
            transition: 'Background-Color0.2sEase',
          }}
        >
          {actionText}
        </button>
      )}
    </div>
  );
};

// ============================================================================// LOADINGSKELETONCOMPONENT// ============================================================================
export const LoadingSkeleton = ({
  type = 'text',
  count = 1,
  height = '16px',
  width = '100%',
}) => {
  const renderSkeleton = () => {
    switch (type) {
      case 'text':
        return Array.from({ length: count }).map((_, index) => (
          <div
            key={index}
            style={{
              height,
              width: index === count - 1 ? '60%' : width,
              backgroundColor: colors.gray[200],
              borderRadius: borderRadius.md,
              marginBottom: spacing.sm,
              animation: 'Pulse1.5sEase-In-OutInfinite',
            }}
          />
        ));

      case 'circle':
        return (
          <div style={{
            width: height,
            height: height,
            backgroundColor: colors.gray[200],
            borderRadius: '50%',
            animation: 'Pulse1.5sEase-In-OutInfinite',
          }} />
        );

      case 'rect':
        return (
          <div style={{
            width: width,
            height: height,
            backgroundColor: colors.gray[200],
            borderRadius: borderRadius.md,
            animation: 'Pulse1.5sEase-In-OutInfinite',
          }} />
        );

      case 'card':
        return (
          <div style={{
            padding: spacing.lg,
            backgroundColor: 'white',
            borderRadius: borderRadius.lg,
            boxShadow: shadows.md,
          }}>
            <div style={{
              height: '120px',
              backgroundColor: colors.gray[200],
              borderRadius: borderRadius.md,
              marginBottom: spacing.md,
              animation: 'Pulse1.5sEase-In-OutInfinite',
            }} />
            <div style={{
              height: '20px',
              width: '60%',
              backgroundColor: colors.gray[200],
              borderRadius: borderRadius.md,
              marginBottom: spacing.sm,
              animation: 'Pulse1.5sEase-In-OutInfinite',
            }} />
            <div style={{
              height: '16px',
              width: '80%',
              backgroundColor: colors.gray[200],
              borderRadius: borderRadius.md,
              animation: 'Pulse1.5sEase-In-OutInfinite',
            }} />
          </div>
        );

      default:
        return null;
    }
  };

  return <div>{renderSkeleton()}</div>;
};

// AddCSSAnimations
if (typeof document !== 'undefined') {
  const style = document.createElement('style');
  style.textContent = `
    @keyframes slideInRight {
      from {
        transform: translateX(100%);
        opacity: 0;
      }
      to {
        transform: translateX(0);
        opacity: 1;
      }
    }
    
    @keyframes pulse {
      0%, 100% {
        opacity: 1;
      }
      50% {
        opacity: 0.5;
      }
    }
  `;
  document.head.appendChild(style);
}

export default {
  Breadcrumb,
  Pagination,
  Toast,
  Progress,
  Avatar,
  Tooltip,
  EmptyState,
  LoadingSkeleton,
};
