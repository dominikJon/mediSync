<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

interface Wizyta {
  id: number
  status: string
  termin_od: string
  termin_do: string
  pacjent: string
  pacjent_telefon: string
  lekarz: string
  gabinet: string
}

const wizyty = ref<Wizyta[]>([])
const ladowanie = ref(true)
const blad = ref('')
const sukces = ref('')
const wybranaData = ref(new Date().toISOString().split('T')[0])
const wizytaDoOdwolania = ref<number | null>(null)

const fetchWizyty = async () => {
  ladowanie.value = true
  blad.value = ''
  try {
    const res = await axios.get(`/api/reception/wizyty?data=${wybranaData.value}`)
    wizyty.value = res.data.wizyty
  } catch {
    blad.value = 'Błąd podczas pobierania wizyt.'
  } finally {
    ladowanie.value = false
  }
}

const changeDate = (days: number) => {
  const d = new Date(wybranaData.value)
  d.setDate(d.getDate() + days)
  wybranaData.value = d.toISOString().split('T')[0]
  fetchWizyty()
}

const moznaOdwolac = (termin_od: string): boolean => {
  const termin = new Date(
    termin_od + (termin_od.includes('+') || termin_od.endsWith('Z') ? '' : 'Z')
  )
  return termin > new Date(Date.now() + 24 * 60 * 60 * 1000)
}

const odwolaj = async (id: number) => {
  blad.value = ''
  sukces.value = ''
  try {
    await axios.delete(`/api/wizyty/${id}`)
    wizytaDoOdwolania.value = null
    sukces.value = 'Wizyta została odwołana.'
    await fetchWizyty()
  } catch (error: any) {
    blad.value = error.response?.data?.detail || 'Nie udało się odwołać wizyty.'
  }
}

const formatGodzina = (iso: string) =>
  new Date(iso).toLocaleTimeString('pl-PL', { hour: '2-digit', minute: '2-digit' })

const statusKolor = (status: string) => {
  switch (status) {
    case 'Zaplanowana': return 'badge-zaplanowana'
    case 'Zakończona':  return 'badge-zakonczona'
    case 'Odwołana':    return 'badge-odwolana'
    default: return ''
  }
}

onMounted(fetchWizyty)
</script>

<template>
  <div class="page">
    <h1 class="page-title">Lista wizyt</h1>

    <div class="date-selector card">
      <button class="btn-secondary" @click="changeDate(-1)">← Poprzedni dzień</button>
      <input
        type="date"
        v-model="wybranaData"
        @change="fetchWizyty"
        class="date-input"
      />
      <button class="btn-secondary" @click="changeDate(1)">Następny dzień →</button>
    </div>

    <div v-if="blad" class="error-box">
      {{ blad }}
      <button @click="blad = ''" class="close-btn">✕</button>
    </div>

    <div v-if="sukces" class="sukces-box">
      {{ sukces }}
      <button @click="sukces = ''" class="close-btn">✕</button>
    </div>

    <div v-if="ladowanie" class="loading-state">Ładowanie wizyt...</div>

    <div v-else-if="wizyty.length === 0" class="empty-state">
      <span class="empty-icon">📋</span>
      <p>Brak wizyt w wybranym dniu.</p>
    </div>

    <div v-else class="card" style="padding: 0; overflow: hidden;">
      <table class="table">
        <thead>
          <tr>
            <th>Godzina</th>
            <th>Pacjent</th>
            <th>Telefon</th>
            <th>Lekarz</th>
            <th>Gabinet</th>
            <th>Status</th>
            <th>Akcja</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="w in wizyty" :key="w.id">
            <td class="fw-bold">
              {{ formatGodzina(w.termin_od) }} – {{ formatGodzina(w.termin_do) }}
            </td>
            <td>{{ w.pacjent }}</td>
            <td class="text-muted">{{ w.pacjent_telefon ?? '—' }}</td>
            <td>{{ w.lekarz }}</td>
            <td>{{ w.gabinet }}</td>
            <td>
              <span :class="['badge', statusKolor(w.status)]">{{ w.status }}</span>
            </td>
            <td>
              <div v-if="w.status === 'Zaplanowana' && moznaOdwolac(w.termin_od)">
                <div v-if="wizytaDoOdwolania === w.id" class="confirm-actions">
                  <span class="confirm-text">Na pewno?</span>
                  <button @click="odwolaj(w.id)" class="btn-danger btn-sm">Tak</button>
                  <button @click="wizytaDoOdwolania = null" class="btn-secondary btn-sm">Nie</button>
                </div>
                <button
                  v-else
                  @click="wizytaDoOdwolania = w.id"
                  class="btn-danger btn-outline btn-sm"
                >
                  Odwołaj
                </button>
              </div>
              <span v-else-if="w.status === 'Zaplanowana'" class="text-muted text-sm">
                Za mniej niż 24h
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.page { padding: 32px; max-width: 1100px; }
.page-title { font-size: 24px; font-weight: 700; color: #1e293b; margin: 0 0 24px 0; }

.date-selector {
  display: flex; justify-content: center;
  align-items: center; gap: 16px; padding: 16px;
  margin-bottom: 24px;
}

.date-input {
  padding: 8px 12px; border: 1px solid #cbd5e1;
  border-radius: 6px; font-family: inherit; font-size: 14px;
}

.card {
  background: white; border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06); margin-bottom: 24px;
}

