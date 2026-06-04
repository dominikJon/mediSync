<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import axios from 'axios'

const router = useRouter()
const authStore = useAuthStore()
const ladowanie = ref(true)
const blad = ref('')
const dane = ref<any>(null)

const pobierzDane = async () => {
  try {
    const res = await axios.get('/api/lekarz/pulpit')
    dane.value = res.data
  } catch {
    blad.value = 'Błąd podczas pobierania danych pulpitu.'
  } finally {
    ladowanie.value = false
  }
}

const formatGodzina = (iso: string) =>
  new Date(iso).toLocaleTimeString('pl-PL', { hour: '2-digit', minute: '2-digit' })

onMounted(pobierzDane)
</script>

<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1>Dzień dobry, dr {{ authStore.user?.nazwisko }} 👋</h1>
        <p class="podtytul">
          {{ new Date().toLocaleDateString('pl-PL', {
            weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
          }) }}
        </p>
      </div>
    </div>

    <div v-if="ladowanie" class="loading">Ładowanie...</div>
    <div v-else-if="blad" class="error-box">{{ blad }}</div>

    <template v-else-if="dane">

      <!-- Wizyty na dziś -->
      <div class="card">
        <div class="card-title">
          Wizyty na dziś
          <span class="badge-liczba">{{ dane.wizyty_dzis.length }}</span>
        </div>

        <div v-if="dane.wizyty_dzis.length === 0" class="brak-wizyt">
          <span>☕</span>
          <p>Brak zaplanowanych wizyt na dziś.</p>
        </div>

        <div v-else class="wizyty-lista">
          <div
            v-for="w in dane.wizyty_dzis"
            :key="w.id"
            class="wizyta-row"
            @click="router.push('/lekarz/wizyty')"
          >
            <div class="wizyta-godzina-blok">
              <span class="godzina-od">{{ formatGodzina(w.termin_od) }}</span>
              <span class="godzina-do">{{ formatGodzina(w.termin_do) }}</span>
            </div>
            <div class="wizyta-info">
              <span class="pacjent-nazwa">{{ w.pacjent }}</span>
              <span class="gabinet-info">Gabinet {{ w.gabinet }}</span>
            </div>
            <span class="arrow">→</span>
          </div>
        </div>

        <button @click="router.push('/lekarz/wizyty')" class="btn-link">
          Przejdź do moich wizyt →
        </button>
      </div>

      <!-- Statystyki tygodnia -->
      <div class="stats-grid">
        <div class="stat-kafelek niebieski">
          <span class="stat-liczba">{{ dane.statystyki.tydzien.zaplanowane }}</span>
          <span class="stat-opis">Zaplanowane<br>w tym tygodniu</span>
        </div>
        <div class="stat-kafelek zielony">
          <span class="stat-liczba">{{ dane.statystyki.tydzien.zakonczone }}</span>
          <span class="stat-opis">Zakończone<br>w tym tygodniu</span>
        </div>
        <div class="stat-kafelek czerwony">
          <span class="stat-liczba">{{ dane.statystyki.tydzien.odwolane }}</span>
          <span class="stat-opis">Odwołane<br>w tym tygodniu</span>
        </div>
      </div>

      <!-- Statystyki całkowite -->
      <div class="card">
        <div class="card-title">Statystyki całkowite</div>
        <div class="total-grid">
          <div class="total-pozycja">
            <span class="total-liczba">{{ dane.statystyki.total.zakonczone }}</span>
            <span class="total-opis">Wszystkich przeprowadzonych wizyt</span>
          </div>
          <div class="total-pozycja">
            <span class="total-liczba">{{ dane.statystyki.total.unikalni_pacjenci }}</span>
            <span class="total-opis">Unikalnych pacjentów</span>
          </div>
          <div v-if="dane.statystyki.total.top_icd" class="total-pozycja full">
            <span class="total-liczba">{{ dane.statystyki.total.top_icd.kod }}</span>
            <span class="total-opis">
              Najczęstsze rozpoznanie — {{ dane.statystyki.total.top_icd.nazwa }}
              ({{ dane.statystyki.total.top_icd.liczba }}x)
            </span>
          </div>
        </div>
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
.error-box { background: #fee2e2; color: #dc2626; padding: 12px 16px; border-radius: 8px; margin-bottom: 16px; }

.card {
  background: white; border-radius: 12px;
  padding: 24px; box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  margin-bottom: 16px;
}

.card-title {
  display: flex; align-items: center; gap: 10px;
  font-size: 13px; font-weight: 700; color: #64748b;
  text-transform: uppercase; letter-spacing: 0.05em;
  padding-bottom: 16px; border-bottom: 1px solid #e2e8f0; margin-bottom: 16px;
}

.badge-liczba {
  background: #dbeafe; color: #1e40af;
  border-radius: 20px; padding: 2px 10px;
  font-size: 13px; font-weight: 700;
}

.brak-wizyt {
  text-align: center; padding: 24px;
  color: #94a3b8; font-size: 14px;
}
.brak-wizyt span { font-size: 32px; display: block; margin-bottom: 8px; }

.wizyty-lista { display: flex; flex-direction: column; gap: 8px; margin-bottom: 16px; }

.wizyta-row {
  display: flex; align-items: center; gap: 16px;
  padding: 12px 16px; border-radius: 8px;
  background: #f8fafc; cursor: pointer; transition: 0.15s;
}
.wizyta-row:hover { background: #eff6ff; }

.wizyta-godzina-blok {
  display: flex; flex-direction: column;
  min-width: 60px; text-align: center;
}
.godzina-od { font-size: 15px; font-weight: 800; color: #3b82f6; }
.godzina-do { font-size: 11px; color: #94a3b8; }

.wizyta-info { display: flex; flex-direction: column; flex: 1; }
.pacjent-nazwa { font-size: 14px; font-weight: 600; color: #1e293b; }
.gabinet-info { font-size: 12px; color: #64748b; margin-top: 2px; }

.arrow { color: #cbd5e1; font-size: 16px; }

.btn-link {
  background: none; border: none; color: #3b82f6;
  font-weight: 600; font-size: 13px; cursor: pointer;
  padding: 8px 0 0 0; display: block;
}
.btn-link:hover { color: #2563eb; }

.stats-grid {
  display: grid; grid-template-columns: repeat(3, 1fr);
  gap: 12px; margin-bottom: 16px;
}

.stat-kafelek {
  border-radius: 12px; padding: 20px;
  display: flex; flex-direction: column; gap: 8px;
}
.stat-kafelek.niebieski { background: #dbeafe; }
.stat-kafelek.zielony   { background: #dcfce7; }
.stat-kafelek.czerwony  { background: #fee2e2; }

.stat-liczba {
  font-size: 32px; font-weight: 800; color: #1e293b; line-height: 1;
}
.stat-opis { font-size: 12px; font-weight: 600; color: #475569; line-height: 1.4; }

.total-grid {
  display: grid; grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.total-pozycja { display: flex; flex-direction: column; gap: 4px; }
.total-pozycja.full { grid-column: span 2; }
.total-liczba { font-size: 28px; font-weight: 800; color: #1e293b; }
.total-opis { font-size: 13px; color: #64748b; }
</style>