import { Configuration, LogLevel } from '@azure/msal-browser';

// Entra ID settings from environment variables (set via Vite)
const clientId = import.meta.env.VITE_AZURE_CLIENT_ID || '';
const tenantId = import.meta.env.VITE_AZURE_TENANT_ID || '';

export const msalConfig: Configuration = {
  auth: {
    clientId,
    authority: tenantId ? `https://login.microsoftonline.com/${tenantId}` : undefined,
    redirectUri: window.location.origin,
    postLogoutRedirectUri: window.location.origin,
  },
  cache: {
    cacheLocation: 'localStorage',
    storeAuthStateInCookie: false,
  },
  system: {
    loggerOptions: {
      logLevel: LogLevel.Warning,
    },
  },
};

export const loginRequest = {
  scopes: clientId ? [`api://${clientId}/access`] : [],
};

// Auth is enabled only when clientId is configured
export const isAuthEnabled = !!clientId;
