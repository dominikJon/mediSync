<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import axios from 'axios'


const email = ref('')
const haslo = ref('')
const imie = ref('')
const nazwisko = ref('')
const npwz = ref('')
const status_npwz = ref('aktywny')
const waznosc_oc = ref('')
const telefon = ref('')
const placowka_id = ref<number | null>(null)
const wybrane_specjalizacje = ref<number[]>([])

const placowki = ref<{ id: number, nazwa: string }[]>([])
const specjalizacje = ref<{ id: number, nazwa: string }[]>([])

const blad = ref('')
const sukces = ref('')
const ladowanie = ref(false)

const pesel = ref('')
const brak_peselu = ref(false)

const bledy = ref<Record<string, string>>({})

// Auto-formatowanie PESEL — tylko cyfry, max 11
watch(pesel, (val) => {
  pesel.value = val.replace(/\D/g, '').slice(0, 11)
})

// Auto-formatowanie telefonu — tylko cyfry/+, max 13 znaków
watch(telefon, (val) => {
  // Dozwolone: opcjonalne +48 na początku, potem 9 cyfr
  const cleaned = val.replace(/[^\d+]/g, '')
  telefon.value = cleaned.slice(0, 13)
})

// Auto-formatowanie NPWZ — tylko cyfry, max 7
watch(npwz, (val) => {
  npwz.value = val.replace(/\D/g, '').slice(0, 7)
})

// Gdy zaznaczy się "brak PESEL" — wyczyść pole i błąd
watch(brak_peselu, (val) => {
  if (val) {
    pesel.value = ''
    delete bledy.value.pesel
  }
})

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

const walidujPesel = (p: string): boolean => {
  if (!/^\d{11}$/.test(p)) return false
  const wagi = [1, 3, 7, 9, 1, 3, 7, 9, 1, 3]
  const suma = wagi.reduce((acc, w, i) => acc + w * parseInt(p.charAt(i), 10), 0)
  const kontrolna = (10 - (suma % 10)) % 10
  return kontrolna === parseInt(p.charAt(10), 10)
}

const walidujEmail = (e: string): boolean => {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e)
}

const walidujTelefon = (t: string): boolean => {
  // Akceptuje: 9 cyfr LUB +48 + 9 cyfr
  return /^(\+48)?\d{9}$/.test(t)
}

