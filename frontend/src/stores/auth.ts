import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'
 
// ── Typy ──────────────────────────────────────────────────────────────────────
interface Uzytkownik {
  id: number
  email: string
  rola: string
}
 
// ── Store ─────────────────────────────────────────────────────────────────────
export const useAuthStore = defineStore('auth', () => {
  // Stan
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<Uzytkownik | null>(null)
 
  // Przy starcie aplikacji — przywróć nagłówek jeśli token już istnieje w localStorage
  if (token.value) {
    axios.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
  }
 
  // Gettery
  const isAuthenticated = computed(() => token.value !== null)
 
  // Akcje
  const login = async (emailInput: string, hasloInput: string): Promise<boolean> => {
    try {
      const response = await axios.post('/api/login', {
        // Nazwy pól zgodne z backendem (LoginRequest w FastAPI)
        email: emailInput,
        haslo: hasloInput,
      })
 
      token.value = response.data.access_token
      user.value = response.data.uzytkownik
 
      localStorage.setItem('token', token.value as string)
      axios.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
 
      return true
    } catch (error) {
      console.error('Błąd logowania:', error)
      return false
    }
  }
 
  const logout = (): void => {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    delete axios.defaults.headers.common['Authorization']
  }
 
  return { token, user, isAuthenticated, login, logout }
})
 