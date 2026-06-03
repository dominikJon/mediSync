<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import axios from 'axios'

const router = useRouter()
const authStore = useAuthStore()
const ladowanie = ref(true)
const blad = ref('')
const dane = ref<any>(null)

const pobierzDane = async () => {
  if (authStore.user?.rola !== 'pacjent') {
    ladowanie.value = false
    return
  }
  try {
    const res = await axios.get('/api/pacjent/profil')
    dane.value = res.data
  } catch {
    blad.value = 'Błąd podczas pobierania danych.'
  } finally {
    ladowanie.value = false
  }
}

const formatData = (iso: string) => {
  const d = new Date(iso)
  return d.toLocaleDateString('pl-PL', {
    weekday: 'long', year: 'numeric',
    month: 'long', day: 'numeric',
  })
}

const formatGodzina = (iso: string) => {
  return new Date(iso).toLocaleTimeString('pl-PL', {
    hour: '2-digit', minute: '2-digit'
  })
}

onMounted(pobierzDane)
</script>

<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1>Dzień dobry, {{ authStore.user?.rola === 'pacjent' ? dane?.pacjent?.imie : authStore.user?.email }} 👋</h1>
        <p class="podtytul">{{ new Date().toLocaleDateString('pl-PL', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }) }}</p>
      </div>
    </div>

    <div v-if="ladowanie" class="loading">Ładowanie...</div>
    <div v-else-if="blad" class="error-box">{{ blad }}</div>

    <template v-else-if="authStore.user?.rola === 'pacjent' && dane">

      <!-- Najbliższa wizyta -->
      <div v-if="dane.najblizsa_wizyta" class="card card-wizyta">
        <div class="card-label">Najbliższa wizyta</div>
        <div class="wizyta-glowna">
          <div class="wizyta-data">
            <span class="wizyta-dzien">{{ formatData(dane.najblizsa_wizyta.termin_od) }}</span>
            <span class="wizyta-godzina">{{ formatGodzina(dane.najblizsa_wizyta.termin_od) }} — {{ formatGodzina(dane.najblizsa_wizyta.termin_do) }}</span>
          </div>
          <div class="wizyta-szczegoly">
            <span class="wizyta-lekarz">Dr {{ dane.najblizsa_wizyta.lekarz }}</span>
            <span class="wizyta-spec">{{ dane.najblizsa_wizyta.specjalizacja }}</span>
            <span class="wizyta-usluga">{{ dane.najblizsa_wizyta.nazwa_uslugi }} · Gabinet {{ dane.najblizsa_wizyta.gabinet }}</span>
          </div>
          <div class="wizyta-cena">{{ dane.najblizsa_wizyta.cena }} zł</div>
        </div>
      </div>

      <div v-else class="card card-brak-wizyty">
        <div class="brak-ikona">📅</div>
        <p>Nie masz zaplanowanych wizyt</p>
        <button @click="router.push('/schedule')" class="btn-primary">
          Zarezerwuj wizytę
        </button>
      </div>

      <!-- Szybkie akcje -->
      <div class="akcje-grid">
        <button @click="router.push('/schedule')" class="akcja-kafelek">
          <span class="akcja-ikona">📅</span>
          <span>Zarezerwuj wizytę</span>
        </button>
        <button @click="router.push('/records')" class="akcja-kafelek">
          <span class="akcja-ikona">📋</span>
          <span>Historia wizyt</span>
        </button>
      </div>

      <!-- Ostatnie wizyty -->
      <div class="card" v-if="dane.ostatnie_wizyty.length > 0">
        <div class="card-title">Ostatnie wizyty</div>
        <div class="wizyty-lista">
          <div v-for="w in dane.ostatnie_wizyty" :key="w.id" class="wizyta-row">
            <div class="wizyta-row-data">
              <span class="data">{{ formatData(w.termin_od) }}</span>
              <span class="godzina">{{ formatGodzina(w.termin_od) }}</span>
            </div>
            <div class="wizyta-row-info">
              <span class="lekarz">Dr {{ w.lekarz }}</span>
              <span class="usluga">{{ w.nazwa_uslugi }}</span>
            </div>
            <span :class="['badge-status', `status-${w.status.toLowerCase()}`]">
              {{ w.status }}
            </span>
          </div>
        </div>
        <button @click="router.push('/records')" class="btn-link">
          Zobacz całą historię →
        </button>
      </div>

    </template>

    <!-- Widok dla innych ról -->
    <template v-else>
      <div class="card">
        <p class="muted">Witaj w systemie MediSync.</p>
      </div>
    </template>
  </div>
