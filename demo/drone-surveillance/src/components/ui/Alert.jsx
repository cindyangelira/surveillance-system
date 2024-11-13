import React from 'react';

export const Alert = ({ children, className = '', variant = 'default', ...props }) => (
  <div
    className={`rounded-lg border p-4 ${
      variant === 'destructive' ? 'border-red-200 bg-red-50' : 'border-slate-200 bg-slate-50'
    } ${className}`}
    {...props}
  >
    {children}
  </div>
);

export const AlertTitle = ({ children, className = '', ...props }) => (
  <h5
    className={`mb-1 font-medium leading-none tracking-tight ${className}`}
    {...props}
  >
    {children}
  </h5>
);

export const AlertDescription = ({ children, className = '', ...props }) => (
  <div
    className={`text-sm text-slate-600 ${className}`}
    {...props}
  >
    {children}
  </div>
);