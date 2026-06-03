<template>
  <div class="page">
    <h1 class="page-title">Moje wizyty</h1>

    <div v-if="blad" class="error-box">
      {{ blad }}
      <button @click="blad = ''" class="close-btn">✕</button>
    </div>
    <div v-if="sukces" class="sukces-box">
      {{ sukces }}
      <button @click="sukces = ''" class="close-btn">✕</button>
    </div>
  </div>

    <!-- Filtry statusu -->
    <div class="filtry">
      <button
        v-for="s in STATUSY"
        :key="s.value"
        :class="['filtr-btn', { aktywny: filtr === s.value }]"
        @click="zmienFiltr(s.value)"
      >
        {{ s.label }}
      </button>
    </div>

    <div v-if="ladowanie" class="loading-state">
      Ładowanie historii wizyt...
    </div>

    <div v-else-if="wizyty.length === 0" class="empty-state">
      <span class="empty-icon">📂</span>
      <p>Brak wizyt{{ filtr ? ` o statusie "${filtr}"` : '' }}.</p>
      <RouterLink v-if="!filtr" to="/schedule" class="link-primary">
        Zarezerwuj pierwszą wizytę →
      </RouterLink>
    </div>

    <div v-else class="wizyty-lista">
      <div v-for="w in wizyty" :key="w.id" class="wizyta-card">

        <!-- Nagłówek wizyty -->
        <div class="wizyta-header">
          <div class="wizyta-data-blok">
            <span class="wizyta-data">{{ formatData(w.termin_od) }}</span>
            <span class="wizyta-godzina">
              {{ formatGodzina(w.termin_od) }} – {{ formatGodzina(w.termin_do) }}
            </span>
          </div>

          <div class="wizyta-info">
            <span class="wizyta-lekarz">
              dr {{ w.lekarz_imie ?? w.lekarz }} {{ w.lekarz_nazwisko ?? '' }}
            </span>
            <span class="wizyta-spec">
              {{ Array.isArray(w.specjalizacje) ? w.specjalizacje.join(', ') : w.specjalizacja }}
              · Gabinet {{ w.gabinet }}
            </span>
            <span class="wizyta-usluga">
              {{ w.nazwa_uslugi ?? '' }} · {{ w.cena }} zł
            </span>
          </div>

          <div class="wizyta-prawa">
            <span :class="['badge', statusKolor(w.status)]">{{ w.status }}</span>

            <!-- Przycisk odwołania -->
            <div v-if="moznaOdwolac(w)" class="akcja-odwolaj">
              <div v-if="wizytaDoOdwolania === w.id" class="confirm-actions">
                <span class="confirm-text">Na pewno?</span>
                <button @click="odwolaj(w.id)" class="btn-danger btn-sm">Tak</button>
                <button @click="wizytaDoOdwolania = null" class="btn-secondary btn-sm">Nie</button>
              </div>
              <button
                v-else
                @click="wizytaDoOdwolania = w.id"
                class="btn-danger btn-outline"
              >
                Odwołaj
              </button>
            </div>

            <!-- Przycisk rozwinięcia dokumentacji -->
            <button
              v-if="w.dokumentacja || w.status === 'Zakończona'"
              class="btn-edm"
              @click="toggleDokumentacja(w.id)"
            >
              {{ rozwinietaWizyta === w.id ? '▲ Ukryj' : '▼ Dokumentacja' }}
            </button>
          </div>
        </div>

        <!-- Dokumentacja EDM -->
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

          <div v-else class="edm-brak">
            Dokumentacja nie została jeszcze uzupełniona.
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()

interface Dokumentacja {
  wywiad_lekarski: any
  kod_icd10: string | null
  icd10_nazwa: string | null
}

interface Wizyta {
  id: number
  status: string
  termin_od: string
  termin_do: string
  // pola z /api/wizyty/moje
  lekarz_imie?: string
  lekarz_nazwisko?: string
  specjalizacje?: string[]
  // pola z /api/pacjent/historia
  lekarz?: string
  specjalizacja?: string
  nazwa_uslugi?: string
  gabinet: string
  cena: string
  dokumentacja?: Dokumentacja | null
}

