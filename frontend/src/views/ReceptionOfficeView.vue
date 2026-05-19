<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

interface Gabinet {
  id: number
  numer: string
  status: 'Dostępny' | 'Niedostępny'
}

const gabinety = ref<Gabinet[]>([])
const ladowanie = ref(true)
const blad = ref('')

// Formularz dodawania
const nowyNumer = ref('')
const nowyStatus = ref<'Dostępny' | 'Niedostępny'>('Dostępny')
const bladFormularza = ref('')
const sukces = ref('')
const ladowanieFormularza = ref(false)

// Inline zmiana statusu
const zmianaStatusu = ref<Record<number, boolean>>({})

const pobierzGabinety = async () => {
  ladowanie.value = true
  blad.value = ''
  try {
    const response = await axios.get('/api/reception/gabinety')
    gabinety.value = response.data.gabinety
  } catch (error: any) {
    if (error.response?.status === 403) {
      blad.value = 'Brak uprawnień do tej strony.'
    } else {
      blad.value = 'Błąd podczas pobierania listy gabinetów.'
    }
  } finally {
    ladowanie.value = false
  }
}

const statusKolor = (status: string) => {
  switch (status) {
    case 'Dostępny': return 'badge-dostepny'
    case 'Niedostępny': return 'badge-niedostepny'
    default: return ''
  }
}

const zmienStatus = async (gabinet: Gabinet, nowyStatusVal: string) => {
  zmianaStatusu.value[gabinet.id] = true
  try {
    await axios.patch(`/api/reception/gabinety/${gabinet.id}/status`, {
      status: nowyStatusVal,
    })
    gabinet.status = nowyStatusVal as Gabinet['status']
  } catch (error: any) {
    blad.value = error.response?.data?.detail || 'Błąd podczas zmiany statusu.'
  } finally {
    zmianaStatusu.value[gabinet.id] = false
  }
}

const walidujFormularz = (): boolean => {
  if (!nowyNumer.value.trim()) {
    bladFormularza.value = 'Numer gabinetu jest wymagany'
    return false
  }
  if (nowyNumer.value.trim().length > 10) {
    bladFormularza.value = 'Numer gabinetu może mieć maksymalnie 10 znaków'
    return false
  }
  bladFormularza.value = ''
  return true
}

const dodajGabinet = async () => {
  sukces.value = ''
  blad.value = ''
  if (!walidujFormularz()) return

  ladowanieFormularza.value = true
  try {
    await axios.post('/api/reception/gabinety', {
      numer: nowyNumer.value.trim(),
      status: nowyStatus.value,
    })
    sukces.value = `Gabinet ${nowyNumer.value.trim()} został dodany.`
    nowyNumer.value = ''
    nowyStatus.value = 'Dostępny'
    await pobierzGabinety()
  } catch (error: any) {
    if (error.response?.status === 409) {
      bladFormularza.value = 'Gabinet o tym numerze już istnieje'
    } else {
      blad.value = 'Błąd podczas dodawania gabinetu.'
    }
  } finally {
    ladowanieFormularza.value = false
  }
}

onMounted(pobierzGabinety)
</script>

