<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()

const email = ref('')
const haslo = ref('')
const npwz = ref('')
const status_npwz = ref('aktywny')
const waznosc_oc = ref('')
const placowka_id = ref<number | null>(null)
const wybrane_specjalizacje = ref<number[]>([])

const placowki = ref<{ id: number, nazwa: string }[]>([])
const specjalizacje = ref<{ id: number, nazwa: string }[]>([])

const blad = ref('')
const sukces = ref('')
const ladowanie = ref(false)

const pobierzDane = async () => {
  try {
    const [p, s] = await Promise.all([
      axios.get('/api/admin/placowki'),
      axios.get('/api/admin/specjalizacje'),
    ])
    placowki.value = p.data.placowki
    specjalizacje.value = s.data.specjalizacje
  } catch {
    blad.value = 'Błąd podczas pobierania danych.'
  }
}

const toggleSpecjalizacja = (id: number) => {
  const idx = wybrane_specjalizacje.value.indexOf(id)
  if (idx === -1) {
    wybrane_specjalizacje.value.push(id)
  } else {
    wybrane_specjalizacje.value.splice(idx, 1)
  }
}

const handleSubmit = async () => {
  blad.value = ''
  sukces.value = ''

  if (!email.value || !haslo.value || !npwz.value || !waznosc_oc.value || !placowka_id.value) {
    blad.value = 'Wypełnij wszystkie wymagane pola.'
    return
  }

  if (npwz.value.length !== 7) {
    blad.value = 'NPWZ musi mieć dokładnie 7 znaków.'
    return
  }

  if (wybrane_specjalizacje.value.length === 0) {
    blad.value = 'Wybierz co najmniej jedną specjalizację.'
    return
  }

  ladowanie.value = true

  try {
    await axios.post('/api/admin/add-doctor', {
      email: email.value,
      haslo: haslo.value,
      npwz: npwz.value,
      status_npwz: status_npwz.value,
      waznosc_oc: waznosc_oc.value,
      placowka_id: placowka_id.value,
      specjalizacje_ids: wybrane_specjalizacje.value,
    })

    sukces.value = 'Lekarz został dodany pomyślnie!'
    // Wyczyść formularz
    email.value = ''
    haslo.value = ''
    npwz.value = ''
    waznosc_oc.value = ''
    placowka_id.value = null
    wybrane_specjalizacje.value = []

  } catch (error: any) {
    if (error.response?.status === 409) {
      blad.value = error.response.data.detail
    } else if (error.response?.status === 403) {
      blad.value = 'Brak uprawnień.'
    } else {
      blad.value = 'Wystąpił błąd serwera.'
    }
  } finally {
    ladowanie.value = false
  }
}

onMounted(pobierzDane)
</script>

<template>
  <div class="page">
    <div class="page-header">
      <RouterLink to="/admin/users" class="btn-back">← Wróć do listy</RouterLink>
      <h1>Dodaj lekarza</h1>
    </div>

    <div class="card">
      <div v-if="blad" class="error-box">{{ blad }}</div>
      <div v-if="sukces" class="sukces-box">{{ sukces }}</div>

      <div class="form-grid">
        <div class="section-title full">Dane konta</div>

        <div class="form-group">
          <label>Email *</label>
          <input v-model="email" type="email" placeholder="lekarz@medisync.pl" />
        </div>
        <div class="form-group">
          <label>Hasło *</label>
          <input v-model="haslo" type="password" placeholder="Min. 8 znaków" />
        </div>

        <div class="section-title full">Dane zawodowe</div>

        <div class="form-group">
          <label>NPWZ * <span class="hint">(7 znaków)</span></label>
          <input v-model="npwz" type="text" maxlength="7" placeholder="1234567" />
        </div>
        <div class="form-group">
          <label>Status NPWZ *</label>
          <select v-model="status_npwz">
            <option value="aktywny">Aktywny</option>
            <option value="zawieszony">Zawieszony</option>
            <option value="wygasły">Wygasły</option>
          </select>
        </div>
        <div class="form-group">
          <label>Ważność OC *</label>
          <input v-model="waznosc_oc" type="date" />
        </div>
        <div class="form-group">
          <label>Placówka *</label>
          <select v-model="placowka_id">
            <option :value="null" disabled>Wybierz placówkę</option>
            <option v-for="p in placowki" :key="p.id" :value="p.id">
              {{ p.nazwa }}
            </option>
          </select>
        </div>

        <div class="section-title full">Specjalizacje *</div>

        <div class="specjalizacje-grid full">
          <div
            v-for="s in specjalizacje"
            :key="s.id"
            :class="['spec-chip', { aktywna: wybrane_specjalizacje.includes(s.id) }]"
            @click="toggleSpecjalizacja(s.id)"
          >
            {{ s.nazwa }}
          </div>
          <div v-if="specjalizacje.length === 0" class="brak-danych">
            Brak specjalizacji w bazie. Dodaj je najpierw przez SQL.
          </div>
        </div>
      </div>

      <button @click="handleSubmit" class="btn-primary" :disabled="ladowanie">
        {{ ladowanie ? 'Zapisywanie...' : 'Dodaj lekarza' }}
      </button>
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
  margin: 8px 0 0 0;
}

.btn-back {
  color: #64748b;
  text-decoration: none;
  font-size: 14px;
  font-weight: 600;
}

.btn-back:hover { color: #3b82f6; }

.card {
  background: white;
  border-radius: 12px;
  padding: 32px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
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
  margin-bottom: 20px;
  font-size: 14px;
  font-weight: 600;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 24px;
}

.full { grid-column: span 2; }

.section-title {
  font-size: 13px;
  font-weight: 700;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding-bottom: 6px;
  border-bottom: 1px solid #e2e8f0;
  margin-top: 8px;
}

.form-group label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 6px;
}

.hint {
  font-weight: 400;
  color: #94a3b8;
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

.specjalizacje-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.spec-chip {
  padding: 8px 14px;
  border-radius: 20px;
  border: 2px solid #e2e8f0;
  background: #f8fafc;
  color: #475569;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
  user-select: none;
}

.spec-chip:hover {
  border-color: #3b82f6;
  color: #3b82f6;
}

.spec-chip.aktywna {
  border-color: #3b82f6;
  background: #dbeafe;
  color: #1e40af;
}

.brak-danych {
  color: #94a3b8;
  font-size: 13px;
  font-style: italic;
}

.btn-primary {
  width: 100%;
  padding: 14px;
  background-color: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 16px;
  cursor: pointer;
  transition: 0.2s;
}

.btn-primary:hover:not(:disabled) { background-color: #2563eb; }
.btn-primary:disabled { background-color: #93c5fd; cursor: not-allowed; }
</style>