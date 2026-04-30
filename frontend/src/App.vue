<script setup lang="ts">
import { ref } from 'vue'
import axios from 'axios'

const apiMessage = ref('Brak połączenia z backendem...')

const testConnection = async () => {
  try {
    const response = await axios.get('http://localhost:8000/api/health')
    apiMessage.value = response.data.message
  } catch (error) {
    apiMessage.value = 'Błąd połączenia! Serwer wyłączony albo zły port.'
    console.error(error)
  }
}
</script>

<template>
  <main style="text-align: center; margin-top: 100px; font-family: sans-serif;">
    <h1>Test Połączenia MediSync</h1>
  
    
    <h2 style="margin-top: 30px; color: #333;">
      Odpowiedź: <span style="color: #007BFF;">{{ apiMessage }}</span>
    </h2>
  </main>
</template>