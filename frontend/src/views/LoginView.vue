<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const email = ref('')
const password = ref('')
const blad = ref('')
const ladowanie = ref(false)
const bledy = ref<{ email?: string; haslo?: string }>({})

const waliduj = () => {
  bledy.value = {}
  if (!email.value) {
    bledy.value.email = 'Podaj adres email'
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value)) {
    bledy.value.email = 'Podaj poprawny adres email'
  }
  if (!password.value) {
    bledy.value.haslo = 'Podaj hasło'
  }
  return Object.keys(bledy.value).length === 0
}

const handleLogin = async () => {
  blad.value = ''
  if (!waliduj()) return

  ladowanie.value = true

  try {
    const success = await authStore.login(email.value, password.value)
    if (success) {
      router.push('/')
    } else {
      blad.value = 'Nieprawidłowy email lub hasło.'
    }
  } finally {
    ladowanie.value = false
  }
}
</script>

<template>
  <div class="auth-card">
    <div class="logo">
      <h2><span class="text-blue">Medi</span><span class="text-green">Sync</span></h2>
    </div>
    <h3 class="auth-title">Zaloguj się</h3>

    <div v-if="blad" class="error-box">{{ blad }}</div>

    <div class="form-group">
      <label>Email</label>
      <input
        v-model="email"
        type="email"
        placeholder="jan.kowalski@email.pl"
        :class="{ 'input-error': bledy.email }"
      />
      <span v-if="bledy.email" class="field-error">{{ bledy.email }}</span>
    </div>

    <div class="form-group">
      <label>Hasło</label>
      <input
        v-model="password"
        type="password"
        placeholder="Wpisz hasło"
        :class="{ 'input-error': bledy.haslo }"
        @keyup.enter="handleLogin"
      />
      <span v-if="bledy.haslo" class="field-error">{{ bledy.haslo }}</span>
    </div>

    <button @click="handleLogin" class="btn-primary" :disabled="ladowanie">
      {{ ladowanie ? 'Logowanie...' : 'Zaloguj się' }}
    </button>

    <p class="auth-footer">
      Nie masz konta? <RouterLink to="/register">Zarejestruj się</RouterLink>
    </p>
  </div>
</template>

<style scoped>
.auth-card {
  background: white;
  padding: 40px;
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.05);
  width: 100%;
  max-width: 400px;
  text-align: center;
}

.logo h2 { margin: 0 0 24px 0; font-size: 28px; }
.text-blue { color: #0056b3; font-weight: bold; }
.text-green { color: #28a745; font-weight: bold; }

.auth-title { margin-bottom: 24px; color: #1e293b; }

.error-box {
  background: #fee2e2;
  color: #dc2626;
  border-radius: 8px;
  padding: 10px 14px;
  margin-bottom: 16px;
  font-size: 14px;
  text-align: left;
}

.form-group {
  text-align: left;
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  font-size: 13px;
  color: #64748b;
  margin-bottom: 6px;
  font-weight: 600;
}

.form-group input {
  width: 100%;
  padding: 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  box-sizing: border-box;
  font-size: 15px;
  transition: border-color 0.2s;
}

.form-group input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.input-error { border-color: #ef4444 !important; }

.field-error {
  display: block;
  color: #ef4444;
  font-size: 12px;
  margin-top: 4px;
}

.btn-primary {
  width: 100%;
  padding: 12px;
  background-color: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 16px;
  cursor: pointer;
  transition: 0.2s;
  margin-top: 10px;
}

.btn-primary:hover { background-color: #2563eb; }

.auth-footer { margin-top: 24px; font-size: 14px; color: #64748b; }
.auth-footer a { color: #3b82f6; text-decoration: none; font-weight: 600; }
</style>