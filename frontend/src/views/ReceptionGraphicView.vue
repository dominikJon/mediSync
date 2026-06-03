<script setup lang="ts">
import { ref, onMounted } from 'vue'

interface Lekarz {
  id: number
  imie: string
  nazwisko: string
  specjalizacje: string[]
}

interface Gabinet {
  id: number
  numer: string
  status: string
}

interface Slot {
  id: number
  lekarz: string
  gabinet: string
  termin_od: string
  termin_do: string
  zajety: boolean
}

const today = new Date().toISOString().split('T')[0]

const doctors = ref<Lekarz[]>([])
const rooms = ref<Gabinet[]>([])
const dailySchedule = ref<Slot[]>([])
const previewSlots = ref<string[]>([])

const tryb = ref<'pojedynczy' | 'cykliczny'>('pojedynczy')
const formCykliczny = ref({
  data_od: today,
  data_do: today,
  wybrane_dni: [] as number[]
})
const datyDoWygenerowania = ref<string[]>([]) 

const showPreview = ref(false)
const currentViewDate = ref(today)

const ladowanie = ref(false)
const blad = ref('')
const sukces = ref('')
const slotDoUsuniecia = ref<number | null>(null)

const form = ref({
  lekarz_id: null as number | null,
  gabinet_id: null as number | null,
  data: today,
  godzina_od: '08:00',
  godzina_do: '16:00',
  co_ile_minut: 30
})