</template>

<style scoped>
.page { padding: 32px; max-width: 900px; }

.page-header { margin-bottom: 28px; }
.page-header h1 { font-size: 26px; font-weight: 700; color: #1e293b; margin: 0; }
.podtytul { color: #64748b; margin: 4px 0 0 0; font-size: 14px; }

.loading { color: #64748b; padding: 20px; }
.error-box { background: #fee2e2; color: #dc2626; padding: 12px 16px; border-radius: 8px; }

.card {
  background: white; border-radius: 12px;
  padding: 24px; box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  margin-bottom: 16px;
}

.card-label {
  font-size: 11px; font-weight: 700; color: #64748b;
  text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 16px;
}

.card-title {
  font-size: 13px; font-weight: 700; color: #64748b;
  text-transform: uppercase; letter-spacing: 0.05em;
  padding-bottom: 16px; border-bottom: 1px solid #e2e8f0; margin-bottom: 16px;
}

.card-wizyta { border-left: 4px solid #3b82f6; }

.wizyta-glowna { display: flex; align-items: center; gap: 24px; }

.wizyta-data { display: flex; flex-direction: column; min-width: 200px; }
.wizyta-dzien { font-size: 15px; font-weight: 700; color: #1e293b; }
.wizyta-godzina { font-size: 20px; font-weight: 800; color: #3b82f6; margin-top: 2px; }

.wizyta-szczegoly { display: flex; flex-direction: column; flex: 1; }
.wizyta-lekarz { font-size: 15px; font-weight: 700; color: #1e293b; }
.wizyta-spec { font-size: 13px; color: #3b82f6; font-weight: 600; margin-top: 2px; }
.wizyta-usluga { font-size: 13px; color: #64748b; margin-top: 2px; }

.wizyta-cena { font-size: 20px; font-weight: 800; color: #1e293b; }

.card-brak-wizyty {
  text-align: center; padding: 40px;
  border: 2px dashed #e2e8f0; background: #f8fafc;
  box-shadow: none;
}
.brak-ikona { font-size: 40px; margin-bottom: 12px; }
.card-brak-wizyty p { color: #64748b; margin-bottom: 16px; }

.akcje-grid {
  display: grid; grid-template-columns: 1fr 1fr;
  gap: 12px; margin-bottom: 16px;
}

.akcja-kafelek {
  display: flex; flex-direction: column; align-items: center;
  gap: 8px; padding: 20px; background: white;
  border: 1px solid #e2e8f0; border-radius: 12px;
  cursor: pointer; transition: 0.2s; font-size: 14px;
  font-weight: 600; color: #475569;
}
.akcja-kafelek:hover { border-color: #3b82f6; color: #3b82f6; background: #f0f7ff; }
.akcja-ikona { font-size: 28px; }

.wizyty-lista { display: flex; flex-direction: column; gap: 12px; }

.wizyta-row {
  display: flex; align-items: center; gap: 16px;
  padding: 12px; border-radius: 8px; background: #f8fafc;
}

.wizyta-row-data { display: flex; flex-direction: column; min-width: 160px; }
.data { font-size: 13px; font-weight: 600; color: #1e293b; }
.godzina { font-size: 12px; color: #64748b; }

.wizyta-row-info { display: flex; flex-direction: column; flex: 1; }
.lekarz { font-size: 14px; font-weight: 600; color: #1e293b; }
.usluga { font-size: 12px; color: #64748b; }

.badge-status {
  padding: 4px 10px; border-radius: 20px;
  font-size: 12px; font-weight: 600;
}
.status-zakończona { background: #dcfce7; color: #166534; }
.status-zaplanowana { background: #dbeafe; color: #1e40af; }
.status-odwołana { background: #fee2e2; color: #dc2626; }

.btn-link {
  background: none; border: none; color: #3b82f6;
  font-weight: 600; font-size: 13px; cursor: pointer;
  padding: 12px 0 0 0; display: block;
}
.btn-link:hover { color: #2563eb; }

.btn-primary {
  padding: 10px 20px; background: #3b82f6; color: white;
  border: none; border-radius: 8px; font-weight: 600;
  font-size: 14px; cursor: pointer; transition: 0.2s;
}
.btn-primary:hover { background: #2563eb; }

.muted { color: #64748b; }
</style>