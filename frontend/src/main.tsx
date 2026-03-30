import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { PublicClientApplication } from '@azure/msal-browser'
import { MsalProvider } from '@azure/msal-react'
import { msalConfig, isAuthEnabled } from './auth/msalConfig'
import './index.css'
import App from './App.tsx'

const msalInstance = isAuthEnabled ? new PublicClientApplication(msalConfig) : null;

function Root() {
  const app = (
    <BrowserRouter>
      <App />
    </BrowserRouter>
  );

  if (msalInstance) {
    return (
      <MsalProvider instance={msalInstance}>
        {app}
      </MsalProvider>
    );
  }

  return app;
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Root />
  </StrictMode>,
)
