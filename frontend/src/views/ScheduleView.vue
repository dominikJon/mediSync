<template>
  <div class="page">
    <h1 class="page-title">Umów nową wizytę</h1>

    <div v-if="blad" class="error-box">
      {{ blad }}
      <button @click="blad = ''" class="close-btn">✕</button>
    </div>
    <div v-if="sukces" class="sukces-box">
      {{ sukces }}
      <RouterLink v-if="!czyRejestracja" to="/records" class="sukces-link">Przejdź do moich wizyt →</RouterLink>
      <button @click="sukces = ''" class="close-btn">✕</button>
    </div>

    <div class="schedule-layout">
      <div class="panel-left">

        <div class="card">
          <div class="card-title">
            <span class="step-badge">1</span>
            Wybierz lekarza
          </div>
          <div class="form-group">
            <label>Specjalizacja</label>
            <select v-model="wybranaSpecjalizacjaId" @change="pobierzLekarzy">
              <option :value="null">Wszyscy lekarze</option>
              <option v-for="spec in specjalizacje" :key="spec.id" :value="spec.id">
                {{ spec.nazwa }}
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>Lekarz</label>
            <select v-model="wybranyLekarzId" @change="resetujSloty" :disabled="isLoadingLekarze">
              <option :value="null" disabled>-- Wybierz z listy --</option>
              <option v-for="lekarz in lekarze" :key="lekarz.id" :value="lekarz.id">
                lek. {{ lekarz.imie }} {{ lekarz.nazwisko }}
              </option>
            </select>
            <div v-if="aktualnyLekarz" class="doctor-info-card">
              <div class="fw-bold">dr {{ aktualnyLekarz.imie }} {{ aktualnyLekarz.nazwisko }}</div>
              <div class="text-sm text-gray">
                {{ aktualnyLekarz.specjalizacje?.join(', ') || 'Lekarz ogólny' }}
              </div>
            </div>
          </div>
        </div>

        <div v-if="czyRejestracja" class="card">
          <div class="card-title">
            <span class="step-badge" style="background:#64748b">👤</span>
            Wybierz pacjenta
          </div>
          <div v-if="wybranyPacjent" class="doctor-info-card">
            <div class="fw-bold">{{ wybranyPacjent.imie }} {{ wybranyPacjent.nazwisko }}</div>
            <div class="text-sm text-gray">PESEL: {{ wybranyPacjent.pesel }}</div>
            <button @click="wybranyPacjent = null; wynikiSzukania = []" class="btn-sm-link">Zmień pacjenta</button>
          </div>
          <div v-else class="form-group">
            <label>Szukaj pacjenta (imię, nazwisko lub PESEL)</label>
            <input
              v-model="szukajPacjentaQuery"
              type="text"
              placeholder="np. Kowalski lub 44051401458"
              @input="szukajPacjenta"
            />
            <div v-if="wynikiSzukania.length > 0" class="search-results">
              <div
                v-for="p in wynikiSzukania"
                :key="p.id"
                class="search-result-item"
                @click="wybranyPacjent = p; wynikiSzukania = []"
              >
                <strong>{{ p.imie }} {{ p.nazwisko }}</strong>
                <span class="text-gray">{{ p.pesel }}</span>
              </div>
            </div>
            <div v-if="isSearching" class="text-gray text-sm mt-1">Szukam...</div>
          </div>
        </div>

        <div v-if="wybranyLekarzId" class="card">
          <div class="card-title">
            <span class="step-badge">2</span>
            Wybierz datę
          </div>
          <div class="form-group">
            <input type="date" v-model="wybranaData" @change="pobierzSloty" :min="dzisiejszaData" />
          </div>
        </div>

      </div>

      <div class="panel-right">
        <div v-if="!wybranyLekarzId || !wybranaData" class="empty-state">
          <span class="empty-icon">📅</span>
          <p>Wybierz lekarza i datę, aby zobaczyć wolne terminy.</p>
        </div>
        <div v-else class="card">
          <div class="card-title">
            <span class="step-badge">3</span>
            Dostępne godziny
          </div>
          <div v-if="isLoadingSloty" class="loading-state">
            Szukam terminów...
          </div>
          <div v-else-if="sloty.length === 0" class="brak-danych">
            😕 Brak wolnych terminów w wybranym dniu. Wybierz inną datę.
          </div>
          <div v-else>
            <div class="sloty-grid">
              <button
                v-for="slot in sloty"
                :key="slot.id"
                @click="wybranySlot = slot"
                :class="['slot-btn', { 'slot-btn--active': wybranySlot?.id === slot.id }]"
              >
                {{ formatujGodzine(slot.termin_od) }}
              </button>
            </div>
            <div v-if="wybranySlot" class="podsumowanie">
              <div class="podsumowanie-title">Podsumowanie wizyty</div>
              <div class="podsumowanie-row">
                <span class="podsumowanie-label">Lekarz</span>
                <span class="podsumowanie-value">dr {{ aktualnyLekarz?.imie }} {{ aktualnyLekarz?.nazwisko }}</span>
              </div>
              <div class="podsumowanie-row">
                <span class="podsumowanie-label">Specjalizacja</span>
                <span class="podsumowanie-value">{{ aktualnyLekarz?.specjalizacje?.join(', ') || '-' }}</span>
              </div>
              <div class="podsumowanie-row">
                <span class="podsumowanie-label">Data</span>
                <span class="podsumowanie-value">{{ wybranaData }}</span>
              </div>
              <div class="podsumowanie-row">
                <span class="podsumowanie-label">Godzina</span>
                <span class="podsumowanie-value">{{ formatujGodzine(wybranySlot.termin_od) }}</span>
              </div>
              <div class="podsumowanie-row">
                <span class="podsumowanie-label">Gabinet</span>
                <span class="podsumowanie-value">{{ wybranySlot.gabinet_numer }}</span>
              </div>
              <div class="podsumowanie-row">
                <span class="podsumowanie-label">Cena</span>
                <span class="podsumowanie-value">
                  {{ wybranySlot.cena ? wybranySlot.cena.toFixed(2) + ' zł' : 'Zgodnie z cennikiem' }}
                </span>
              </div>

              <button
                @click="zarezerwujWizyte"
                :disabled="isBooking"
                class="btn-primary btn-full"
                style="margin-top: 16px;"
              >
                {{ isBooking ? 'Trwa rezerwacja...' : 'Potwierdź i zarezerwuj' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import axios from 'axios';
import { useAuthStore } from '../stores/auth';

// interfejsy
interface Specjalizacja { id: number; nazwa: string; }
interface Lekarz { id: number; imie: string; nazwisko: string; specjalizacje: string[]; }
interface Slot { id: number; termin_od: string; termin_do: string; gabinet_numer: string; cena: number; }
interface Pacjent { id: number; imie: string; nazwisko: string; pesel: string; }

// store (pinia) i rola uzytkownika
const authStore = useAuthStore();
const czyRejestracja = computed(() => ['rejestracja', 'admin'].includes(authStore.user?.rola || ''));

// stany
const specjalizacje = ref<Specjalizacja[]>([]);
const lekarze = ref<Lekarz[]>([]);
const sloty = ref<Slot[]>([]);

const wybranaSpecjalizacjaId = ref<number | null>(null);
const wybranyLekarzId = ref<number | null>(null);
const wybranaData = ref<string>('');
const wybranySlot = ref<Slot | null>(null);

// stany - rejestracja pacjenta
const wybranyPacjent = ref<Pacjent | null>(null);
const szukajPacjentaQuery = ref('');
const wynikiSzukania = ref<Pacjent[]>([]);
const isSearching = ref(false);

const isLoadingLekarze = ref(false);
const isLoadingSloty = ref(false);
const isBooking = ref(false);

const blad = ref<string>('');
const sukces = ref<string>('');

const aktualnyLekarz = computed(() => lekarze.value.find(l => l.id === wybranyLekarzId.value));
const dzisiejszaData = computed(() => new Date().toISOString().split('T')[0]);

const formatujGodzine = (dataIso: string) => dataIso.substring(11, 16);

// metody
const szukajPacjenta = async () => {
  if (szukajPacjentaQuery.value.length < 2) {
    wynikiSzukania.value = [];
    return;
  }
  isSearching.value = true;
  try {
    const res = await axios.get(`/api/pacjenci/szukaj?q=${szukajPacjentaQuery.value}`);
    wynikiSzukania.value = res.data.pacjenci;
  } catch (error) {
    console.error("Błąd szukania pacjentów:", error);
  } finally {
    isSearching.value = false;
  }
};

const resetujSloty = () => {
  sloty.value = [];
  wybranySlot.value = null;
  blad.value = '';
  sukces.value = '';
  if (wybranaData.value) {
    pobierzSloty();
  }
};

const pobierzSpecjalizacje = async () => {
  try {
    const response = await axios.get('/api/specjalizacje/lista');
    specjalizacje.value = response.data.specjalizacje;
  } catch (error: any) {
    console.error("Błąd pobierania specjalizacji:", error);
  }
};

const pobierzLekarzy = async () => {
  isLoadingLekarze.value = true;
  wybranyLekarzId.value = null;
  resetujSloty();
  try {
    const url = wybranaSpecjalizacjaId.value
      ? `/api/lekarze/lista?specjalizacja_id=${wybranaSpecjalizacjaId.value}`
      : `/api/lekarze/lista`;
    const response = await axios.get(url);
    lekarze.value = response.data.lekarze;
  } catch (error: any) {
    console.error("Błąd pobierania lekarzy:", error);
  } finally {
    isLoadingLekarze.value = false;
  }
};

const pobierzSloty = async () => {
  if (!wybranyLekarzId.value || !wybranaData.value) return;
  isLoadingSloty.value = true;
  wybranySlot.value = null;
  blad.value = '';
  sukces.value = '';
  
  try {
    const response = await axios.get(`/api/wizyty/wolne-sloty?lekarz_id=${wybranyLekarzId.value}&data=${wybranaData.value}`);
    sloty.value = response.data.sloty;
  } catch (error: any) {
    blad.value = error.response?.data?.detail || "Wystąpił błąd przy pobieraniu terminów.";
  } finally {
    isLoadingSloty.value = false;
  }
};

const zarezerwujWizyte = async () => {
  if (!wybranySlot.value) return;
  
  if (czyRejestracja.value && !wybranyPacjent.value) {
    blad.value = 'Wybierz pacjenta przed rezerwacją.';
    return;
  }

  isBooking.value = true;
  blad.value = '';
  sukces.value = '';
  
  try {
    const payload = { 
      grafik_id: wybranySlot.value.id, 
      pacjent_id: czyRejestracja.value ? wybranyPacjent.value?.id : null 
    };
    await axios.post('/api/wizyty', payload);
    
    sukces.value = "Wizyta zarezerwowana!";
    wybranaData.value = '';
    sloty.value = [];
    wybranySlot.value = null;
    wybranyLekarzId.value = null;
    wybranyPacjent.value = null;
    szukajPacjentaQuery.value = '';
    
  } catch (error: any) {
    blad.value = error.response?.data?.detail || "Nie udało się zarezerwować wizyty. Spróbuj ponownie.";
    pobierzSloty();
  } finally {
    isBooking.value = false;
  }
};

onMounted(() => {
  pobierzSpecjalizacje();
  pobierzLekarzy();
});
</script>

<style scoped>
.page {
  padding: 32px;
  max-width: 1100px;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 24px 0;
}

.schedule-layout {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}

.panel-left {
  display: flex;
  flex-direction: column;
  gap: 20px;
  flex: 0 0 300px;
}

.panel-right {
  flex: 1;
  min-width: 0;
}

.card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.card-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  font-weight: 700;
  color: #1e293b;
  padding-bottom: 14px;
  border-bottom: 1px solid #e2e8f0;
  margin-bottom: 16px;
}

.step-badge {
  background: #3b82f6;
  color: white;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}

.form-group {
  display: flex;
  flex-direction: column;
  margin-bottom: 14px;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-group label {
  font-size: 13px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 6px;
}

.form-group select,
.form-group input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  box-sizing: border-box;
  font-size: 14px;
  color: #1e293b;
  background: white;
  font-family: inherit;
}

.form-group select:focus,
.form-group input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-group select:disabled {
  background: #f1f5f9;
  color: #94a3b8;
  cursor: not-allowed;
}

.empty-state {
  background: #f8fafc;
  border: 2px dashed #cbd5e1;
  border-radius: 12px;
  min-height: 300px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #64748b;
  font-size: 14px;
  text-align: center;
  padding: 32px;
}

.empty-icon {
  font-size: 36px;
}

.loading-state {
  text-align: center;
  padding: 32px;
  color: #3b82f6;
  font-size: 14px;
  font-style: italic;
}

.brak-danych {
  text-align: center;
  padding: 32px;
  color: #64748b;
  font-size: 14px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.sloty-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 24px;
}

.slot-btn {
  padding: 10px 16px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: white;
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  cursor: pointer;
  transition: all 0.15s;
  font-family: inherit;
}

.slot-btn:hover {
  border-color: #3b82f6;
  color: #3b82f6;
  background: #eff6ff;
}

.slot-btn--active {
  background: #3b82f6;
  border-color: #3b82f6;
  color: white;
}

.slot-btn--active:hover {
  background: #2563eb;
  color: white;
}

.podsumowanie {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 20px;
  margin-top: 8px;
}

.podsumowanie-title {
  font-size: 13px;
  font-weight: 700;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding-bottom: 12px;
  border-bottom: 1px solid #e2e8f0;
  margin-bottom: 14px;
}

.podsumowanie-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
  font-size: 14px;
  border-bottom: 1px solid #f1f5f9;
}

