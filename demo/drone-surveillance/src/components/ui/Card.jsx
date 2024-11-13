import React from 'react';

export const Card = ({ children, className = '', ...props }) => (
  <div
    className={`rounded-lg border border-slate-200 bg-white shadow-sm ${className}`}
    {...props}
  >
    {children}
  </div>
);

export const CardHeader = ({ children, className = '', ...props }) => (
  <div
    className={`flex flex-col space-y-1.5 p-6 ${className}`}
    {...props}
  >
    {children}
  </div>
);

export const CardTitle = ({ children, className = '', ...props }) => (
  <h3
    className={`text-2xl font-semibold leading-none tracking-tight ${className}`}
    {...props}
  >
    {children}
  </h3>
);

export const CardContent = ({ children, className = '', ...props }) => (
  <div
    className={`p-6 pt-0 ${className}`}
    {...props}
  >
    {children}
  </div>
);