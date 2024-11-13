import React from 'react';
import MapDashboard from './components/MapDashboard';

const App = () => {
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      <header className="border-b bg-white dark:bg-slate-800 px-4 py-3">
        <h1 className="text-xl font-bold text-slate-900 dark:text-white">
          Drone Surveillance System
        </h1>
      </header>
      <main className="container mx-auto">
        <MapDashboard />
      </main>
    </div>
  );
};

export default App;