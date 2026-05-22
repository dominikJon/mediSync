<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const route = useRoute()

const token = ref('')
const noweHaslo = ref('')
const powtorzHaslo = ref('')
const blad = ref('')
const sukces = ref(false)
const ladowanie = ref(false)
const bledy = ref<{ haslo?: string; potwierdzenie?: string }>({})

// Siła hasła
const silaHasla = computed(() => {
  const h = noweHaslo.value
  if (!h) return null
  let punkty = 0
  if (h.length >= 12) punkty++
  if (/[A-Z]/.test(h)) punkty++
  if (/[a-z]/.test(h)) punkty++
  if (/\d/.test(h)) punkty++
  if (/[!@#$%^&*(),.?":{}|<>_\-]/.test(h)) punkty++
  if (punkty <= 2) return { poziom: 'słabe', kolor: '#ef4444' }
  if (punkty <= 3) return { poziom: 'średnie', kolor: '#f59e0b' }
  return { poziom: 'silne', kolor: '#22c55e' }
})

onMounted(() => {
  token.value = route.query.token as string
  if (!token.value) {
    blad.value = 'Nieprawidłowy link resetowania hasła.'
  }
})

const waliduj = () => {
  bledy.value = {}

  if (!noweHaslo.value) {
    bledy.value.haslo = 'Podaj nowe hasło'
  } else if (noweHaslo.value.length < 12) {
    bledy.value.haslo = 'Hasło musi mieć co najmniej 12 znaków'
  } else if (!/[A-Z]/.test(noweHaslo.value)) {
    bledy.value.haslo = 'Hasło musi zawierać co najmniej jedną wielką literę'
  } else if (!/[a-z]/.test(noweHaslo.value)) {
    bledy.value.haslo = 'Hasło musi zawierać co najmniej jedną małą literę'
  } else if (!/\d/.test(noweHaslo.value)) {
    bledy.value.haslo = 'Hasło musi zawierać co najmniej jedną cyfrę'
  } else if (!/[!@#$%^&*(),.?":{}|<>_\-]/.test(noweHaslo.value)) {
    bledy.value.haslo = 'Hasło musi zawierać co najmniej jeden znak specjalny'
  }

  if (!powtorzHaslo.value) {
    bledy.value.potwierdzenie = 'Powtórz hasło'
  } else if (noweHaslo.value !== powtorzHaslo.value) {
    bledy.value.potwierdzenie = 'Hasła się nie zgadzają'
  }

  return Object.keys(bledy.value).length === 0
}

const handleSubmit = async () => {
  blad.value = ''
  if (!waliduj()) return

  ladowanie.value = true
  try {
    await axios.post('/api/reset-password', {
      token: token.value,
      nowe_haslo: noweHaslo.value,
    })
    sukces.value = true
    setTimeout(() => router.push('/login'), 3000)
  } catch (error: any) {
    if (error.response?.status === 400) {
      blad.value = 'Link wygasł lub jest nieprawidłowy. Poproś o nowy.'
    } else {
      blad.value = 'Wystąpił błąd serwera. Spróbuj ponownie.'
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
    <h3 class="auth-title">Ustaw nowe hasło</h3>

    <div v-if="sukces" class="sukces-box">
      Hasło zostało zmienione! Za chwilę zostaniesz przekierowany do strony logowania.
    </div>

    <template v-else>
      <div v-if="blad" class="error-box">{{ blad }}</div>

      <div class="form-group">
        <label>Nowe hasło</label>
        <input
          v-model="noweHaslo"
          type="password"
          placeholder="Min. 12 znaków, wielka litera, cyfra, znak specjalny"
          :class="{ 'input-error': bledy.haslo }"
        />
        <div v-if="noweHaslo" class="sila-hasla">
          <div class="sila-pasek" :style="{ backgroundColor: silaHasla?.kolor }"></div>
          <span :style="{ color: silaHasla?.kolor }">Hasło {{ silaHasla?.poziom }}</span>
        </div>
        <span v-if="bledy.haslo" class="field-error">{{ bledy.haslo }}</span>
      </div>

      <div class="form-group">
        <label>Powtórz hasło</label>
        <input
          v-model="powtorzHaslo"
          type="password"
          placeholder="Powtórz nowe hasło"
          :class="{ 'input-error': bledy.potwierdzenie }"
          @keyup.enter="handleSubmit"
        />
        <span v-if="bledy.potwierdzenie" class="field-error">{{ bledy.potwierdzenie }}</span>
      </div>

      <div class="wymagania-hasla">
        <p class="wymagania-tytul">Hasło musi zawierać:</p>
        <ul>
          <li :class="{ spelnione: noweHaslo.length >= 12 }">✓ Minimum 12 znaków</li>
          <li :class="{ spelnione: /[A-Z]/.test(noweHaslo) }">✓ Wielką literę (A-Z)</li>
          <li :class="{ spelnione: /[a-z]/.test(noweHaslo) }">✓ Małą literę (a-z)</li>
          <li :class="{ spelnione: /\d/.test(noweHaslo) }">✓ Cyfrę (0-9)</li>
          <li :class="{ spelnione: /[!@#$%^&*(),.?&quot;:{}|<>_\-]/.test(noweHaslo) }">✓ Znak specjalny (!@#$...)</li>
        </ul>
      </div>

      <button @click="handleSubmit" class="btn-primary" :disabled="ladowanie || !token">
        {{ ladowanie ? 'Zapisywanie...' : 'Ustaw nowe hasło' }}
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

.sukces-box {
  background: #dcfce7;
  color: #166534;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  font-size: 14px;
  line-height: 1.6;
}

.form-group { text-align: left; margin-bottom: 20px; }

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

.sila-hasla {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 6px;
}

.sila-pasek {
  height: 4px;
  width: 60px;
  border-radius: 2px;
  transition: background-color 0.3s;
}

.sila-hasla span { font-size: 12px; font-weight: 600; }

.wymagania-hasla {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 20px;
  text-align: left;
}

.wymagania-tytul {
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  margin: 0 0 8px 0;
}

.wymagania-hasla ul { list-style: none; padding: 0; margin: 0; }

.wymagania-hasla li {
  font-size: 12px;
  color: #94a3b8;
  padding: 2px 0;
  transition: color 0.2s;
}

.wymagania-hasla li.spelnione { color: #22c55e; font-weight: 600; }

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

.btn-primary:hover:not(:disabled) { background-color: #2563eb; }
.btn-primary:disabled { background-color: #93c5fd; cursor: not-allowed; }

.auth-footer { margin-top: 24px; font-size: 14px; color: #64748b; }
.auth-footer a { color: #3b82f6; text-decoration: none; font-weight: 600; }
</style>