const STATUSY = [
  { label: 'Wszystkie',  value: '' },
  { label: 'Zaplanowane', value: 'Zaplanowana' },
  { label: 'Zakończone',  value: 'Zakończona' },
  { label: 'Odwołane',    value: 'Odwołana' },
]

const wizyty = ref<Wizyta[]>([])
const ladowanie = ref(true)
const filtr = ref('')
const rozwinietaWizyta = ref<number | null>(null)
const wizytaDoOdwolania = ref<number | null>(null)
const blad = ref('')
const sukces = ref('')

// Pobiera wizyty z obu endpointów i scala je
const fetchWizyty = async () => {
  ladowanie.value = true
  blad.value = ''

  try {
    const [mojeRes, historiaRes] = await Promise.all([
      axios.get('/api/wizyty/moje'),
      axios.get('/api/pacjent/historia', {
        params: filtr.value ? { status: filtr.value } : {}
      }),
    ])

    // Mapa id → dane z historii (dokumentacja, nazwa_uslugi)
    const historiaMap = new Map<number, any>()
    for (const w of historiaRes.data.wizyty) {
      historiaMap.set(w.id, w)
    }

    // Scala dane — baza z /moje, dokumentacja z /historia
    const scalone: Wizyta[] = mojeRes.data.wizyty
      .filter((w: any) => !filtr.value || w.status === filtr.value)
      .map((w: any) => ({
        ...w,
        dokumentacja: historiaMap.get(w.id)?.dokumentacja ?? null,
        nazwa_uslugi: historiaMap.get(w.id)?.nazwa_uslugi ?? null,
      }))

    wizyty.value = scalone
  } catch (error: any) {
    blad.value = error.response?.data?.detail || 'Błąd podczas pobierania wizyt.'
  } finally {
    ladowanie.value = false
  }
}

const zmienFiltr = async (status: string) => {
  filtr.value = status
  rozwinietaWizyta.value = null
  wizytaDoOdwolania.value = null
  await fetchWizyty()
}

const toggleDokumentacja = (id: number) => {
  rozwinietaWizyta.value = rozwinietaWizyta.value === id ? null : id
}

const odwolaj = async (id: number) => {
  blad.value = ''
  sukces.value = ''
  try {
    await axios.delete(`/api/wizyty/${id}`)
    wizytaDoOdwolania.value = null
    sukces.value = 'Wizyta została pomyślnie odwołana.'
    await fetchWizyty()
  } catch (error: any) {
    blad.value = error.response?.data?.detail || 'Nie udało się odwołać wizyty.'
  }
}

const moznaOdwolac = (wizyta: Wizyta) => {
  if (wizyta.status !== 'Zaplanowana') return false
  const termin = new Date(
    wizyta.termin_od + (wizyta.termin_od.includes('+') || wizyta.termin_od.endsWith('Z') ? '' : 'Z')
  )
  return termin > new Date(Date.now() + 24 * 60 * 60 * 1000)
}

const formatData = (iso: string) =>
  new Date(iso).toLocaleDateString('pl-PL', {
    weekday: 'short', year: 'numeric', month: 'short', day: 'numeric',
  })

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

const formatujKlucz = (klucz: string): string => {
  // snake_case i camelCase → czytelna nazwa
  return klucz
    .replace(/_/g, ' ')
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .replace(/^\w/, c => c.toUpperCase())
}

onMounted(() => {
  if (authStore.user?.rola !== 'pacjent') return
  fetchWizyty()
})
</script>

<style scoped>
.page { padding: 32px; max-width: 900px; }

.page-title {
  font-size: 24px; font-weight: 700;
  color: #1e293b; margin: 0 0 24px 0;
}

.filtry { display: flex; gap: 8px; margin-bottom: 20px; flex-wrap: wrap; }

