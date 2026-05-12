<script setup lang="ts">
import { ref } from 'vue'

const username = ref('')
const password = ref('')
const confirmPassword = ref('')

const handleRegister = () => {
  if(password.value !== confirmPassword.value) {
    alert("Hasła się nie zgadzają!")
    return
  }
  console.log('Rejestracja:', username.value)
  // Tutaj bedzie axios do backendu
}
</script>

<template>
  <div class="auth-card">
    <div class="logo">
      <h2><span class="text-blue">Medi</span><span class="text-green">Sync</span></h2>
    </div>
    <h3 class="auth-title">Utwórz konto</h3>
    
    <div class="form-group">
      <label>Login lub Email</label>
      <input v-model="username" type="text" placeholder="Wpisz login" />
    </div>
    
    <div class="form-group">
      <label>Hasło</label>
      <input v-model="password" type="password" placeholder="Wpisz hasło" />
    </div>

    <div class="form-group">
      <label>Powtórz hasło</label>
      <input v-model="confirmPassword" type="password" placeholder="Powtórz hasło" />
    </div>
    
    <button @click="handleRegister" class="btn-primary">Zarejestruj się</button>
    
    <p class="auth-footer">
      Masz już konto? <RouterLink to="/login">Zaloguj się</RouterLink>
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

.logo h2 {
  margin: 0 0 24px 0;
  font-size: 28px;
}

.text-blue {
  color: #0056b3;
  font-weight: bold;
}

.text-green {
  color: #28a745;
  font-weight: bold;
}

.auth-title {
  margin-bottom: 24px;
  color: #1e293b;
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
}

.form-group input:focus {
  outline: none;
  border-color: #3b82f6;
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

.btn-primary:hover {
  background-color: #2563eb;
}

.auth-footer {
  margin-top: 24px;
  font-size: 14px;
  color: #64748b;
}

.auth-footer a {
  color: #3b82f6;
  text-decoration: none;
  font-weight: 600;
}

</style>