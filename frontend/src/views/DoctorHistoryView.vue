<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

const ladowanie = ref(true)
const blad = ref('')
const wizyty = ref<any[]>([])
const rozwinietaWizyta = ref<number | null>(null)
const szukaj = ref('')

const pobierzHistorie = async () => {
  try {
    const res = await axios.get('/api/lekarz/historia')
    wizyty.value = res.data.wizyty
  } catch {
    blad.value = 'Błąd podczas pobierania historii.'
  } finally {
    ladowanie.value = false
  }
}

const przefiltrowane = () => {
  if (!szukaj.value.trim()) return wizyty.value
  const q = szukaj.value.toLowerCase()
  return wizyty.value.filter(w =>
    w.pacjent.toLowerCase().includes(q) ||
    w.pacjent_pesel?.includes(q)
  )
}

const toggleWizyta = (id: number) => {
  rozwinietaWizyta.value = rozwinietaWizyta.value === id ? null : id
}

const formatData = (iso: string) =>
  new Date(iso).toLocaleDateString('pl-PL', {
    year: 'numeric', month: 'long', day: 'numeric'
  })

const formatGodzina = (iso: string) =>
  new Date(iso).toLocaleTimeString('pl-PL', { hour: '2-digit', minute: '2-digit' })

const formatujKlucz = (klucz: string) =>
  klucz.replace(/_/g, ' ').replace(/([a-z])([A-Z])/g, '$1 $2')
    .replace(/^\w/, c => c.toUpperCase())

onMounted(pobierzHistorie)
</script>

