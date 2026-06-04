<script setup lang="ts">
import { ref } from 'vue'
import axios from 'axios'

const szukaj = ref('')
const ladowanie = ref(false)
const blad = ref('')
const wyniki = ref<any[]>([])
const wybranyPacjent = ref<any>(null)

const szukajPacjenta = async () => {
  if (szukaj.value.trim().length < 2) return
  ladowanie.value = true
  blad.value = ''
  wybranyPacjent.value = null
  try {
    const res = await axios.get('/api/lekarz/pacjent', { params: { q: szukaj.value } })
    wyniki.value = res.data.pacjenci
  } catch {
    blad.value = 'Błąd podczas wyszukiwania.'
  } finally {
    ladowanie.value = false
  }
}

const wybierzPacjenta = (p: any) => {
  wybranyPacjent.value = p
  wyniki.value = []
}
</script>

<template>
  <div class="page">
    <h1 class="page-title">Kartoteka pacjenta</h1>

    <div class="szukaj-row">
      <input
        v-model="szukaj"
        type="text"
        placeholder="Wpisz imię, nazwisko lub PESEL..."
        class="szukaj-input"
        @keyup.enter="szukajPacjenta"
      />
      <button @click="szukajPacjenta" class="btn-primary" :disabled="ladowanie">
        {{ ladowanie ? 'Szukam...' : 'Szukaj' }}
      </button>
    </div>

    <div v-if="blad" class="error-box">{{ blad }}</div>

    <!-- Wyniki wyszukiwania -->
    <div v-if="wyniki.length > 0" class="wyniki-lista">
      <div
        v-for="p in wyniki"
        :key="p.id"
        class="wynik-row"
        @click="wybierzPacjenta(p)"
      >
        <div class="wynik-info">
          <span class="wynik-nazwa">{{ p.imie }} {{ p.nazwisko }}</span>
          <span class="wynik-pesel">PESEL: {{ p.pesel }}</span>
        </div>
        <span class="wynik-arrow">→</span>
      </div>
    </div>

    <div v-else-if="!ladowanie && szukaj && wyniki.length === 0 && !wybranyPacjent" class="empty">
      Brak wyników dla "{{ szukaj }}".
    </div>

    <!-- Kartoteka wybranego pacjenta -->
    <div v-if="wybranyPacjent" class="kartoteka">
      <div class="karta-naglowek">
        <div>
          <h2>{{ wybranyPacjent.imie }} {{ wybranyPacjent.nazwisko }}</h2>
          <p class="pesel-text">PESEL: {{ wybranyPacjent.pesel }}</p>
        </div>
        <button @click="wybranyPacjent = null" class="btn-zamknij">✕</button>
      </div>

      <div class="karta-grid">
        <div class="karta-sekcja">
          <div class="sekcja-tytul">Dane kontaktowe</div>
          <div class="karta-row">
            <span class="karta-label">Telefon</span>
            <span class="karta-value">{{ wybranyPacjent.telefon ?? '—' }}</span>
          </div>
        </div>

        <div class="karta-sekcja">
          <div class="sekcja-tytul">Adres zamieszkania</div>
          <div class="karta-row">
            <span class="karta-label">Miejscowość</span>
            <span class="karta-value">{{ wybranyPacjent.adres?.miejscowosc ?? '—' }}</span>
          </div>
          <div class="karta-row">
            <span class="karta-label">Kod pocztowy</span>
            <span class="karta-value">{{ wybranyPacjent.adres?.kod_pocztowy ?? '—' }}</span>
          </div>
          <div class="karta-row">
            <span class="karta-label">Ulica</span>
            <span class="karta-value">
              {{ wybranyPacjent.adres?.ulica
                ? `${wybranyPacjent.adres.ulica} ${wybranyPacjent.adres.nr_domu}`
                : '—' }}
              {{ wybranyPacjent.adres?.nr_lokalu ? `/ ${wybranyPacjent.adres.nr_lokalu}` : '' }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page { padding: 32px; max-width: 800px; }
.page-title { font-size: 24px; font-weight: 700; color: #1e293b; margin: 0 0 24px 0; }

.szukaj-row { display: flex; gap: 12px; margin-bottom: 20px; }
.szukaj-input {
  flex: 1; padding: 12px 16px;
  border: 1px solid #e2e8f0; border-radius: 10px;
  font-size: 14px;
}
.szukaj-input:focus { outline: none; border-color: #3b82f6; }

.btn-primary {
  padding: 12px 24px; background: #3b82f6; color: white;
  border: none; border-radius: 10px; font-weight: 600;
  font-size: 14px; cursor: pointer; transition: 0.2s; white-space: nowrap;
}
.btn-primary:hover:not(:disabled) { background: #2563eb; }
.btn-primary:disabled { background: #93c5fd; cursor: not-allowed; }

.error-box { background: #fee2e2; color: #dc2626; padding: 12px 16px; border-radius: 8px; margin-bottom: 16px; }

.wyniki-lista {
  background: white; border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  overflow: hidden; margin-bottom: 16px;
}

.wynik-row {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 20px; cursor: pointer; transition: 0.15s;
  border-bottom: 1px solid #f1f5f9;
}
.wynik-row:last-child { border-bottom: none; }
.wynik-row:hover { background: #f0f7ff; }

.wynik-info { display: flex; flex-direction: column; }
.wynik-nazwa { font-size: 14px; font-weight: 600; color: #1e293b; }
.wynik-pesel { font-size: 12px; color: #94a3b8; margin-top: 2px; }
.wynik-arrow { color: #cbd5e1; }

.empty { color: #94a3b8; font-size: 14px; padding: 20px 0; }

.kartoteka {
  background: white; border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06); overflow: hidden;
}

.karta-naglowek {
  display: flex; justify-content: space-between; align-items: flex-start;
  padding: 24px; border-bottom: 1px solid #e2e8f0;
}
.karta-naglowek h2 { font-size: 20px; font-weight: 700; color: #1e293b; margin: 0; }
.pesel-text { color: #64748b; font-size: 14px; margin: 4px 0 0 0; }

.btn-zamknij {
  background: #f1f5f9; border: none; border-radius: 6px;
  padding: 6px 12px; cursor: pointer; font-size: 14px; color: #64748b;
}
.btn-zamknij:hover { background: #e2e8f0; }

.karta-grid { display: grid; grid-template-columns: 1fr 1fr; padding: 24px; gap: 24px; }

.karta-sekcja { display: flex; flex-direction: column; gap: 12px; }
.sekcja-tytul {
  font-size: 11px; font-weight: 700; color: #94a3b8;
  text-transform: uppercase; letter-spacing: 0.08em;
  padding-bottom: 8px; border-bottom: 1px solid #f1f5f9;
}

.karta-row { display: flex; flex-direction: column; gap: 2px; }
.karta-label { font-size: 12px; color: #94a3b8; font-weight: 600; }
.karta-value { font-size: 14px; color: #1e293b; font-weight: 500; }
</style>