.podsumowanie-row:last-of-type {
  border-bottom: none;
  margin-bottom: 16px;
}

.podsumowanie-label {
  color: #64748b;
  font-weight: 500;
}

.podsumowanie-value {
  color: #1e293b;
  font-weight: 600;
}

.btn-primary {
  background: #3b82f6;
  color: white;
  padding: 11px 20px;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: 0.2s;
  font-family: inherit;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
}

.btn-primary:disabled {
  background: #93c5fd;
  cursor: not-allowed;
}

.btn-full {
  width: 100%;
}

.error-box {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fee2e2;
  color: #b91c1c;
  padding: 14px 20px;
  border-radius: 8px;
  border: 1px solid #fca5a5;
  margin-bottom: 24px;
  font-weight: 500;
  font-size: 14px;
}

.sukces-box {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #dcfce7;
  color: #15803d;
  padding: 14px 20px;
  border-radius: 8px;
  border: 1px solid #86efac;
  margin-bottom: 24px;
  font-weight: 500;
  font-size: 14px;
}

.sukces-link {
  margin-left: 12px;
  color: #166534;
  font-weight: 700;
  text-decoration: underline;
}

.close-btn {
  background: transparent;
  border: none;
  color: inherit;
  cursor: pointer;
  font-size: 16px;
  font-weight: bold;
  margin-left: auto;
  padding: 0 8px;
  opacity: 0.7;
}

.close-btn:hover {
  opacity: 1;
}

.doctor-info-card {
  margin-top: 12px;
  padding: 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
}

.fw-bold {
  font-weight: 600;
  color: #1e293b;
}

.text-sm {
  font-size: 12px;
}

.text-gray {
  color: #64748b;
  margin-top: 4px;
}

.mt-1 {
  margin-top: 4px;
}

/* STYLE DLA WYSZUKIWARKI PACJENTÓW */
.search-results {
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  margin-top: 4px;
  overflow: hidden;
  background: white;
}

.search-result-item {
  display: flex;
  justify-content: space-between;
  padding: 10px 14px;
  cursor: pointer;
  font-size: 14px;
  border-bottom: 1px solid #f1f5f9;
}

.search-result-item:last-child {
  border-bottom: none;
}

.search-result-item:hover {
  background: #eff6ff;
}

.btn-sm-link {
  background: none;
  border: none;
  color: #3b82f6;
  font-size: 12px;
  cursor: pointer;
  padding: 4px 0;
  text-decoration: underline;
  margin-top: 4px;
}
</style>s