import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import Processing from './pages/Processing';
import Dashboard from './pages/Dashboard';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/processing/:jobId" element={<Processing />} />
        <Route path="/dashboard/:jobId" element={<Dashboard />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
