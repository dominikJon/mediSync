<template>
  <div class="page">
    <button @click="router.push('/lekarz/wizyty')" class="btn-back">← Wróć do listy wizyt</button>
    <h1 class="page-title">Szczegóły wizyty i EDM</h1>

    <div v-if="ladowanie" class="loading-state">Ładowanie danych wizyty...</div>
    <div v-else-if="!wizyta" class="error-box">Nie udało się załadować wizyty.</div>

    <div v-else>
      <div v-if="blad" class="error-box">
        {{ blad }} <button @click="blad = ''" class="close-btn">✕</button>
      </div>
      <div v-if="sukces" class="sukces-box">
        {{ sukces }} <button @click="sukces = ''" class="close-btn">✕</button>
      </div>

      <div class="layout-grid">
        <div class="col-left">
          <div class="card info-card">
            <h3 class="card-header">Karta Pacjenta</h3>
            <div class="info-row">
              <span class="fw-bold text-lg">{{ wizyta.pacjent.imie }} {{ wizyta.pacjent.nazwisko }}</span>
            </div>
            <div class="info-row text-gray">
              <span>Wiek:</span> <span class="fw-bold text-dark">{{ wizyta.pacjent.wiek }} lat(a)</span>
            </div>
            <div class="info-row text-gray">
              <span>PESEL:</span> <span class="fw-bold text-dark">{{ wizyta.pacjent.pesel }}</span>
            </div>
            <div class="info-row text-gray">
              <span>Tel:</span> <span class="fw-bold text-dark">{{ wizyta.pacjent.telefon }}</span>
            </div>
          </div>

          <div class="card info-card mt-4">
            <h3 class="card-header">Szczegóły Wizyty</h3>
            <div class="info-row text-gray">
              <span>Data:</span> <span class="fw-bold text-dark">{{ wizyta.termin_od.substring(0, 10) }}</span>
            </div>
            <div class="info-row text-gray">
              <span>Godzina:</span> 
              <span class="fw-bold text-dark">{{ wizyta.termin_od.substring(11, 16) }} – {{ wizyta.termin_do.substring(11, 16) }}</span>
            </div>
            <div class="info-row text-gray">
              <span>Gabinet:</span> <span class="fw-bold text-dark">{{ wizyta.gabinet }}</span>
            </div>
            <div class="info-row text-gray">
              <span>Status:</span> 
              <span :class="['badge', statusKolor(wizyta.status)]">{{ wizyta.status }}</span>
            </div>
          </div>
        </div>

        <div class="col-right">
          <div class="card edm-card">
            <h3 class="card-header">Dokumentacja Medyczna (EDM)</h3>

            <div class="form-group relative">
              <label>Kod ICD-10</label>
              <input 
                type="text" 
                v-model="icd10Query" 
                @input="onIcd10Input"
                placeholder="Szukaj kodu lub nazwy choroby..."
                :disabled="isReadonly"
              />
              <div v-if="icd10Wyniki.length > 0 && !isReadonly" class="autocomplete-dropdown">
                <div 
                  v-for="res in icd10Wyniki" 
                  :key="res.kod" 
                  class="autocomplete-item"
                  @click="wybierzICD10(res.kod, res.nazwa)"
                >
                  <strong>{{ res.kod }}</strong> - {{ res.nazwa }}
                </div>
              </div>
              <div v-if="wybranyICD10" class="selected-icd">
                Wybrany: <strong>{{ wybranyICD10.kod }}</strong> - {{ wybranyICD10.nazwa || 'Kod z bazy' }}
                <button v-if="!isReadonly" @click="wybranyICD10 = null" class="clear-btn">Usuń</button>
              </div>
            </div>

            <div class="form-group" v-for="(val, klucz) in wywiad" :key="klucz">
              <label>{{ klucz }}</label>
              <textarea 
                v-model="wywiad[klucz]" 
                rows="3" 
                :disabled="isReadonly"
                :placeholder="'Wprowadź ' + klucz.toLowerCase() + '...'"
              ></textarea>
            </div>

            <div class="form-actions">
              <button 
                v-if="!isReadonly"
                @click="zapiszDokumentacje" 
                :disabled="zapisywanie"
                class="btn-primary btn-full"
              >
                {{ zapisywanie ? 'Trwa zapisywanie...' : 'Zapisz dokumentację i zakończ wizytę' }}
              </button>
              <div v-else class="readonly-notice">
                Wizyta została zakończona. Dokumentacja jest zablokowana do edycji.
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';

const route = useRoute();
const router = useRouter();
const wizytaId = route.params.id;

