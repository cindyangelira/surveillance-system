import React from 'react';

export const Badge = ({ children, className = '', variant = 'default', ...props }) => {
  const baseStyles = 'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold';
  const variantStyles = {
    default: 'bg-slate-900 text-white',
    secondary: 'bg-slate-100 text-slate-900',
    destructive: 'bg-red-500 text-white',
  };

  return (
    <span
      className={`${baseStyles} ${variantStyles[variant]} ${className}`}
      {...props}
    >
      {children}
    </span>
  );
};