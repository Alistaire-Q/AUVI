import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import Processing from './pages/Processing';
import Dashboard from './pages/Dashboard';
import Projects from './pages/Projects';
import Integrations from './pages/Integrations';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/processing/:jobId" element={<Processing />} />
        <Route path="/dashboard/:jobId" element={<Dashboard />} />
        <Route path="/dashboard" element={<Projects />} />
        <Route path="/projects" element={<Projects />} />
        <Route path="/integrations" element={<Integrations />} />
        <Route path="*" element={<Home />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
