<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const ladowanie = ref(true)
const blad = ref('')
const dane = ref<any>(null)

const pobierzDane = async () => {
  try {
    const res = await axios.get('/api/reception/pulpit')
    dane.value = res.data
  } catch {
    blad.value = 'Błąd podczas pobierania danych.'
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
      <h1>Dzień dobry 👋</h1>
      <p class="podtytul">
        {{ new Date().toLocaleDateString('pl-PL', {
          weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
        }) }}
      </p>
    </div>

    <div v-if="ladowanie" class="loading">Ładowanie...</div>
    <div v-else-if="blad" class="error-box">{{ blad }}</div>

    <template v-else-if="dane">

      <!-- Statystyki dnia -->
      <div class="stats-grid">
        <div class="stat-kafelek niebieski">
          <span class="stat-liczba">{{ dane.wizyty_dzis.zaplanowane }}</span>
          <span class="stat-opis">Zaplanowanych dziś</span>
        </div>
        <div class="stat-kafelek zielony">
          <span class="stat-liczba">{{ dane.wizyty_dzis.zakonczone }}</span>
          <span class="stat-opis">Zakończonych dziś</span>
        </div>
        <div class="stat-kafelek czerwony">
          <span class="stat-liczba">{{ dane.wizyty_dzis.odwolane }}</span>
          <span class="stat-opis">Odwołanych dziś</span>
        </div>
        <div class="stat-kafelek szary">
          <span class="stat-liczba">{{ dane.wolne_sloty_dzis }}</span>
          <span class="stat-opis">Wolnych slotów dziś</span>
        </div>
      </div>

      <!-- Szybkie akcje -->
      <div class="card">
        <div class="card-title">Szybkie akcje</div>
        <div class="akcje-grid">
          <button @click="router.push('/schedule')" class="akcja-btn">
            <span class="akcja-ikona">📅</span>
            <span>Zarezerwuj wizytę</span>
          </button>
          <button @click="router.push('/reception/graphic')" class="akcja-btn">
            <span class="akcja-ikona">🗓️</span>
            <span>Grafik pracy</span>
          </button>
          <button @click="router.push('/reception/office')" class="akcja-btn">
            <span class="akcja-ikona">🏥</span>
            <span>Gabinety</span>
          </button>
        </div>
      </div>

      <!-- Wizyty na dziś -->
      <div class="card">
        <div class="card-title">
          Najbliższe wizyty na dziś
          <span class="badge-liczba">{{ dane.lista_dzis.length }}</span>
        </div>

        <div v-if="dane.lista_dzis.length === 0" class="brak">
          <span>☕</span>
          <p>Brak zaplanowanych wizyt na dziś.</p>
        </div>

        <div v-else class="wizyty-lista">
          <div v-for="w in dane.lista_dzis" :key="w.id" class="wizyta-row">
            <div class="wizyta-godzina-blok">
              <span class="godzina-od">{{ formatGodzina(w.termin_od) }}</span>
              <span class="godzina-do">{{ formatGodzina(w.termin_do) }}</span>
            </div>
            <div class="wizyta-info">
              <span class="pacjent">{{ w.pacjent }}</span>
              <span class="lekarz">{{ w.lekarz }} · Gabinet {{ w.gabinet }}</span>
            </div>
          </div>
        </div>

        <button @click="router.push('/reception/graphic')" class="btn-link">
          Zobacz pełny grafik →
        </button>
      </div>

      <!-- Lekarze dziś -->
      <div class="card" v-if="dane.lekarze_dzis.length > 0">
        <div class="card-title">Lekarze pracujący dziś</div>
        <div class="lekarze-lista">
          <div v-for="l in dane.lekarze_dzis" :key="l.lekarz" class="lekarz-row">
            <div class="lekarz-info">
              <span class="lekarz-nazwa">{{ l.lekarz }}</span>
              <span class="lekarz-gabinety">Gabinet {{ l.gabinety.join(', ') }}</span>
            </div>
            <div class="lekarz-sloty">
              <span class="slot-zajety">{{ l.zajete_sloty }} zajętych</span>
              <span class="slot-separator">/</span>
              <span class="slot-wolny">{{ l.wolne_sloty }} wolnych</span>
            </div>
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

.stats-grid {
  display: grid; grid-template-columns: repeat(4, 1fr);
  gap: 12px; margin-bottom: 16px;
}

.stat-kafelek {
  border-radius: 12px; padding: 20px;
  display: flex; flex-direction: column; gap: 6px;
}
.stat-kafelek.niebieski { background: #dbeafe; }
.stat-kafelek.zielony   { background: #dcfce7; }
.stat-kafelek.czerwony  { background: #fee2e2; }
.stat-kafelek.szary     { background: #f1f5f9; }

.stat-liczba { font-size: 32px; font-weight: 800; color: #1e293b; line-height: 1; }
.stat-opis   { font-size: 12px; font-weight: 600; color: #475569; }

.card {
  background: white; border-radius: 12px;
  padding: 24px; box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  margin-bottom: 16px;
}

.card-title {
  display: flex; align-items: center; gap: 10px;
  font-size: 13px; font-weight: 700; color: #64748b;
  text-transform: uppercase; letter-spacing: 0.05em;
  padding-bottom: 16px; border-bottom: 1px solid #e2e8f0;
  margin-bottom: 16px;
}

.badge-liczba {
  background: #dbeafe; color: #1e40af;
  border-radius: 20px; padding: 2px 10px;
  font-size: 13px; font-weight: 700;
}

.akcje-grid {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px;
}

.akcja-btn {
  display: flex; flex-direction: column; align-items: center;
  gap: 8px; padding: 16px; background: #f8fafc;
  border: 1px solid #e2e8f0; border-radius: 8px;
  cursor: pointer; transition: 0.15s;
  font-size: 13px; font-weight: 600; color: #475569;
}
.akcja-btn:hover { background: #eff6ff; border-color: #3b82f6; color: #3b82f6; }
.akcja-ikona { font-size: 24px; }

.brak {
  text-align: center; padding: 24px;
  color: #94a3b8; font-size: 14px;
}
.brak span { font-size: 32px; display: block; margin-bottom: 8px; }

.wizyty-lista { display: flex; flex-direction: column; gap: 8px; margin-bottom: 12px; }

.wizyta-row {
  display: flex; align-items: center; gap: 16px;
  padding: 12px; border-radius: 8px; background: #f8fafc;
}

.wizyta-godzina-blok {
  display: flex; flex-direction: column;
  min-width: 55px; text-align: center;
}
.godzina-od { font-size: 15px; font-weight: 800; color: #3b82f6; }
.godzina-do { font-size: 11px; color: #94a3b8; }

.wizyta-info { display: flex; flex-direction: column; flex: 1; }
.pacjent { font-size: 14px; font-weight: 600; color: #1e293b; }
.lekarz  { font-size: 12px; color: #64748b; margin-top: 2px; }

.lekarze-lista { display: flex; flex-direction: column; gap: 8px; }

.lekarz-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 16px; background: #f8fafc; border-radius: 8px;
}

.lekarz-info { display: flex; flex-direction: column; }
.lekarz-nazwa   { font-size: 14px; font-weight: 600; color: #1e293b; }
.lekarz-gabinety { font-size: 12px; color: #64748b; margin-top: 2px; }

.lekarz-sloty { display: flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 600; }
.slot-zajety  { color: #3b82f6; }
.slot-wolny   { color: #16a34a; }
.slot-separator { color: #cbd5e1; }

.btn-link {
  background: none; border: none; color: #3b82f6;
  font-weight: 600; font-size: 13px; cursor: pointer;
  padding: 8px 0 0 0; display: block;
}
.btn-link:hover { color: #2563eb; }
</style>