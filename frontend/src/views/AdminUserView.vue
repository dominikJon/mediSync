<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const userId = Number(route.params.id)

const uzytkownik = ref<any>(null)
const specjalizacje = ref<{ id: number; nazwa: string }[]>([])
const placowki = ref<{ id: number; nazwa: string }[]>([])
const ladowanie = ref(true)
const zapisywanie = ref(false)
const resetowanie = ref(false)                                                    
const blad = ref('')
const sukces = ref('')

const ROLE = ['admin', 'lekarz', 'pracownik', 'pacjent']

// Edytowalne pola
const wybrana_rola = ref('')
const telefon = ref('')
const miejscowosc = ref('')
const kod_pocztowy = ref('')
const ulica = ref('')
const nr_domu = ref('')
const nr_lokalu = ref('')
const status_npwz = ref('')
const waznosc_oc = ref('')
const placowka_id = ref<number | null>(null)
const wybrane_specjalizacje = ref<number[]>([])

const pobierzDane = async () => {
  try {
    const [userRes, specRes, placRes] = await Promise.all([
      axios.get(`/api/admin/user/${userId}`),
      axios.get('/api/admin/specjalizacje'),
      axios.get('/api/admin/placowki'),
    ])

    uzytkownik.value = userRes.data
    specjalizacje.value = specRes.data.specjalizacje
    placowki.value = placRes.data.placowki

    // Wypełnij pola
    wybrana_rola.value = uzytkownik.value.rola
    const p = uzytkownik.value.profil

    if (p) {
      telefon.value = p.telefon || ''
      miejscowosc.value = p.miejscowosc || ''
      kod_pocztowy.value = p.kod_pocztowy || ''
      ulica.value = p.ulica || ''
      nr_domu.value = p.nr_domu || ''
      nr_lokalu.value = p.nr_lokalu || ''
      status_npwz.value = p.status_npwz || ''
      waznosc_oc.value = p.waznosc_oc || ''
      placowka_id.value = p.placowka_id || null
      wybrane_specjalizacje.value = p.specjalizacje?.map((s: any) => s.id) || []
    }
  } catch {
    blad.value = 'Błąd podczas pobierania danych użytkownika.'
  } finally {
    ladowanie.value = false
  }
}

const toggleSpecjalizacja = (id: number) => {
  const idx = wybrane_specjalizacje.value.indexOf(id)
  if (idx === -1) wybrane_specjalizacje.value.push(id)
  else wybrane_specjalizacje.value.splice(idx, 1)
}

const zapiszZmiany = async () => {
  blad.value = ''
  sukces.value = ''
  zapisywanie.value = true

  try {
    await axios.put(`/api/admin/user/${userId}`, {
      rola: wybrana_rola.value,
      telefon: telefon.value || null,
      miejscowosc: miejscowosc.value || null,
      kod_pocztowy: kod_pocztowy.value || null,
      ulica: ulica.value || null,
      nr_domu: nr_domu.value || null,
      nr_lokalu: nr_lokalu.value || null,
      status_npwz: status_npwz.value || null,
      waznosc_oc: waznosc_oc.value || null,
      placowka_id: placowka_id.value,
      specjalizacje_ids: wybrane_specjalizacje.value,
    })
    sukces.value = 'Zmiany zostały zapisane.'
    await pobierzDane()
  } catch {
    blad.value = 'Błąd podczas zapisywania zmian.'
  } finally {
    zapisywanie.value = false
  }
}

const resetujHaslo = async () => {
  if (!confirm(`Czy na pewno chcesz zresetować hasło użytkownika ${uzytkownik.value?.email}?`))
    return

  blad.value = ''
  sukces.value = ''
  resetowanie.value = true

  try {
    await axios.post('/api/forgot-password', { email: uzytkownik.value.email })
    sukces.value = 'Link do resetowania hasła został wysłany na adres email użytkownika.'
  } catch {
    blad.value = 'Błąd podczas wysyłania linku resetującego.'
  } finally {
    resetowanie.value = false
  }
}

onMounted(pobierzDane)
</script>

