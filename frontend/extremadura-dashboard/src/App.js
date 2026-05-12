import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Dashboard from "./components/Dashboard";
import PrivacyModule from "./components/PrivacyModule";
import BillingDashboard from "./components/BillingDashboard";
import "./App.css";

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/privacidad" element={<PrivacyModule />} />
          <Route path="/facturacion" element={<BillingDashboard />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