// Zwraca null jak OK, albo komunikat błędu
const walidujHaslo = (h: string): string | null => {
  if (!h) return 'Hasło jest wymagane'
  if (h.length < 12) return 'Hasło musi mieć co najmniej 12 znaków'
  if (!/[A-Z]/.test(h)) return 'Hasło musi zawierać wielką literę'
  if (!/[a-z]/.test(h)) return 'Hasło musi zawierać małą literę'
  if (!/\d/.test(h)) return 'Hasło musi zawierać cyfrę'
  if (!/[!@#$%^&*(),.?":{}|<>_\-]/.test(h)) return 'Hasło musi zawierać znak specjalny'
  return null
}

const waliduj = (): boolean => {
  bledy.value = {}

  // Email
  if (!email.value.trim()) {
    bledy.value.email = 'Email jest wymagany'
  } else if (!walidujEmail(email.value.trim())) {
    bledy.value.email = 'Nieprawidłowy format adresu email'
  }

  // Hasło
  const bladHasla = walidujHaslo(haslo.value)
  if (bladHasla) {
    bledy.value.haslo = bladHasla
  }

  // Imię
  if (!imie.value.trim()) {
    bledy.value.imie = 'Imię jest wymagane'
  } else if (imie.value.trim().length < 2) {
    bledy.value.imie = 'Imię musi mieć co najmniej 2 znaki'
  } else if (!/^[a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ\s-]+$/.test(imie.value)) {
    bledy.value.imie = 'Imię może zawierać tylko litery'
  }

  // Nazwisko
  if (!nazwisko.value.trim()) {
    bledy.value.nazwisko = 'Nazwisko jest wymagane'
  } else if (nazwisko.value.trim().length < 2) {
    bledy.value.nazwisko = 'Nazwisko musi mieć co najmniej 2 znaki'
  } else if (!/^[a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ\s-]+$/.test(nazwisko.value)) {
    bledy.value.nazwisko = 'Nazwisko może zawierać tylko litery'
  }

  // PESEL — TYLKO gdy nie zaznaczono "brak_peselu"
  if (!brak_peselu.value) {
    if (!pesel.value) {
      bledy.value.pesel = 'PESEL jest wymagany (lub zaznacz "lekarz zagraniczny")'
    } else if (pesel.value.length !== 11) {
      bledy.value.pesel = 'PESEL musi mieć dokładnie 11 cyfr'
    } else if (!walidujPesel(pesel.value)) {
      bledy.value.pesel = 'Nieprawidłowy PESEL — błędna cyfra kontrolna'
    }
  }

  //telefon
  if (!telefon.value) {
    bledy.value.telefon = 'Numer telefonu jest wymagany'
  } else if (!walidujTelefon(telefon.value)) {
    bledy.value.telefon = 'Podaj 9 cyfr lub numer z +48 (np. 123456789 lub +48123456789)'
  }

  // NPWZ — długość + regex
  if (!npwz.value) {
    bledy.value.npwz = 'NPWZ jest wymagany'
  } else if (!/^\d{7}$/.test(npwz.value)) {
    bledy.value.npwz = 'NPWZ musi składać się z dokładnie 7 cyfr'
  }

  // Status NPWZ — zabezpieczenie przed manipulacją DOM
  if (!['aktywny', 'zawieszony', 'wygasły'].includes(status_npwz.value)) {
    bledy.value.status_npwz = 'Nieprawidłowy status NPWZ'
  }

  // Ważność OC — wymagana i w przyszłości
  if (!waznosc_oc.value) {
    bledy.value.waznosc_oc = 'Data ważności OC jest wymagana'
  } else {
    const dataOc = new Date(waznosc_oc.value)
    const dzis = new Date()
    dzis.setHours(0, 0, 0, 0)
    if (dataOc <= dzis) {
      bledy.value.waznosc_oc = 'Data ważności OC musi być w przyszłości'
    }
  }

  // Placówka — wybrana
  if (!placowka_id.value) {
    bledy.value.placowka_id = 'Wybierz placówkę'
  }

  // Specjalizacje — min. 1
  if (wybrane_specjalizacje.value.length === 0) {
    bledy.value.specjalizacje = 'Wybierz co najmniej jedną specjalizację'
  }

  return Object.keys(bledy.value).length === 0
}

const handleSubmit = async () => {
  blad.value = ''
  sukces.value = ''

  if (!waliduj()) {
    blad.value = 'Popraw błędy w formularzu przed zapisaniem.'
    return
  }

  ladowanie.value = true

  try {
    await axios.post('/api/admin/add-doctor', {
      email: email.value.trim().toLowerCase(),
      haslo: haslo.value,
      imie: imie.value.trim(),
      nazwisko: nazwisko.value.trim(),
      pesel: brak_peselu.value ? null : pesel.value,
      brak_peselu: brak_peselu.value,
      npwz: npwz.value,
      status_npwz: status_npwz.value,
      waznosc_oc: waznosc_oc.value,
      placowka_id: placowka_id.value,
      telefon: telefon.value,
      specjalizacje_ids: wybrane_specjalizacje.value,
    })

    sukces.value = 'Lekarz został dodany pomyślnie!'
    // Wyczyść formularz
    email.value = ''
    haslo.value = ''
    imie.value = ''
    nazwisko.value = ''
    pesel.value = ''
    brak_peselu.value = false
    npwz.value = ''
    status_npwz.value = 'aktywny'
    waznosc_oc.value = ''
    placowka_id.value = null
    telefon.value = ''
    wybrane_specjalizacje.value = []
    bledy.value = {}

  } catch (error: any) {
    if (error.response?.status === 409) {
      blad.value = error.response.data.detail
    } else if (error.response?.status === 403) {
      blad.value = 'Brak uprawnień.'
    } else if (error.response?.status === 422) {
      // Błąd walidacji z backendu (Pydantic)
      const detail = error.response.data.detail
      if (Array.isArray(detail) && detail.length > 0) {
        blad.value = detail[0].msg || 'Błąd walidacji danych'
      } else {
        blad.value = typeof detail === 'string' ? detail : 'Błąd walidacji danych'
      }
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
          <input
            v-model="email"
            type="email"
            placeholder="lekarz@medisync.pl"
            :class="{ 'input-error': bledy.email }"
          />
          <span v-if="bledy.email" class="field-error">{{ bledy.email }}</span>
        </div>

        <div class="form-group">
          <label>Hasło *</label>
          <input
            v-model="haslo"
            type="password"
            placeholder="Min. 12 znaków"
            :class="{ 'input-error': bledy.haslo }"
          />
          <span v-if="bledy.haslo" class="field-error">{{ bledy.haslo }}</span>
        </div>

        <div class="section-title full">Dane osobowe</div>

        <div class="form-group">
          <label>Imię *</label>
          <input
            v-model="imie"
            type="text"
            placeholder="Jan"
            :class="{ 'input-error': bledy.imie }"
          />
          <span v-if="bledy.imie" class="field-error">{{ bledy.imie }}</span>
        </div>

        <div class="form-group">
          <label>Nazwisko *</label>
          <input
            v-model="nazwisko"
            type="text"
            placeholder="Kowalski"
            :class="{ 'input-error': bledy.nazwisko }"
          />
          <span v-if="bledy.nazwisko" class="field-error">{{ bledy.nazwisko }}</span>
        </div>

        <div class="form-group">
          <label>Numer telefonu *</label>
          <input v-model="telefon"
            type="tel"
            placeholder="123456789 lub +48123456789"
            :class="{ 'input-error': bledy.telefon }"
          />
          <span v-if="bledy.telefon" class="field-error">{{ bledy.telefon }}</span>
        </div>

        <div class="form-group">
          <label>PESEL <span class="hint">(11 cyfr)</span></label>
          <input
            v-model="pesel"
            type="text"
            maxlength="11"
            placeholder="12345678901"
            :disabled="brak_peselu"
            :class="{ 'input-disabled': brak_peselu, 'input-error': bledy.pesel }"
          />
          <span v-if="bledy.pesel" class="field-error">{{ bledy.pesel }}</span>
          <label class="checkbox-label">
            <input type="checkbox" v-model="brak_peselu" />
             Lekarz zagraniczny — brak numeru PESEL
          </label>
        </div>

        <div class="section-title full">Dane zawodowe</div>

        <div class="form-group">
          <label>NPWZ * <span class="hint">(7 cyfr)</span></label>
          <input
            v-model="npwz"
            type="text"
            maxlength="7"
            placeholder="1234567"
            :class="{ 'input-error': bledy.npwz }"
          />
          <span v-if="bledy.npwz" class="field-error">{{ bledy.npwz }}</span>
        </div>

        <div class="form-group">
          <label>Status NPWZ *</label>
          <select v-model="status_npwz" :class="{ 'input-error': bledy.status_npwz }">
            <option value="aktywny">Aktywny</option>
            <option value="zawieszony">Zawieszony</option>
            <option value="wygasły">Wygasły</option>
          </select>
          <span v-if="bledy.status_npwz" class="field-error">{{ bledy.status_npwz }}</span>
        </div>

        <div class="form-group">
          <label>Ważność OC *</label>
          <input
            v-model="waznosc_oc"
            type="date"
            :class="{ 'input-error': bledy.waznosc_oc }"
          />
          <span v-if="bledy.waznosc_oc" class="field-error">{{ bledy.waznosc_oc }}</span>
        </div>

        <div class="form-group">
          <label>Placówka *</label>
          <select v-model="placowka_id" :class="{ 'input-error': bledy.placowka_id }">
            <option :value="null" disabled>Wybierz placówkę</option>
            <option v-for="p in placowki" :key="p.id" :value="p.id">
              {{ p.nazwa }}
            </option>
          </select>
          <span v-if="bledy.placowka_id" class="field-error">{{ bledy.placowka_id }}</span>
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
        <span v-if="bledy.specjalizacje" class="field-error full">{{ bledy.specjalizacje }}</span>
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

.input-error {
  border-color: #ef4444 !important;
}

.field-error {
  display: block;
  color: #ef4444;
  font-size: 12px;
  margin-top: 4px;
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

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #475569;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  width: 16px;
  height: 16px;
  accent-color: #3b82f6;
  cursor: pointer;
}

.input-disabled {
  background: #f1f5f9 !important;
  color: #94a3b8 !important;
  cursor: not-allowed !important;
}

.btn-primary:hover:not(:disabled) { background-color: #2563eb; }
.btn-primary:disabled { background-color: #93c5fd; cursor: not-allowed; }
</style>