<template>
  <div class="page">
    <h1 class="page-title">Historia wizyt</h1>

    <div class="szukaj-box">
      <input
        v-model="szukaj"
        type="text"
        placeholder="Szukaj po nazwisku lub PESEL pacjenta..."
        class="szukaj-input"
      />
    </div>

    <div v-if="ladowanie" class="loading">Ładowanie...</div>
    <div v-else-if="blad" class="error-box">{{ blad }}</div>

    <div v-else-if="przefiltrowane().length === 0" class="empty-state">
      <span>📂</span>
      <p>Brak zakończonych wizyt.</p>
    </div>

    <div v-else class="wizyty-lista">
      <div v-for="w in przefiltrowane()" :key="w.id" class="wizyta-card">
        <div class="wizyta-header" @click="toggleWizyta(w.id)">
          <div class="wizyta-data-blok">
            <span class="wizyta-data">{{ formatData(w.termin_od) }}</span>
            <span class="wizyta-godzina">
              {{ formatGodzina(w.termin_od) }} — {{ formatGodzina(w.termin_do) }}
            </span>
          </div>
          <div class="wizyta-info">
            <span class="pacjent">{{ w.pacjent }}</span>
            <span class="pesel">PESEL: {{ w.pacjent_pesel }}</span>
            <span class="usluga">{{ w.nazwa_uslugi }} · Gabinet {{ w.gabinet }}</span>
          </div>
          <div class="wizyta-prawa">
            <span class="badge-zakonczona">Zakończona</span>
            <button class="btn-edm">
              {{ rozwinietaWizyta === w.id ? '▲ Ukryj' : '▼ EDM' }}
            </button>
          </div>
        </div>

        <div v-if="rozwinietaWizyta === w.id" class="wizyta-dokumentacja">
          <div v-if="w.dokumentacja" class="edm">
            <div class="edm-title">Dokumentacja medyczna</div>
            <div v-if="w.dokumentacja.kod_icd10" class="edm-row">
              <span class="edm-label">Rozpoznanie ICD-10</span>
              <span class="edm-value">
                <strong>{{ w.dokumentacja.kod_icd10 }}</strong>
                — {{ w.dokumentacja.icd10_nazwa }}
              </span>
            </div>
            <div v-if="w.dokumentacja.wywiad_lekarski" class="edm-wywiad">
              <span class="edm-label">Wywiad lekarski</span>
              <div class="edm-pola">
                <div
                  v-for="(wartosc, klucz) in w.dokumentacja.wywiad_lekarski"
                  :key="klucz"
                  class="edm-pole"
                >
                  <span class="edm-pole-klucz">{{ formatujKlucz(String(klucz)) }}</span>
                  <span class="edm-pole-wartosc">{{ wartosc }}</span>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="edm-brak">
            Brak dokumentacji dla tej wizyty.
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page { padding: 32px; max-width: 900px; }
.page-title { font-size: 24px; font-weight: 700; color: #1e293b; margin: 0 0 20px 0; }

.szukaj-box { margin-bottom: 20px; }
.szukaj-input {
  width: 100%; padding: 12px 16px;
  border: 1px solid #e2e8f0; border-radius: 10px;
  font-size: 14px; box-sizing: border-box;
}
.szukaj-input:focus { outline: none; border-color: #3b82f6; }

.loading { color: #64748b; padding: 20px; }
.error-box { background: #fee2e2; color: #dc2626; padding: 12px 16px; border-radius: 8px; }

.empty-state {
  text-align: center; padding: 48px;
  color: #94a3b8; font-size: 14px;
}
.empty-state span { font-size: 36px; display: block; margin-bottom: 8px; }

.wizyty-lista { display: flex; flex-direction: column; gap: 8px; }

.wizyta-card {
  background: white; border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06); overflow: hidden;
}

.wizyta-header {
  display: flex; align-items: center; gap: 16px;
  padding: 16px 20px; cursor: pointer; transition: 0.15s;
}
.wizyta-header:hover { background: #f8fafc; }

.wizyta-data-blok { display: flex; flex-direction: column; min-width: 150px; }
.wizyta-data { font-size: 13px; font-weight: 600; color: #1e293b; }
.wizyta-godzina { font-size: 12px; color: #64748b; margin-top: 2px; }

.wizyta-info { display: flex; flex-direction: column; flex: 1; }
.pacjent { font-size: 14px; font-weight: 700; color: #1e293b; }
.pesel { font-size: 12px; color: #94a3b8; margin-top: 2px; }
.usluga { font-size: 12px; color: #64748b; margin-top: 2px; }

.wizyta-prawa { display: flex; flex-direction: column; align-items: flex-end; gap: 8px; }

.badge-zakonczona {
  padding: 4px 12px; border-radius: 20px;
  background: #dcfce7; color: #166534;
  font-size: 12px; font-weight: 600;
}

.btn-edm {
  background: none; border: 1px solid #e2e8f0;
  color: #64748b; border-radius: 6px;
  padding: 6px 12px; font-size: 12px;
  font-weight: 600; cursor: pointer; transition: 0.15s;
}
.btn-edm:hover { border-color: #3b82f6; color: #3b82f6; }

.wizyta-dokumentacja {
  border-top: 1px solid #e2e8f0;
  padding: 20px; background: #f8fafc;
}

.edm-title {
  font-size: 12px; font-weight: 700; color: #64748b;
  text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 12px;
}
.edm-row { margin-bottom: 12px; }
.edm-label { display: block; font-size: 12px; color: #94a3b8; font-weight: 600; margin-bottom: 4px; }
.edm-value { font-size: 14px; color: #1e293b; }
.edm-wywiad { margin-bottom: 12px; }
.edm-pola { display: flex; flex-direction: column; gap: 8px; margin-top: 8px; }
.edm-pole {
  display: flex; flex-direction: column;
  background: white; border: 1px solid #e2e8f0;
  border-radius: 8px; padding: 12px 16px;
}
.edm-pole-klucz {
  font-size: 11px; font-weight: 700; color: #94a3b8;
  text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px;
}
.edm-pole-wartosc { font-size: 14px; color: #1e293b; line-height: 1.5; }
.edm-brak { color: #94a3b8; font-size: 13px; font-style: italic; }
</style>