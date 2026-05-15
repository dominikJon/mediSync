<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import axios from 'axios'

const router = useRouter()
const authStore = useAuthStore()

// Zmienne formularza 
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

// UX: Jeśli ktoś zaznaczy "brak ulicy", czyścimy pole ulicy
watch(brak_ulicy, (nowaWartosc) => {
  if (nowaWartosc) {
    ulica.value = ''
  }
})

const handleSaveProfile = async () => {
  blad.value = ''

  if (!imie.value || !nazwisko.value || !pesel.value || !telefon.value || !miejscowosc.value || !kod_pocztowy.value || !nr_domu.value) {
    blad.value = 'Wypełnij wszystkie pola oznaczone gwiazdką (*)!'
    return
  }

  if (pesel.value.length !== 11) {
    blad.value = 'PESEL musi mieć dokładnie 11 cyfr.'
    return
  }

  if (!/^\d{2}-\d{3}$/.test(kod_pocztowy.value)) {
    blad.value = 'Kod pocztowy musi być w formacie XX-XXX (np. 00-001).'
    return
  }

  if (!brak_ulicy.value && !ulica.value) {
    blad.value = 'Podaj ulicę lub zaznacz "Brak nazwy ulicy".'
    return
  }

  ladowanie.value = true

  try {
    const payload = {
      uzytkownik_id: authStore.user?.id,  // ← id z Pinia store
      imie: imie.value,
      nazwisko: nazwisko.value,
      pesel: pesel.value,
      telefon: telefon.value,
      miejscowosc: miejscowosc.value,
      kod_pocztowy: kod_pocztowy.value,
      ulica: brak_ulicy.value ? null : ulica.value,
      nr_domu: nr_domu.value,
      nr_lokalu: nr_lokalu.value === '' ? null : nr_lokalu.value,
      brak_ulicy: brak_ulicy.value
    }

    await axios.post('/api/complete-profile', payload)

    // Zaktualizuj store — profil uzupełniony
    if (authStore.user) {
      authStore.user.imie = imie.value           // imie 
      authStore.user.nazwisko = nazwisko.value   // nazwisko
      authStore.user.profil_uzupelniony = true

      localStorage.setItem('user_data', JSON.stringify(authStore.user)) //aktualizacja danych uzytkownika w localstorage
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

      <div v-if="blad" class="error-box">
        {{ blad }}
      </div>

      <div class="form-grid">
        <div class="section-title full-width">Dane osobowe</div>
        
        <div class="form-group">
          <label>Imię *</label>
          <input v-model="imie" type="text" placeholder="Jan" />
        </div>
        <div class="form-group">
          <label>Nazwisko *</label>
          <input v-model="nazwisko" type="text" placeholder="Kowalski" />
        </div>
        <div class="form-group">
          <label>Numer PESEL *</label>
          <input v-model="pesel" type="text" maxlength="11" placeholder="11 cyfr" />
        </div>
        <div class="form-group">
          <label>Numer telefonu *</label>
          <input v-model="telefon" type="tel" placeholder="np. 123456789" />
        </div>

        <div class="section-title full-width">Adres zamieszkania</div>

        <div class="form-group">
          <label>Miejscowość *</label>
          <input v-model="miejscowosc" type="text" placeholder="Warszawa" />
        </div>
        <div class="form-group">
          <label>Kod pocztowy *</label>
          <input v-model="kod_pocztowy" type="text" placeholder="00-000" />
        </div>

        <div class="form-group full-width checkbox-container">
          <input type="checkbox" id="brak_ulicy" v-model="brak_ulicy" />
          <label for="brak_ulicy" class="checkbox-label">Brak nazwy ulicy w miejscowości</label>
        </div>

        <div class="form-group full-width" v-if="!brak_ulicy">
          <label>Ulica</label>
          <input v-model="ulica" type="text" placeholder="Wiosenna" />
        </div>

        <div class="form-group">
          <label>Numer domu *</label>
          <input v-model="nr_domu" type="text" placeholder="12" @keyup.enter="handleSaveProfile" />
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

.header {
  text-align: center;
  margin-bottom: 25px;
}

.header h2 {
  margin: 0 0 10px 0;
  font-size: 26px;
  color: #1e293b;
}

.header p {
  color: #64748b;
  font-size: 15px;
  line-height: 1.5;
  margin: 0;
}

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

.full-width {
  grid-column: span 2;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #0f172a;
  margin-top: 10px;
  padding-bottom: 5px;
  border-bottom: 1px solid #e2e8f0;
}

.form-group {
  text-align: left;
}

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

.checkbox-container {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 5px;
}

.checkbox-label {
  margin-bottom: 0 !important;
  cursor: pointer;
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

.btn-primary:hover:not(:disabled) {
  background-color: #2563eb;
}

.btn-primary:disabled {
  background-color: #93c5fd;
  cursor: not-allowed;
}

@media (max-width: 600px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
  .full-width {
    grid-column: span 1;
  }
}
</style>