// --- INTERFEJSY ---
interface SzczegolyWizyty {
  id: number;
  status: string;
  termin_od: string;
  termin_do: string;
  gabinet: string;
  pacjent: {
    imie: string;
    nazwisko: string;
    pesel: string;
    telefon: string;
    wiek: number; 
  };
  dokumentacja?: {
    kod_icd10: string | null;
    wywiad_lekarski: Record<string, string> | null;
  };
}

// --- STANY ---
const wizyta = ref<SzczegolyWizyty | null>(null);
const ladowanie = ref(false);
const zapisywanie = ref(false);
const blad = ref('');
const sukces = ref('');

// EDM Formularz
const icd10Query = ref('');
const icd10Wyniki = ref<{kod: string, nazwa: string}[]>([]);
const wybranyICD10 = ref<{kod: string, nazwa: string} | null>(null);
const wywiad = ref<Record<string, string>>({
  'Powód wizyty': '',
  'Objawy': '',
  'Wywiad chorobowy': '',
  'Zalecenia': '',
  'Przepisane leki': '',
});

let debounceTimeout: any = null;

// --- COMPUTED ---
const isReadonly = computed(() => 
  wizyta.value?.status === 'Zakończona' || 
  wizyta.value?.status === 'Nieobecność' ||
  wizyta.value?.status === 'Odwołana'
);

// --- HELPERY ---
const obliczWiek = (pesel: string): number => {
  if (!pesel || pesel.length !== 11) return 0;
  let rok = parseInt(pesel.substring(0, 2));
  let miesiac = parseInt(pesel.substring(2, 4));
  
  if (miesiac >= 21 && miesiac <= 32) {
    miesiac -= 20;
    rok += 2000;
  } else {
    rok += 1900;
  }
  
  const dzien = parseInt(pesel.substring(4, 6));
  const urodziny = new Date(rok, miesiac - 1, dzien);
  const dzis = new Date();
  
  let wiek = dzis.getFullYear() - urodziny.getFullYear();
  if (dzis < new Date(dzis.getFullYear(), urodziny.getMonth(), urodziny.getDate())) {
    wiek--;
  }
  return wiek;
};

const statusKolor = (status: string) => {
  switch (status) {
    case 'Zaplanowana': return 'badge-zaplanowana';
    case 'Zakończona': return 'badge-zakonczona';
    case 'Odwołana': return 'badge-odwolana';
    default: return '';
  }
};

// --- METODY API ---
const fetchWizyta = async () => {
  ladowanie.value = true;
  try {
    const response = await axios.get(`/api/lekarz/wizyty/${wizytaId}`);
    const w = response.data;
    
    // Obliczenie wieku
    w.pacjent.wiek = obliczWiek(w.pacjent.pesel);
    wizyta.value = w;

    // Uzupełnienie danych EDM jeśli istnieją
    if (w.dokumentacja) {
      if (w.dokumentacja.kod_icd10) {
        try {
          const icdRes = await axios.get(`/api/slownik/icd10?szukaj=${w.dokumentacja.kod_icd10}`);
          const znaleziony = icdRes.data.find((r: any) => r.kod === w.dokumentacja.kod_icd10);
          wybranyICD10.value = znaleziony
            ? { kod: znaleziony.kod, nazwa: znaleziony.nazwa }
            : { kod: w.dokumentacja.kod_icd10, nazwa: '' };
        } catch {
          wybranyICD10.value = { kod: w.dokumentacja.kod_icd10, nazwa: ''}
        }
      }
      if (w.dokumentacja.wywiad_lekarski) {
        wywiad.value = { ...wywiad.value, ...w.dokumentacja.wywiad_lekarski };
      }
    }
  } catch (error: any) {
    blad.value = "Nie udało się pobrać szczegółów wizyty.";
  } finally {
    ladowanie.value = false;
  }
};

const onIcd10Input = () => {
  clearTimeout(debounceTimeout);
  if (icd10Query.value.length === 0) {
    icd10Wyniki.value = [];
    return;
  }
  debounceTimeout = setTimeout(() => {
    szukajICD10();
  }, 300);
};

const szukajICD10 = async () => {
  try {
    const response = await axios.get(`/api/slownik/icd10?szukaj=${icd10Query.value}`);
    icd10Wyniki.value = response.data;
  } catch (error) {
    console.error("Błąd szukania ICD-10:", error);
    blad.value = 'Błąd wyszukiwania ICD-10.';
  }
};

const wybierzICD10 = (kod: string, nazwa: string) => {
  wybranyICD10.value = { kod, nazwa };
  icd10Query.value = '';
  icd10Wyniki.value = [];
};