.filtr-btn {
  padding: 8px 16px; border-radius: 20px;
  border: 2px solid #e2e8f0; background: #f8fafc;
  color: #475569; font-size: 13px; font-weight: 600;
  cursor: pointer; transition: 0.15s;
}
.filtr-btn:hover { border-color: #3b82f6; color: #3b82f6; }
.filtr-btn.aktywny { border-color: #3b82f6; background: #dbeafe; color: #1e40af; }

.loading-state {
  text-align: center; padding: 32px;
  color: #3b82f6; font-size: 14px; font-style: italic;
}

.empty-state {
  background: #f8fafc; border: 2px dashed #cbd5e1;
  border-radius: 12px; min-height: 300px;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  gap: 12px; color: #64748b; font-size: 14px;
  text-align: center; padding: 32px;
}
.empty-icon { font-size: 36px; }
.link-primary { color: #3b82f6; font-weight: 600; text-decoration: none; }
.link-primary:hover { text-decoration: underline; }

.wizyty-lista { display: flex; flex-direction: column; gap: 8px; }

.wizyta-card {
  background: white; border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06); overflow: hidden;
}

.wizyta-header {
  display: flex; align-items: center;
  gap: 16px; padding: 16px 20px;
}

.wizyta-data-blok { display: flex; flex-direction: column; min-width: 150px; }
.wizyta-data { font-size: 13px; font-weight: 600; color: #1e293b; }
.wizyta-godzina { font-size: 12px; color: #64748b; margin-top: 2px; }

.wizyta-info { display: flex; flex-direction: column; flex: 1; }
.wizyta-lekarz { font-size: 14px; font-weight: 700; color: #1e293b; }
.wizyta-spec { font-size: 12px; color: #3b82f6; font-weight: 600; margin-top: 2px; }
.wizyta-usluga { font-size: 12px; color: #64748b; margin-top: 2px; }

.wizyta-prawa {
  display: flex; flex-direction: column;
  align-items: flex-end; gap: 8px;
}

.badge {
  padding: 4px 12px; border-radius: 20px;
  font-size: 12px; font-weight: 600; display: inline-block;
}
.badge-zaplanowana { background: #dbeafe; color: #1e40af; }
.badge-zakonczona  { background: #dcfce7; color: #166534; }
.badge-odwolana    { background: #f1f5f9; color: #64748b; }

.akcja-odwolaj { display: flex; align-items: center; }

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
  background: #e2e8f0; color: #475569; border: none;
  padding: 8px 14px; border-radius: 6px;
  font-size: 13px; font-weight: 600; cursor: pointer; transition: 0.2s;
}
.btn-secondary:hover { background: #cbd5e1; }

.btn-sm { padding: 6px 10px; font-size: 12px; }

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
.edm-label {
  display: block; font-size: 12px;
  color: #94a3b8; font-weight: 600; margin-bottom: 4px;
}
.edm-value { font-size: 14px; color: #1e293b; }

.edm-json {
  background: white; border: 1px solid #e2e8f0;
  border-radius: 8px; padding: 12px;
  font-size: 12px; color: #475569;
  overflow-x: auto; white-space: pre-wrap;
}

.edm-brak { color: #94a3b8; font-size: 13px; font-style: italic; }

.error-box {
  display: flex; justify-content: space-between; align-items: center;
  background: #fee2e2; color: #b91c1c;
  padding: 14px 20px; border-radius: 8px;
  border: 1px solid #fca5a5;
  margin-bottom: 24px; font-weight: 500; font-size: 14px;
}

.sukces-box {
  display: flex; justify-content: space-between; align-items: center;
  background: #dcfce7; color: #15803d;
  padding: 14px 20px; border-radius: 8px;
  border: 1px solid #86efac;
  margin-bottom: 24px; font-weight: 500; font-size: 14px;
}

.close-btn {
  background: transparent; border: none; color: inherit;
  cursor: pointer; font-size: 16px; font-weight: bold;
  margin-left: auto; padding: 0 8px; opacity: 0.7;
}
.close-btn:hover { opacity: 1; }

.edm-wywiad { margin-bottom: 12px; }

.edm-pola {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 8px;
}

.edm-pole {
  display: flex;
  flex-direction: column;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 12px 16px;
}

.edm-pole-klucz {
  font-size: 11px;
  font-weight: 700;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 4px;
}

.edm-pole-wartosc {
  font-size: 14px;
  color: #1e293b;
  line-height: 1.5;
}
</style>