<template>
  <div class="page">
    <div class="page-header">
      <h1>Gabinety</h1>
    </div>

    <div v-if="blad" class="error-box">{{ blad }}</div>

    <!-- Tabela gabinetów -->
    <div class="card mb">
      <div class="card-title">Lista gabinetów</div>

      <div v-if="ladowanie" class="loading">Ładowanie...</div>

      <div v-else-if="gabinety.length === 0" class="brak-danych">
        Brak gabinetów w systemie. Dodaj pierwszy poniżej.
      </div>

      <table v-else class="table">
        <thead>
          <tr>
            <th>Numer</th>
            <th>Status</th>
            <th>Zmień status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="g in gabinety" :key="g.id">
            <td class="numer-cell">{{ g.numer }}</td>
            <td>
              <span :class="['badge', statusKolor(g.status)]">
                {{ g.status }}
              </span>
            </td>
            <td>
              <select
                :value="g.status"
                :disabled="zmianaStatusu[g.id]"
                class="status-select"
                @change="zmienStatus(g, ($event.target as HTMLSelectElement).value)"
              >
                <option value="Dostępny">Dostępny</option>
                <option value="Niedostępny">Niedostępny</option>
              </select>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Formularz dodania gabinetu -->
    <div class="card">
      <div class="card-title">Dodaj gabinet</div>

      <div v-if="sukces" class="sukces-box">{{ sukces }}</div>

      <div class="form-row">
        <div class="form-group">
          <label>Numer gabinetu *</label>
          <input
            v-model="nowyNumer"
            type="text"
            placeholder="np. G04, 101"
            maxlength="10"
            :class="{ 'input-error': bladFormularza }"
            @keyup.enter="dodajGabinet"
          />
          <span v-if="bladFormularza" class="field-error">{{ bladFormularza }}</span>
        </div>

        <div class="form-group">
          <label>Status początkowy</label>
          <select v-model="nowyStatus">
            <option value="Dostępny">Dostępny</option>
            <option value="Niedostępny">Niedostępny</option>
          </select>
        </div>

        <div class="form-group btn-group">
          <label>&nbsp;</label>
          <button
            @click="dodajGabinet"
            class="btn-primary"
            :disabled="ladowanieFormularza"
          >
            {{ ladowanieFormularza ? 'Dodawanie...' : '+ Dodaj gabinet' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page {
  padding: 32px;
  max-width: 800px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
}

.mb { margin-bottom: 24px; }

.card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}

.card-title {
  font-size: 13px;
  font-weight: 700;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding-bottom: 12px;
  border-bottom: 1px solid #e2e8f0;
  margin-bottom: 16px;
}

.error-box {
  background: #fee2e2;
  color: #dc2626;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 20px;
  font-size: 14px;
}

.sukces-box {
  background: #dcfce7;
  color: #166534;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  font-size: 14px;
  font-weight: 600;
}

.loading {
  color: #64748b;
  padding: 16px 0;
  font-size: 14px;
}

.brak-danych {
  color: #94a3b8;
  font-size: 14px;
  font-style: italic;
  padding: 16px 0;
}

.table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.table thead {
  background-color: #f8fafc;
}

.table th {
  padding: 12px 16px;
  text-align: left;
  font-size: 12px;
  font-weight: 700;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid #e2e8f0;
}

.table td {
  padding: 14px 16px;
  border-bottom: 1px solid #f1f5f9;
  color: #1e293b;
}

.table tbody tr:last-child td {
  border-bottom: none;
}

.table tbody tr:hover {
  background-color: #f8fafc;
}

.numer-cell {
  font-weight: 700;
  font-size: 15px;
}

.badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

.badge-dostepny {
  background: #dcfce7;
  color: #166534;
}

.badge-niedostepny {
  background: #fef3c7;
  color: #92400e;
}

.status-select {
  padding: 6px 10px;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 13px;
  color: #1e293b;
  background: white;
  cursor: pointer;
}

.status-select:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.form-row {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.form-group {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.btn-group {
  flex: 0 0 auto;
}

.form-group label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 6px;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  box-sizing: border-box;
  font-size: 14px;
  color: #1e293b;
  background: white;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59,130,246,0.1);
}

.input-error {
  border-color: #ef4444 !important;
}

.field-error {
  display: block;
  color: #ef4444;
  font-size: 12px;
  margin-top: 4px;
}

.btn-primary {
  padding: 10px 20px;
  background-color: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: 0.2s;
  white-space: nowrap;
}

.btn-primary:hover:not(:disabled) {
  background-color: #2563eb;
}

.btn-primary:disabled {
  background-color: #93c5fd;
  cursor: not-allowed;
}
</style>