const zapiszDokumentacje = async () => {
  // walidacja - czy icd jest wybrany
  if (!wybranyICD10.value) {
    blad.value = 'Wybierz kod ICD-10 przed zapisaniem dokumentacji i zakończeniem wizyty.';
    // Wypuszczamy użytkownika z funkcji, żeby nie poszło API
    return;
  }

  zapisywanie.value = true;
  blad.value = '';
  sukces.value = '';
  
  try {
    const payload = {
      kod_icd10: wybranyICD10.value?.kod || null,
      wywiad_lekarski: wywiad.value
    };
    
    await axios.post(`/api/lekarz/wizyty/${wizytaId}/dokumentacja`, payload);
    sukces.value = "Dokumentacja zapisana. Wizyta została zakończona!";
    
    // Odświeżenie danych żeby zablokować formularz
    await fetchWizyta(); 
  } catch (error: any) {
    blad.value = error.response?.data?.detail || "Błąd podczas zapisu dokumentacji.";
  } finally {
    zapisywanie.value = false;
  }
};

// --- LIFECYCLE ---
onMounted(() => {
  fetchWizyta();
});
</script>

<style scoped>
.page {
  padding: 32px;
  max-width: 1200px;
  margin: 0 auto;
}

.btn-back {
  background: none;
  border: none;
  color: #64748b;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  margin-bottom: 12px;
  padding: 0;
}

.btn-back:hover {
  color: #3b82f6;
  text-decoration: underline;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 24px 0;
}

.layout-grid {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}

.col-left {
  flex: 1;
  min-width: 300px;
}

.col-right {
  flex: 2;
}

.card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  padding: 24px;
}

.card-header {
  font-size: 14px;
  font-weight: 700;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid #e2e8f0;
  padding-bottom: 12px;
  margin-bottom: 16px;
  margin-top: 0;
}

.mt-4 {
  margin-top: 24px;
}

/* Typografia w kartach Info */
.info-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
  font-size: 14px;
}

.info-row:last-child {
  margin-bottom: 0;
}

.text-gray {
  color: #64748b;
}

.text-dark {
  color: #1e293b;
}

.fw-bold {
  font-weight: 600;
}

.text-lg {
  font-size: 18px;
  color: #1e293b;
}

/* Formularze EDM */
.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 6px;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 14px;
  font-family: inherit;
  box-sizing: border-box;
}

.form-group input:disabled,
.form-group textarea:disabled {
  background: #f8fafc;
  color: #64748b;
  cursor: not-allowed;
}

/* Autocomplete ICD-10 */
.relative {
  position: relative;
}

.autocomplete-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
  max-height: 200px;
  overflow-y: auto;
  z-index: 10;
  margin-top: 4px;
}

.autocomplete-item {
  padding: 10px 12px;
  cursor: pointer;
  font-size: 13px;
  border-bottom: 1px solid #f1f5f9;
}

.autocomplete-item:hover {
  background: #eff6ff;
  color: #1d4ed8;
}

.selected-icd {
  margin-top: 8px;
  padding: 10px 12px;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 8px;
  font-size: 13px;
  color: #166534;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.clear-btn {
  background: none;
  border: none;
  color: #dc2626;
  font-size: 12px;
  font-weight: bold;
  cursor: pointer;
  text-decoration: underline;
}

/* Actions */
.form-actions {
  margin-top: 32px;
  border-top: 1px solid #e2e8f0;
  padding-top: 24px;
}

.btn-primary {
  background: #3b82f6;
  color: white;
  border: none;
  padding: 12px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: 0.2s;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
}

.btn-primary:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.btn-full {
  width: 100%;
}

.readonly-notice {
  text-align: center;
  color: #10b981;
  font-weight: 600;
  background: #ecfdf5;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #a7f3d0;
}

/* Statusy i stany alertów z innych widoków */
.badge {
  padding: 6px 12px;
  border-radius: 9999px;
  font-size: 12px;
  font-weight: 600;
  display: inline-block;
}

.badge-zaplanowana {
  background: #dbeafe;
  color: #1e40af;
}

.badge-zakonczona {
  background: #dcfce7;
  color: #166534;
}

.badge-odwolana {
  background: #f1f5f9;
  color: #64748b;
}

.error-box {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fee2e2;
  color: #b91c1c;
  padding: 14px 20px;
  border-radius: 8px;
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
  margin-bottom: 24px;
  font-weight: 500;
  font-size: 14px;
}

.close-btn {
  background: transparent;
  border: none;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  opacity: 0.7;
}

.loading-state {
  text-align: center;
  padding: 32px;
  color: #3b82f6;
  font-style: italic;
}
</style>