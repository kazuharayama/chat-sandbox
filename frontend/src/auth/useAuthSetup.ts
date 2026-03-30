import { useEffect } from 'react';
import { useMsal } from '@azure/msal-react';
import { apiService } from '../services/api';
import { loginRequest, isAuthEnabled } from './msalConfig';

/**
 * Hook to wire MSAL token acquisition into apiService.
 * Call this once in a component inside MsalProvider.
 */
export function useAuthSetup() {
  const { instance, accounts } = useMsal();

  useEffect(() => {
    if (!isAuthEnabled || accounts.length === 0) return;

    apiService.setTokenProvider(async () => {
      try {
        const result = await instance.acquireTokenSilent({
          ...loginRequest,
          account: accounts[0],
        });
        return result.accessToken;
      } catch {
        // Silent token acquisition failed, trigger redirect
        instance.acquireTokenRedirect(loginRequest);
        return null;
      }
    });
  }, [instance, accounts]);
}
