<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import axios from 'axios'

const router = useRouter()
const authStore = useAuthStore()

const imie = ref('')
const nazwisko = ref('')
const pesel = ref('')
const telefon = ref('')
const miejscowosc = ref('')
const kod_pocztowy = ref('')
const ulica = ref('')
const nr_domu = ref('')
const nr_lokalu = ref('')
const brak_ulicy = ref(false)

const blad = ref('')
const ladowanie = ref(false)
const bledy = ref<Record<string, string>>({})

watch(brak_ulicy, (nowaWartosc) => {
  if (nowaWartosc) ulica.value = ''
})

// Auto-formatowanie kodu pocztowego: 12345 → 12-345
watch(kod_pocztowy, (val) => {
  const cyfry = val.replace(/\D/g, '').slice(0, 5)
  if (cyfry.length > 2) {
    kod_pocztowy.value = `${cyfry.slice(0, 2)}-${cyfry.slice(2)}`
  } else {
    kod_pocztowy.value = cyfry
  }
})

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

const walidujPesel = (p: string): boolean => {
  if (!/^\d{11}$/.test(p)) return false
  const wagi = [1, 3, 7, 9, 1, 3, 7, 9, 1, 3]
  
  //p.charAt(i)
  const suma = wagi.reduce((acc, w, i) => acc + w * parseInt(p.charAt(i), 10), 0)
  
  const kontrolna = (10 - (suma % 10)) % 10
  
  //p.charAt(10)
  return kontrolna === parseInt(p.charAt(10), 10)
}

const walidujTelefon = (t: string): boolean => {
  // Akceptuje: 9 cyfr LUB +48 + 9 cyfr
  return /^(\+48)?\d{9}$/.test(t.replace(/\s/g, ''))
}

const waliduj = (): boolean => {
  bledy.value = {}

  if (!imie.value.trim()) {
    bledy.value.imie = 'Imię jest wymagane'
  } else if (imie.value.trim().length < 2) {
    bledy.value.imie = 'Imię musi mieć co najmniej 2 znaki'
  } else if (!/^[a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ\s-]+$/.test(imie.value)) {
    bledy.value.imie = 'Imię może zawierać tylko litery'
  }

  if (!nazwisko.value.trim()) {
    bledy.value.nazwisko = 'Nazwisko jest wymagane'
  } else if (nazwisko.value.trim().length < 2) {
    bledy.value.nazwisko = 'Nazwisko musi mieć co najmniej 2 znaki'
  } else if (!/^[a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ\s-]+$/.test(nazwisko.value)) {
    bledy.value.nazwisko = 'Nazwisko może zawierać tylko litery'
  }

  if (!pesel.value) {
    bledy.value.pesel = 'PESEL jest wymagany'
  } else if (pesel.value.length !== 11) {
    bledy.value.pesel = 'PESEL musi mieć dokładnie 11 cyfr'
  } else if (!walidujPesel(pesel.value)) {
    bledy.value.pesel = 'Podany PESEL jest nieprawidłowy (błędna cyfra kontrolna)'
  }

  if (!telefon.value) {
    bledy.value.telefon = 'Numer telefonu jest wymagany'
  } else if (!walidujTelefon(telefon.value)) {
    bledy.value.telefon = 'Podaj 9 cyfr lub numer z +48 (np. 123456789 lub +48123456789)'
  }

  if (!miejscowosc.value.trim()) {
    bledy.value.miejscowosc = 'Miejscowość jest wymagana'
  } else if (miejscowosc.value.trim().length < 2) {
    bledy.value.miejscowosc = 'Podaj prawidłową miejscowość'
  }

  if (!kod_pocztowy.value) {
    bledy.value.kod_pocztowy = 'Kod pocztowy jest wymagany'
  } else if (!/^\d{2}-\d{3}$/.test(kod_pocztowy.value)) {
    bledy.value.kod_pocztowy = 'Format: XX-XXX (np. 34-600)'
  }

  if (!brak_ulicy.value && !ulica.value.trim()) {
    bledy.value.ulica = 'Podaj ulicę lub zaznacz "Brak nazwy ulicy"'
  }

  if (!nr_domu.value.trim()) {
    bledy.value.nr_domu = 'Numer domu jest wymagany'
  } else if (!/^[a-zA-Z0-9\-\/]+$/.test(nr_domu.value)) {
    bledy.value.nr_domu = 'Nieprawidłowy numer domu'
  }

  return Object.keys(bledy.value).length === 0
}

const handleSaveProfile = async () => {
  blad.value = ''
  if (!waliduj()) {
    blad.value = 'Popraw błędy w formularzu przed zapisaniem.'
    return
  }

  ladowanie.value = true

  try {
    const payload = {
      uzytkownik_id: authStore.user?.id,
      imie: imie.value.trim(),
      nazwisko: nazwisko.value.trim(),
      pesel: pesel.value,
      telefon: telefon.value.replace(/\s/g, ''),
      miejscowosc: miejscowosc.value.trim(),
      kod_pocztowy: kod_pocztowy.value,
      ulica: brak_ulicy.value ? null : ulica.value.trim(),
      nr_domu: nr_domu.value.trim(),
      nr_lokalu: nr_lokalu.value.trim() === '' ? null : nr_lokalu.value.trim(),
      brak_ulicy: brak_ulicy.value,
    }

    await axios.post('/api/complete-profile', payload)

    if (authStore.user) {
      authStore.user.imie = imie.value.trim()
      authStore.user.nazwisko = nazwisko.value.trim()
      authStore.user.profil_uzupelniony = true
      localStorage.setItem('user_data', JSON.stringify(authStore.user))
    }

    router.push('/')
  } catch (error: any) {
    if (error.response?.status === 409) {
      blad.value = 'Pacjent z tym numerem PESEL już istnieje.'
    } else if (error.response?.status === 422) {
      blad.value = error.response.data.detail
    } else {
      blad.value = 'Wystąpił błąd podczas zapisywania danych.'
    }
    console.error(error)
  } finally {
    ladowanie.value = false
  }
}
</script>

