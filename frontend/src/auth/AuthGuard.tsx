import { useMsal, AuthenticatedTemplate, UnauthenticatedTemplate } from '@azure/msal-react';
import { loginRequest, isAuthEnabled } from './msalConfig';
import { LogIn } from 'lucide-react';

interface AuthGuardProps {
  children: React.ReactNode;
}

export default function AuthGuard({ children }: AuthGuardProps) {
  // If auth is not configured, render children directly
  if (!isAuthEnabled) {
    return <>{children}</>;
  }

  return (
    <>
      <AuthenticatedTemplate>
        {children}
      </AuthenticatedTemplate>
      <UnauthenticatedTemplate>
        <LoginScreen />
      </UnauthenticatedTemplate>
    </>
  );
}

function LoginScreen() {
  const { instance } = useMsal();

  const handleLogin = () => {
    instance.loginRedirect(loginRequest);
  };

  return (
    <div className="flex items-center justify-center h-screen bg-gray-50">
      <div className="text-center">
        <h1 className="text-2xl font-semibold text-gray-900 mb-2">Chat AI</h1>
        <p className="text-sm text-gray-500 mb-6">ログインが必要です</p>
        <button
          onClick={handleLogin}
          className="flex items-center gap-2 mx-auto px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors text-sm font-medium"
        >
          <LogIn className="w-4 h-4" />
          Microsoft でログイン
        </button>
      </div>
    </div>
  );
}
