import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { ReactKeycloakProvider } from "@react-keycloak/web";
import Keycloak from "keycloak-js";
import App from "./App.jsx";

const kc = new Keycloak({
  url: import.meta.env.VITE_KEYCLOAK_URL || "http://127.0.0.1:8090",
  realm: import.meta.env.VITE_KEYCLOAK_REALM || "castuo-system",
  clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID || "ctaex-hydro-dashboard",
});

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <ReactKeycloakProvider
      authClient={kc}
      initOptions={{ onLoad: "login-required", pkceMethod: "S256" }}
    >
      <BrowserRouter>
        <Routes>
          <Route path="/hidroponic/:zoneId" element={<App />} />
          <Route path="*" element={<Navigate to="/hidroponic/zone_cannabis_1" replace />} />
        </Routes>
      </BrowserRouter>
    </ReactKeycloakProvider>
  </React.StrictMode>
);