.table { width: 100%; border-collapse: collapse; text-align: left; }

.table th {
  background: #f8fafc; padding: 16px 20px;
  font-size: 13px; font-weight: 600; color: #475569;
  border-bottom: 1px solid #e2e8f0;
}

.table td {
  padding: 14px 20px; border-bottom: 1px solid #e2e8f0;
  font-size: 14px; color: #1e293b; vertical-align: middle;
}

.table tbody tr:last-child td { border-bottom: none; }
.table tbody tr:hover { background: #f8fafc; }

.fw-bold { font-weight: 600; }
.text-muted { color: #94a3b8; }
.text-sm { font-size: 12px; }

.badge {
  padding: 4px 12px; border-radius: 20px;
  font-size: 12px; font-weight: 600; display: inline-block;
}
.badge-zaplanowana { background: #dbeafe; color: #1e40af; }
.badge-zakonczona  { background: #dcfce7; color: #166534; }
.badge-odwolana    { background: #f1f5f9; color: #64748b; }

.confirm-actions { display: flex; align-items: center; gap: 8px; }
.confirm-text { font-size: 12px; font-weight: 600; color: #ef4444; }

.btn-danger {
  background: #ef4444; color: white; border: none;
  padding: 8px 14px; border-radius: 6px;
  font-size: 13px; font-weight: 600; cursor: pointer; transition: 0.2s;
}
.btn-danger:hover { background: #dc2626; }
.btn-danger.btn-outline {
  background: white; color: #ef4444; border: 1px solid #ef4444;
}
.btn-danger.btn-outline:hover { background: #fef2f2; }

.btn-secondary {
  background: #f1f5f9; color: #475569; border: 1px solid #cbd5e1;
  padding: 8px 14px; border-radius: 6px;
  font-size: 13px; font-weight: 600; cursor: pointer; transition: 0.2s;
}
.btn-secondary:hover { background: #e2e8f0; }
.btn-sm { padding: 6px 10px; font-size: 12px; }

.loading-state {
  text-align: center; padding: 32px;
  color: #3b82f6; font-style: italic;
}

.empty-state {
  background: #f8fafc; border: 2px dashed #cbd5e1;
  border-radius: 12px; min-height: 200px;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  gap: 12px; color: #64748b;
}
.empty-icon { font-size: 36px; }

.error-box {
  display: flex; justify-content: space-between; align-items: center;
  background: #fee2e2; color: #b91c1c;
  padding: 14px 20px; border-radius: 8px;
  border: 1px solid #fca5a5; margin-bottom: 24px;
  font-weight: 500; font-size: 14px;
}

.sukces-box {
  display: flex; justify-content: space-between; align-items: center;
  background: #dcfce7; color: #15803d;
  padding: 14px 20px; border-radius: 8px;
  border: 1px solid #86efac; margin-bottom: 24px;
  font-weight: 500; font-size: 14px;
}

.close-btn {
  background: transparent; border: none; color: inherit;
  cursor: pointer; font-size: 16px; font-weight: bold;
  padding: 0 8px; opacity: 0.7;
}
.close-btn:hover { opacity: 1; }
</style>