<template>
  <div class="page">
    <div class="page-header">
      <RouterLink to="/admin/users" class="btn-back">← Wróć do listy</RouterLink>
      <h1>Szczegóły użytkownika</h1>
    </div>

    <div v-if="ladowanie" class="loading">Ładowanie...</div>

    <template v-else-if="uzytkownik">
      <div v-if="blad" class="error-box">{{ blad }}</div>
      <div v-if="sukces" class="sukces-box">{{ sukces }}</div>

      <!-- Dane podstawowe -->
      <div class="card">
        <div class="card-title">Dane konta</div>
        <div class="info-grid">
          <div class="info-row">
            <span class="info-label">Email</span>
            <span class="info-value">{{ uzytkownik.email }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">ID</span>
            <span class="info-value muted">#{{ uzytkownik.id }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">Kartoteka</span>
            <span :class="uzytkownik.profil_uzupelniony ? 'status-ok' : 'status-brak'">
              {{ uzytkownik.profil_uzupelniony ? '✓ Uzupełniona' : '✗ Brak' }}
            </span>
          </div>
          <div class="info-row">
            <span class="info-label">Tymczasowe hasło</span>
            <span :class="uzytkownik.tymczasowe_haslo ? 'status-brak' : 'status-ok'">
              {{ uzytkownik.tymczasowe_haslo ? '⚠ Tak — użytkownik powinien zmienić hasło' : 'Nie' }}
            </span>
          </div>
        </div>
      </div>

      <!-- Zmiana roli -->
      <div v-if="uzytkownik.rola === 'pracownik'" class="card">
        <div class="card-title">Rola użytkownika</div>
        <div class="form-group">
        <label>Aktualna rola</label>
        <select v-model="wybrana_rola">
        <option value="pracownik">pracownik</option>
        <option value="admin">admin</option>
        </select>
        <p class="hint-text">⚠ Zmiana roli nie przenosi danych profilu między tabelami.</p>
    </div>
    </div>

      <!-- Profil pacjenta -->
      <div v-if="uzytkownik.rola === 'pacjent'" class="card">
        <div class="card-title">Dane pacjenta</div>
        <div class="form-grid">
          <div class="form-group">
            <label>Imię</label>
            <input :value="uzytkownik.profil?.imie" disabled class="input-disabled" />
          </div>
          <div class="form-group">
            <label>Nazwisko</label>
            <input :value="uzytkownik.profil?.nazwisko" disabled class="input-disabled" />
          </div>
          <div class="form-group">
            <label>PESEL</label>
            <input :value="uzytkownik.profil?.pesel" disabled class="input-disabled" />
          </div>
          <div class="form-group">
            <label>Telefon</label>
            <input v-model="telefon" type="text" placeholder="np. 600200300" />
          </div>

          <div class="section-title full">Adres zamieszkania</div>

          <div class="form-group">
            <label>Miejscowość</label>
            <input v-model="miejscowosc" type="text" />
          </div>
          <div class="form-group">
            <label>Kod pocztowy</label>
            <input v-model="kod_pocztowy" type="text" placeholder="00-000" />
          </div>
          <div class="form-group">
            <label>Ulica</label>
            <input v-model="ulica" type="text" />
          </div>
          <div class="form-group">
            <label>Nr domu</label>
            <input v-model="nr_domu" type="text" />
          </div>
          <div class="form-group">
            <label>Nr lokalu</label>
            <input v-model="nr_lokalu" type="text" />
          </div>
        </div>
      </div>

      <!-- Profil lekarza -->
      <div v-else-if="uzytkownik.rola === 'lekarz'" class="card">
        <div class="card-title">Dane lekarza</div>
        <div class="form-grid">
          <div class="form-group">
            <label>Imię</label>
            <input :value="uzytkownik.profil?.imie" disabled class="input-disabled" />
          </div>
          <div class="form-group">
            <label>Nazwisko</label>
            <input :value="uzytkownik.profil?.nazwisko" disabled class="input-disabled" />
          </div>
          <div class="form-group">
            <label>NPWZ</label>
            <input :value="uzytkownik.profil?.npwz" disabled class="input-disabled" />
          </div>
          <div class="form-group">
            <label>PESEL</label>
            <input :value="uzytkownik.profil?.pesel ?? 'Brak (lekarz zagraniczny)'" disabled class="input-disabled" />
          </div>
          <div class="form-group">
            <label>Status NPWZ</label>
            <select v-model="status_npwz">
              <option value="aktywny">Aktywny</option>
              <option value="zawieszony">Zawieszony</option>
              <option value="wygasły">Wygasły</option>
            </select>
          </div>
          <div class="form-group">
            <label>Ważność OC</label>
            <input v-model="waznosc_oc" type="date" />
          </div>
          <div class="form-group full">
            <label>Placówka</label>
            <select v-model="placowka_id">
              <option v-for="p in placowki" :key="p.id" :value="p.id">{{ p.nazwa }}</option>
            </select>
          </div>

          <div class="section-title full">Specjalizacje</div>
          <div class="specjalizacje-grid full">
            <div
              v-for="s in specjalizacje"
              :key="s.id"
              :class="['spec-chip', { aktywna: wybrane_specjalizacje.includes(s.id) }]"
              @click="toggleSpecjalizacja(s.id)"
            >
              {{ s.nazwa }}
            </div>
          </div>
        </div>
      </div>

      <!-- Profil pracownika -->
      <div v-else-if="uzytkownik.rola === 'pracownik'" class="card">
        <div class="card-title">Dane pracownika</div>
        <div class="form-grid">
          <div class="form-group">
            <label>Imię</label>
            <input :value="uzytkownik.profil?.imie" disabled class="input-disabled" />
          </div>
          <div class="form-group">
            <label>Nazwisko</label>
            <input :value="uzytkownik.profil?.nazwisko" disabled class="input-disabled" />
          </div>
          <div class="form-group">
            <label>PESEL</label>
            <input :value="uzytkownik.profil?.pesel" disabled class="input-disabled" />
          </div>
          <div class="form-group">
            <label>Telefon</label>
            <input v-model="telefon" type="text" placeholder="np. 500100200" />
          </div>
        </div>
      </div>

      <!-- Akcje -->
      <div class="card akcje-card">
        <div class="card-title">Akcje</div>
        <div class="akcje-row">
          <button @click="zapiszZmiany" class="btn-primary" :disabled="zapisywanie">
            {{ zapisywanie ? 'Zapisywanie...' : 'Zapisz zmiany' }}
          </button>
          <button @click="resetujHaslo" class="btn-danger" :disabled="resetowanie">
            {{ resetowanie ? 'Wysyłanie...' : '🔑 Resetuj hasło' }}
          </button>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.page { padding: 32px; max-width: 800px; }

.page-header { margin-bottom: 24px; }
.page-header h1 { font-size: 24px; font-weight: 700; color: #1e293b; margin: 8px 0 0 0; }

.btn-back { color: #64748b; text-decoration: none; font-size: 14px; font-weight: 600; }
.btn-back:hover { color: #3b82f6; }

.loading { color: #64748b; padding: 20px; }

.error-box {
  background: #fee2e2; color: #dc2626;
  padding: 12px 16px; border-radius: 8px; margin-bottom: 16px; font-size: 14px;
}
.sukces-box {
  background: #dcfce7; color: #166534;
  padding: 12px 16px; border-radius: 8px; margin-bottom: 16px;
  font-size: 14px; font-weight: 600;
}

.card {
  background: white; border-radius: 12px;
  padding: 24px; box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  margin-bottom: 16px;
}

.card-title {
  font-size: 13px; font-weight: 700; color: #64748b;
  text-transform: uppercase; letter-spacing: 0.05em;
  padding-bottom: 16px; border-bottom: 1px solid #e2e8f0;
  margin-bottom: 16px;
}

.info-grid { display: flex; flex-direction: column; gap: 12px; }
.info-row { display: flex; justify-content: space-between; align-items: center; }
.info-label { font-size: 13px; color: #64748b; font-weight: 600; }
.info-value { font-size: 14px; color: #1e293b; }
.muted { color: #94a3b8; }

.status-ok { color: #16a34a; font-weight: 600; font-size: 13px; }
.status-brak { color: #dc2626; font-weight: 600; font-size: 13px; }

.form-grid {
  display: grid; grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.full { grid-column: span 2; }

.section-title {
  font-size: 12px; font-weight: 700; color: #94a3b8;
  text-transform: uppercase; letter-spacing: 0.05em;
  padding-bottom: 6px; border-bottom: 1px solid #f1f5f9;
  margin-top: 4px;
}

.form-group label {
  display: block; font-size: 13px;
  font-weight: 600; color: #475569; margin-bottom: 6px;
}

.hint-text { font-size: 12px; color: #f59e0b; margin-top: 6px; }

.form-group input,
.form-group select {
  width: 100%; padding: 10px 12px;
  border: 1px solid #cbd5e1; border-radius: 8px;
  box-sizing: border-box; font-size: 14px; color: #1e293b;
  background: white;
}

.form-group input:focus,
.form-group select:focus {
  outline: none; border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59,130,246,0.1);
}

.input-disabled {
  background: #f8fafc !important;
  color: #94a3b8 !important;
  cursor: not-allowed;
}

.specjalizacje-grid { display: flex; flex-wrap: wrap; gap: 8px; }

.spec-chip {
  padding: 8px 14px; border-radius: 20px;
  border: 2px solid #e2e8f0; background: #f8fafc;
  color: #475569; font-size: 13px; font-weight: 600;
  cursor: pointer; transition: all 0.15s; user-select: none;
}
.spec-chip:hover { border-color: #3b82f6; color: #3b82f6; }
.spec-chip.aktywna { border-color: #3b82f6; background: #dbeafe; color: #1e40af; }


.akcje-row { display: flex; gap: 12px; }

.btn-primary {
  padding: 12px 24px; background-color: #3b82f6;
  color: white; border: none; border-radius: 8px;
  font-weight: 600; font-size: 14px; cursor: pointer; transition: 0.2s;
}
.btn-primary:hover:not(:disabled) { background-color: #2563eb; }
.btn-primary:disabled { background-color: #93c5fd; cursor: not-allowed; }

.btn-danger {
  padding: 12px 24px; background-color: #fee2e2;
  color: #dc2626; border: 1px solid #fecaca;
  border-radius: 8px; font-weight: 600;
  font-size: 14px; cursor: pointer; transition: 0.2s;
}
.btn-danger:hover:not(:disabled) { background-color: #fecaca; }
.btn-danger:disabled { opacity: 0.6; cursor: not-allowed; }
</style>