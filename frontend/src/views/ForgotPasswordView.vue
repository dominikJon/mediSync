<script setup lang="ts">
import { ref } from 'vue'
import axios from 'axios'

const email = ref('')
const blad = ref('')
const sukces = ref(false)
const ladowanie = ref(false)

const handleSubmit = async () => {
  blad.value = ''
  if (!email.value) {
    blad.value = 'Podaj adres email'
    return
  }

  ladowanie.value = true
  try {
    await axios.post('/api/forgot-password', { email: email.value })
    sukces.value = true
  } catch {
    blad.value = 'Wystąpił błąd serwera. Spróbuj ponownie.'
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
    <h3 class="auth-title">Resetuj hasło</h3>

    <div v-if="sukces" class="sukces-box">
      Jeśli podany adres email istnieje w systemie, wysłaliśmy link do resetowania hasła.
      Sprawdź swoją skrzynkę.
    </div>

    <template v-else>
      <p class="opis">Podaj adres email przypisany do konta. Wyślemy Ci link do resetowania hasła.</p>

      <div v-if="blad" class="error-box">{{ blad }}</div>

      <div class="form-group">
        <label>Email</label>
        <input v-model="email" type="email" placeholder="jan.kowalski@email.pl" />
      </div>

      <button @click="handleSubmit" class="btn-primary" :disabled="ladowanie">
        {{ ladowanie ? 'Wysyłanie...' : 'Wyślij link resetujący' }}
      </button>
    </template>

    <p class="auth-footer">
      <RouterLink to="/login">← Wróć do logowania</RouterLink>
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
.auth-title { margin-bottom: 12px; color: #1e293b; }
.opis { color: #64748b; font-size: 14px; margin-bottom: 24px; }
.error-box {
  background: #fee2e2; color: #dc2626;
  border-radius: 8px; padding: 10px 14px;
  margin-bottom: 16px; font-size: 14px; text-align: left;
}
.sukces-box {
  background: #dcfce7; color: #166534;
  border-radius: 8px; padding: 16px;
  margin-bottom: 16px; font-size: 14px; line-height: 1.6;
}
.form-group { text-align: left; margin-bottom: 20px; }
.form-group label {
  display: block; font-size: 13px;
  color: #64748b; margin-bottom: 6px; font-weight: 600;
}
.form-group input {
  width: 100%; padding: 12px;
  border: 1px solid #e2e8f0; border-radius: 8px;
  box-sizing: border-box; font-size: 15px;
}
.form-group input:focus { outline: none; border-color: #3b82f6; }
.btn-primary {
  width: 100%; padding: 12px;
  background-color: #3b82f6; color: white;
  border: none; border-radius: 8px;
  font-weight: 600; font-size: 16px;
  cursor: pointer; transition: 0.2s;
}
.btn-primary:hover:not(:disabled) { background-color: #2563eb; }
.btn-primary:disabled { background-color: #93c5fd; cursor: not-allowed; }
.auth-footer { margin-top: 24px; font-size: 14px; }
.auth-footer a { color: #3b82f6; text-decoration: none; font-weight: 600; }
</style>