<template>
  <div class="profile-container">
    <div class="profile-card">
      <div class="header">
        <h2>Witaj w <span class="text-blue">Medi</span><span class="text-green">Sync</span></h2>
        <p>Założenie kartoteki wymaga podania szczegółowych danych pacjenta.</p>
      </div>

      <div v-if="blad" class="error-box">{{ blad }}</div>

      <div class="form-grid">
        <div class="section-title full-width">Dane osobowe</div>

        <div class="form-group">
          <label>Imię *</label>
          <input v-model="imie" type="text" placeholder="Jan" :class="{ 'input-error': bledy.imie }" />
          <span v-if="bledy.imie" class="field-error">{{ bledy.imie }}</span>
        </div>

        <div class="form-group">
          <label>Nazwisko *</label>
          <input v-model="nazwisko" type="text" placeholder="Kowalski" :class="{ 'input-error': bledy.nazwisko }" />
          <span v-if="bledy.nazwisko" class="field-error">{{ bledy.nazwisko }}</span>
        </div>

        <div class="form-group">
          <label>Numer PESEL *</label>
          <input v-model="pesel" type="text" maxlength="11" placeholder="11 cyfr" :class="{ 'input-error': bledy.pesel }" />
          <span v-if="bledy.pesel" class="field-error">{{ bledy.pesel }}</span>
        </div>

        <div class="form-group">
          <label>Numer telefonu *</label>
          <input v-model="telefon" type="tel" placeholder="123456789 lub +48123456789" :class="{ 'input-error': bledy.telefon }" />
          <span v-if="bledy.telefon" class="field-error">{{ bledy.telefon }}</span>
        </div>

        <div class="section-title full-width">Adres zamieszkania</div>

        <div class="form-group">
          <label>Miejscowość *</label>
          <input v-model="miejscowosc" type="text" placeholder="Warszawa" :class="{ 'input-error': bledy.miejscowosc }" />
          <span v-if="bledy.miejscowosc" class="field-error">{{ bledy.miejscowosc }}</span>
        </div>

        <div class="form-group">
          <label>Kod pocztowy *</label>
          <input v-model="kod_pocztowy" type="text" placeholder="00-000" maxlength="6" :class="{ 'input-error': bledy.kod_pocztowy }" />
          <span v-if="bledy.kod_pocztowy" class="field-error">{{ bledy.kod_pocztowy }}</span>
        </div>

        <div class="form-group full-width checkbox-container">
          <input type="checkbox" id="brak_ulicy" v-model="brak_ulicy" />
          <label for="brak_ulicy" class="checkbox-label">Brak nazwy ulicy w miejscowości</label>
        </div>

        <div class="form-group full-width" v-if="!brak_ulicy">
          <label>Ulica *</label>
          <input v-model="ulica" type="text" placeholder="Wiosenna" :class="{ 'input-error': bledy.ulica }" />
          <span v-if="bledy.ulica" class="field-error">{{ bledy.ulica }}</span>
        </div>

        <div class="form-group">
          <label>Numer domu *</label>
          <input v-model="nr_domu" type="text" placeholder="12A" :class="{ 'input-error': bledy.nr_domu }" />
          <span v-if="bledy.nr_domu" class="field-error">{{ bledy.nr_domu }}</span>
        </div>

        <div class="form-group">
          <label>Numer lokalu</label>
          <input v-model="nr_lokalu" type="text" placeholder="4 (opcjonalnie)" @keyup.enter="handleSaveProfile" />
        </div>
      </div>

      <button @click="handleSaveProfile" class="btn-primary" :disabled="ladowanie">
        {{ ladowanie ? 'Zapisywanie...' : 'Zapisz dane i stwórz kartotekę' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.profile-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f8fafc;
  padding: 20px;
}

.profile-card {
  background: white;
  padding: 40px;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.05);
  width: 100%;
  max-width: 650px;
}

.header { text-align: center; margin-bottom: 25px; }
.header h2 { margin: 0 0 10px 0; font-size: 26px; color: #1e293b; }
.header p { color: #64748b; font-size: 15px; line-height: 1.5; margin: 0; }

.text-blue { color: #0056b3; font-weight: bold; }
.text-green { color: #28a745; font-weight: bold; }

.error-box {
  background: #fee2e2;
  color: #dc2626;
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 20px;
  font-size: 14px;
  font-weight: 500;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 30px;
}

.full-width { grid-column: span 2; }

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #0f172a;
  margin-top: 10px;
  padding-bottom: 5px;
  border-bottom: 1px solid #e2e8f0;
}

.form-group { text-align: left; }

.form-group label {
  display: block;
  font-size: 13px;
  color: #475569;
  margin-bottom: 6px;
  font-weight: 600;
}

.form-group input[type="text"],
.form-group input[type="tel"] {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  box-sizing: border-box;
  font-size: 14px;
  color: #1e293b;
  transition: border-color 0.2s;
}

.form-group input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.input-error { border-color: #ef4444 !important; }

.field-error {
  display: block;
  color: #ef4444;
  font-size: 12px;
  margin-top: 4px;
}

.checkbox-container {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 5px;
}

.checkbox-label { margin-bottom: 0 !important; cursor: pointer; }

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

@media (max-width: 600px) {
  .form-grid { grid-template-columns: 1fr; }
  .full-width { grid-column: span 1; }
}
</style>