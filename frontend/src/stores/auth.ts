import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export const useAuthStore = defineStore('auth', () => {
  // stan (zmienne)
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<string | null>(null)

  // Gettery czy zalogowany
  const isAuthenticated = computed(() => token.value !== null)

  // Akcje
  const login = async (usernameInput: string, passwordInput: string) => {
    try {
      const response = await axios.post('http://localhost:8000/api/login', {
        username: usernameInput,
        password: passwordInput
      })
      
      token.value = response.data.access_token
      user.value = response.data.user
      
      localStorage.setItem('token', token.value as string)
      axios.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
      
      return true
    } catch (error) {
      console.error("Błąd logowania:", error)
      return false
    }
  }

  const logout = () => {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    delete axios.defaults.headers.common['Authorization']
  }

  return { token, user, isAuthenticated, login, logout }
})