const getHeaders = () => ({
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${localStorage.getItem('token')}`
})

const fetchDoctors = async () => {
  try {
    const res = await fetch('/api/reception/lekarze', { headers: getHeaders() })
    if (!res.ok) throw new Error()
    const data = await res.json()
    doctors.value = data.lekarze
  } catch {
    blad.value = 'Błąd podczas pobierania listy lekarzy.'
  }
}

const fetchRooms = async () => {
  try {
    const res = await fetch('/api/reception/gabinety', { headers: getHeaders() })
    if (!res.ok) throw new Error()
    const data = await res.json()
    rooms.value = data.gabinety.filter((g: Gabinet) => g.status === 'Dostępny')
  } catch {
    blad.value = 'Błąd podczas pobierania listy gabinetów.'
  }
}

const fetchSchedule = async () => {
  ladowanie.value = true
  blad.value = ''
  try {
    const res = await fetch(`/api/reception/grafiki?data=${currentViewDate.value}`, { headers: getHeaders() })
    if (!res.ok) throw new Error()
    const data = await res.json()
    dailySchedule.value = data.grafiki
  } catch {
    blad.value = 'Błąd podczas pobierania grafiku na dany dzień.'
  } finally {
    ladowanie.value = false
  }
}

const waliduj = (): boolean => {
  blad.value = ''
  sukces.value = ''
  if (!form.value.lekarz_id) { blad.value = 'Wybierz lekarza.'; return false }
  if (!form.value.gabinet_id) { blad.value = 'Wybierz gabinet.'; return false }
  if (form.value.godzina_od >= form.value.godzina_do) { 
    blad.value = 'Godzina "od" musi być wcześniejsza niż "do".'
    return false 
  }

  if (tryb.value === 'pojedynczy') {
    if (!form.value.data) { blad.value = 'Wybierz datę.'; return false }
  } else {
    if (!formCykliczny.value.data_od || !formCykliczny.value.data_do) { blad.value = 'Wybierz zakres dat.'; return false }
    if (formCykliczny.value.data_od > formCykliczny.value.data_do) { blad.value = 'Data "od" nie może być późniejsza niż "do".'; return false }
    if (formCykliczny.value.wybrane_dni.length === 0) { blad.value = 'Wybierz co najmniej jeden dzień tygodnia.'; return false }

    // Walidacja max 360 dni
    const dataOd = new Date(formCykliczny.value.data_od + 'T00:00:00').getTime()
    const dataDo = new Date(formCykliczny.value.data_do + 'T00:00:00').getTime()
    const diffDni = (dataDo - dataOd) / 86400000
    if (diffDni > 360) { 
      blad.value = 'Zakres dat nie może przekraczać 360 dni.'
      return false 
    }
  }

  return true
}

const obliczDatyCykliczne = () => {
  datyDoWygenerowania.value = []
  
  // T00:00:00 wymusza czas lokalny i zapobiega bugowi przesunięcia o 1 dzień w tył
  const aktualna = new Date(formCykliczny.value.data_od + 'T00:00:00')
  const koncowa = new Date(formCykliczny.value.data_do + 'T00:00:00')

  while (aktualna <= koncowa) {
    if (formCykliczny.value.wybrane_dni.includes(aktualna.getDay())) {
      // Kuloodporne wyciąganie stringa YYYY-MM-DD w czasie lokalnym
      const rok = aktualna.getFullYear()
      const miesiac = String(aktualna.getMonth() + 1).padStart(2, '0')
      const dzien = String(aktualna.getDate()).padStart(2, '0')
      datyDoWygenerowania.value.push(`${rok}-${miesiac}-${dzien}`)
    }
    aktualna.setDate(aktualna.getDate() + 1)
  }
}

const generatePreview = () => {
  if (!waliduj()) return

  previewSlots.value = []
  
  if (tryb.value === 'pojedynczy') {
    datyDoWygenerowania.value = [form.value.data as string]
  } else {
    obliczDatyCykliczne()
    if (datyDoWygenerowania.value.length === 0) {
      blad.value = 'W wybranym zakresie nie ma ani jednego wybranego dnia tygodnia.'
      return
    }
  }

  const [hOd, mOd] = form.value.godzina_od.split(':').map(Number)
  const [hDo, mDo] = form.value.godzina_do.split(':').map(Number)

  let start = new Date(0, 0, 0, hOd, mOd)
  const end = new Date(0, 0, 0, hDo, mDo)
  const step = form.value.co_ile_minut * 60000

  while (start.getTime() + step <= end.getTime()) {
    const slotEnd = new Date(start.getTime() + step)
    const sStr = start.toTimeString().substring(0, 5)
    const eStr = slotEnd.toTimeString().substring(0, 5)
    previewSlots.value.push(`${sStr} - ${eStr}`)
    start = slotEnd
  }
  showPreview.value = true
}

const saveSchedule = async () => {
  ladowanie.value = true
  blad.value = ''
  sukces.value = ''
  
  let lacznieDodanych = 0
  let wystapilBlad = false

  try {
    for (const dataGen of datyDoWygenerowania.value) {
      const payload = { ...form.value, data: dataGen }
      
      const res = await fetch('/api/reception/grafiki', {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify(payload)
      })

      const data = await res.json()
      if (res.ok) {
        lacznieDodanych += data.dodano_slotow || 0
      } else {
        wystapilBlad = true
        blad.value = `Błąd dla daty ${dataGen}: ${data.detail}. Poprzednie dni (${lacznieDodanych > 0 ? lacznieDodanych + ' slotów' : 'brak'}) zostały zapisane.`
        break 
      }
    }

    if (!wystapilBlad && lacznieDodanych > 0) {
      showPreview.value = false
      sukces.value = `Pomyślnie wygenerowano łącznie ${lacznieDodanych} slotów dla ${datyDoWygenerowania.value.length} dni.`
      
      form.value = {
        lekarz_id: null,
        gabinet_id: null,
        data: today,
        godzina_od: '08:00',
        godzina_do: '16:00',
        co_ile_minut: 30
      }
      formCykliczny.value = { data_od: today, data_do: today, wybrane_dni: [] }
      datyDoWygenerowania.value = []

      await fetchSchedule()
    }
  } catch {
    blad.value = 'Problem z połączeniem z serwerem podczas zapisywania.'
  } finally {
    ladowanie.value = false
  }
}

const confirmDeleteSlot = (id: number) => {
  slotDoUsuniecia.value = id
}

const cancelDeleteSlot = () => {
  slotDoUsuniecia.value = null
}

const deleteSlot = async (id: number) => {
  blad.value = ''
  sukces.value = ''
  try {
    const res = await fetch(`/api/reception/grafiki/${id}`, {
      method: 'DELETE',
      headers: getHeaders()
    })

    if (res.ok) {
      sukces.value = 'Slot został pomyślnie usunięty.'
      slotDoUsuniecia.value = null
      await fetchSchedule()
    } else {
      const error = await res.json()
      blad.value = error.detail || 'Błąd podczas usuwania slotu.'
    }
  } catch {
    blad.value = 'Problem z połączeniem z serwerem przy usuwaniu.'
  }
}

const changeDate = (days: number) => {
  const d = new Date(currentViewDate.value as string)
  d.setDate(d.getDate() + days)
  currentViewDate.value = d.toISOString().split('T')[0]
  fetchSchedule()
}

const formatTime = (datetimeStr: string): string => {
  return datetimeStr.substring(11, 16)
}

onMounted(() => {
  fetchDoctors()
  fetchRooms()
  fetchSchedule()
})
</script>

<template>
  <div class="grafik-view">
    <div v-if="blad " class="error-box-wide">{{ blad }}</div>
    <div v-if="sukces" class="success-box-wide">{{ sukces }}</div>

    <div class="grafik-layout">
      <div class="section-a">
        <h2>Kreator grafiku</h2>
        
        <div class="grafik-form">
          <div class="form-group">
            <label>Lekarz:</label>
            <select v-model="form.lekarz_id">
              <option disabled :value="null">Wybierz lekarza</option>
              <option v-for="d in doctors" :key="d.id" :value="d.id">
                {{ d.imie }} {{ d.nazwisko }}
              </option>
            </select>
          </div>

          <div class="form-group">
            <label>Gabinet:</label>
            <select v-model="form.gabinet_id">
              <option disabled :value="null">Wybierz gabinet</option>
              <option v-for="g in rooms" :key="g.id" :value="g.id">
                Gabinet {{ g.numer }}
              </option>
            </select>
          </div>

          <div class="form-group mode-selector">
            <label class="radio-label">
              <input type="radio" v-model="tryb" value="pojedynczy" /> Pojedynczy dzień
            </label>
            <label class="radio-label">
              <input type="radio" v-model="tryb" value="cykliczny" /> Cykliczny (Wiele dni)
            </label>
          </div>

          <div v-if="tryb === 'pojedynczy'" class="form-group">
            <label>Data:</label>
            <input type="date" v-model="form.data" :min="today" />
          </div>

          <div v-if="tryb === 'cykliczny'" class="cyclic-group">
            <div class="form-group">
              <label>Data od:</label>
              <input type="date" v-model="formCykliczny.data_od" :min="today" />
            </div>
            <div class="form-group">
              <label>Data do:</label>
              <input type="date" v-model="formCykliczny.data_do" :min="formCykliczny.data_od" />
            </div>
            <div class="form-group">
              <label>Wybierz dni tygodnia:</label>
              <div class="days-checkboxes">
                <label><input type="checkbox" v-model="formCykliczny.wybrane_dni" :value="1"> Pon</label>
                <label><input type="checkbox" v-model="formCykliczny.wybrane_dni" :value="2"> Wt</label>
                <label><input type="checkbox" v-model="formCykliczny.wybrane_dni" :value="3"> Śr</label>
                <label><input type="checkbox" v-model="formCykliczny.wybrane_dni" :value="4"> Czw</label>
                <label><input type="checkbox" v-model="formCykliczny.wybrane_dni" :value="5"> Pt</label>
                <label><input type="checkbox" v-model="formCykliczny.wybrane_dni" :value="6"> Sob</label>
                <label><input type="checkbox" v-model="formCykliczny.wybrane_dni" :value="0"> Nd</label>
              </div>
            </div>
          </div>
          <div class="time-inputs-row">
            <div class="form-group half-width">
              <label>Od godziny:</label>
              <input type="time" v-model="form.godzina_od" />
            </div>
            <div class="form-group half-width">
              <label>Do godziny:</label>
              <input type="time" v-model="form.godzina_do" />
            </div>
          </div>

          <div class="form-group">
            <label>Co ile minut (długość wizyty):</label>
            <select v-model="form.co_ile_minut">
              <option :value="15">15 min</option>
              <option :value="20">20 min</option>
              <option :value="30">30 min</option>
              <option :value="45">45 min</option>
              <option :value="60">1 godzina</option>
            </select>
          </div>

          <button @click="generatePreview" class="btn-primary" v-if="!showPreview">
            Generuj grafik
          </button>
        </div>

        <div v-if="showPreview" class="preview-box">
          <h3>Podgląd:</h3>
          <p class="preview-meta">Liczba dni do wygenerowania: <strong>{{ datyDoWygenerowania.length }}</strong></p>
          
          <div v-if="tryb === 'cykliczny'" class="preview-dates-container">
            <p class="preview-meta">Wyliczone daty:</p>
            <ul class="preview-dates-list">
              <li v-for="d in datyDoWygenerowania" :key="d">{{ d }}</li>
            </ul>
          </div>

          <p class="preview-meta">Sloty dla każdego dnia:</p>
          <ul class="preview-list">
            <li v-for="(slot, index) in previewSlots" :key="index">{{ slot }}</li>
          </ul>
          <div class="preview-actions">
            <button @click="showPreview = false" class="btn-secondary">Anuluj</button>
            <button @click="saveSchedule" class="btn-success" :disabled="ladowanie">
              {{ ladowanie ? 'Zapisywanie...' : 'Zatwierdź i zapisz wszystko' }}
            </button>
          </div>
        </div>
      </div>

      <div class="section-b">
        <h2>Podgląd dnia</h2>
        <div class="date-nav">
          <button @click="changeDate(-1)" class="btn-nav">← Poprzedni dzień</button>
          <input type="date" v-model="currentViewDate" @change="fetchSchedule" class="date-display" />
          <button @click="changeDate(1)" class="btn-nav">Następny dzień →</button>
        </div>

        <div v-if="ladowanie" class="loading-state">Ładowanie grafiku...</div>
        
        <table v-else class="schedule-table">
          <thead>
            <tr>
              <th>Godzina</th>
              <th>Lekarz</th>
              <th>Gabinet</th>
              <th>Status</th>
              <th>Akcja</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="slot in dailySchedule" :key="slot.id">
              <td>{{ formatTime(slot.termin_od) }} – {{ formatTime(slot.termin_do) }}</td>
              <td>{{ slot.lekarz }}</td>
              <td>{{ slot.gabinet }}</td>
              <td>
                <span v-if="slot.zajety" class="status-zajety">Zajęty</span>
                <span v-else class="status-wolny">Wolny</span>
              </td>
              <td>
                <div v-if="!slot.zajety">
                  <div v-if="slotDoUsuniecia === slot.id" class="confirm-actions">
                    <span class="confirm-text">Usunąć?</span>
                    <button @click="deleteSlot(slot.id)" class="btn-danger btn-sm">Tak</button>
                    <button @click="cancelDeleteSlot" class="btn-secondary btn-sm">Nie</button>
                  </div>
                  <button v-else @click="confirmDeleteSlot(slot.id)" class="btn-danger">
                    Usuń
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="dailySchedule.length === 0">
              <td colspan="5" class="empty-state">Brak grafików na ten dzień.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<style scoped>
.grafik-view {
  padding: 32px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 20px;
  width: 100%;
}

.grafik-layout {
  display: flex;
  gap: 20px;
  align-items: flex-start;
  width: 100%;
}

.section-a, .section-b {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.section-a {
  flex: 1;
  min-width: 320px;
}

.section-b {
  flex: 2;
}

.form-group {
  margin-bottom: 15px;
  display: flex;
  flex-direction: column;
}

.form-group label {
  margin-bottom: 5px;
  font-weight: 500;
  color: #334155;
}

.form-group select, .form-group input {
  padding: 8px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  outline: none;
  font-family: inherit;
}

.form-group select:focus, .form-group input:focus {
  border-color: #3b82f6;
}

.mode-selector {
  flex-direction: row;
  gap: 15px;
  background: #f8fafc;
  padding: 10px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.radio-label {
  display: flex;
  align-items: center;
  gap: 5px;
  cursor: pointer;
  font-weight: 500;
  color: #334155;
  margin: 0 !important;
}

.cyclic-group {
  background: #f1f5f9;
  padding: 15px;
  border-radius: 8px;
  border: 1px dashed #cbd5e1;
  margin-bottom: 15px;
}

.days-checkboxes {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.days-checkboxes label {
  display: flex;
  align-items: center;
  gap: 4px;
  background: white;
  padding: 6px 10px;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9em;
  font-weight: normal;
  margin: 0;
}

.time-inputs-row {
  display: flex;
  gap: 15px;
}

.half-width {
  flex: 1;
}

.preview-meta {
  margin: 0 0 10px 0;
  color: #475569;
  font-size: 0.9em;
}

.preview-box {
  margin-top: 20px;
  padding: 15px;
  background: #f8fafc;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
}

.preview-list {
  list-style: none;
  padding: 0;
  max-height: 200px;
  overflow-y: auto;
  color: #334155;
}

/* Nowe style dla listy dat w podglądzie */
.preview-dates-container {
  margin-bottom: 15px;
  background: white;
  padding: 10px;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
}

.preview-dates-list {
  list-style-type: square;
  margin: 5px 0 0 0;
  padding-left: 20px;
  max-height: 100px;
  overflow-y: auto;
  color: #334155;
  font-size: 0.9em;
}

.preview-actions {
  display: flex;
  gap: 10px;
  margin-top: 15px;
}

.date-nav {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 15px;
  margin-bottom: 20px;
}

.date-display {
  padding: 8px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
}

.loading-state {
  text-align: center;
  padding: 20px;
  color: #64748b;
  font-style: italic;
}

.schedule-table {
  width: 100%;
  border-collapse: collapse;
}

.schedule-table th, .schedule-table td {
  padding: 12px;
  border-bottom: 1px solid #e2e8f0;
  text-align: left;
}

.status-zajety {
  color: #ef4444;
  font-weight: 600;
}

.status-wolny {
  color: #22c55e;
  font-weight: 600;
}

.empty-state {
  text-align: center;
  color: #64748b;
  font-style: italic;
  padding: 20px;
}

.error-box-wide {
  background: #fee2e2;
  color: #b91c1c;
  padding: 12px 16px;
  border-radius: 8px;
  border: 1px solid #fecaca;
  width: 100%;
  box-sizing: border-box;
  font-weight: 500;
}

.success-box-wide {
  background: #dcfce3;
  color: #15803d;
  padding: 12px 16px;
  border-radius: 8px;
  border: 1px solid #bbf7d0;
  width: 100%;
  box-sizing: border-box;
  font-weight: 500;
}

.btn-primary {
  background: #3b82f6;
  color: white;
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: 0.2s;
  font-weight: 500;
}

.btn-primary:hover {
  background: #2563eb;
}

.btn-secondary {
  background: #94a3b8;
  color: white;
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
}

.btn-secondary:hover {
  background: #64748b;
}

.btn-success {
  background: #22c55e;
  color: white;
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
}

.btn-success:hover {
  background: #16a34a;
}

.btn-success:disabled {
  background: #86efac;
  cursor: not-allowed;
}

.btn-danger {
  background: #ef4444;
  color: white;
  padding: 6px 12px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
}

.btn-danger:hover {
  background: #dc2626;
}

.btn-nav {
  background: #f8fafc;
  border: 1px solid #cbd5e1;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  color: #334155;
}

.btn-nav:hover {
  background: #f1f5f9;
}

.confirm-actions {
  display: flex;
  gap: 5px;
  align-items: center;
}

.confirm-text {
  font-size: 0.85em;
  color: #64748b;
  margin-right: 5px;
}

.btn-sm {
  padding: 4px 8px;
  font-size: 0.85em;
}
</style>