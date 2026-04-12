import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { getAuthToken, setAuthToken, clearAuthToken } from '../lib/api';

interface AuthState {
  token: string | null;
  isAuthenticated: boolean;

  login: (token: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: getAuthToken(),
      isAuthenticated: !!getAuthToken(),

      login: (token) => {
        setAuthToken(token);
        set({ token, isAuthenticated: true });
      },

      logout: () => {
        clearAuthToken();
        set({ token: null, isAuthenticated: false });
      },
    }),
    {
      name: 'mc_auth',
    },
  ),
);

// Listen for 401 events from the API client
window.addEventListener('mc:unauthorized', () => {
  useAuthStore.getState().logout();
});
