import { create } from 'zustand'

// Access token disimpan di MEMORY (state) — sengaja TIDAK persist ke
// localStorage supaya aman dari XSS. Session di-restore via refresh cookie.
export const useAuthStore = create((set) => ({
  user: null,
  accessToken: null,
  initialized: false,
  setAuth: (user, accessToken) => set({ user, accessToken }),
  setAccessToken: (accessToken) => set({ accessToken }),
  setInitialized: () => set({ initialized: true }),
  clear: () => set({ user: null, accessToken: null }),
}))
