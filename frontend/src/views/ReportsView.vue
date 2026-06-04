<script setup lang="ts">
import { ref, onMounted } from 'vue';
import axios from 'axios';

// --- INTERFEJSY ---
interface Summary {
  pacjenci: number;
  lekarze: number;
  wizyty_dzis: number;
  wizyty_miesiac: number;
}

interface RaportWizyt {
  okres: { od: string; do: string };
  lacznie: number;
  per_status: { status: string; liczba: number; procent: number }[];
  per_lekarz: {
    lekarz: string;
    specjalizacje: string[];
    wszystkie: number;
    zakonczone: number;
    odwolane: number;
    nieobecnosci: number;
    zaplanowane: number;
  }[];
}

// --- BEZPIECZNE DATY (Lokalne) ---
const getLocalYMD = (date: Date) => {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
};

const dzis = new Date();
const trzydziesciDniTemu = new Date();
trzydziesciDniTemu.setDate(dzis.getDate() - 30);

// --- STANY ---
const summary = ref<Summary | null>(null);
const raport = ref<RaportWizyt | null>(null);

const dataOd = ref<string>(getLocalYMD(trzydziesciDniTemu));
const dataDo = ref<string>(getLocalYMD(dzis));

const ladowanieKafelkow = ref(false);
const ladowanie = ref(false);
const blad = ref('');

// --- METODY ---
const fetchSummary = async () => {
  ladowanieKafelkow.value = true;
  try {
    const response = await axios.get('/api/admin/raporty/summary');
    summary.value = response.data;
  } catch (error) {
    console.error("Błąd pobierania podsumowania:", error);
    blad.value = "Błąd podczas pobierania podsumowania.";
  } finally {
    ladowanieKafelkow.value = false;
  }
};

const fetchRaport = async () => {
  blad.value = '';
  if (dataOd.value > dataDo.value) {
    blad.value = 'Data "od" nie może być późniejsza niż "do".'
    return
  }
  ladowanie.value = true;
  try {
    const response = await axios.get(`/api/admin/raporty/wizyty?od=${dataOd.value}&do=${dataDo.value}`);
    raport.value = response.data;
  } catch (error: any) {
    blad.value = error.response?.data?.detail || "Błąd podczas generowania raportu.";
  } finally {
    ladowanie.value = false;
  }
};

const statusKolor = (status: string) => {
  switch (status) {
    case 'Zaplanowana': return 'badge-zaplanowana';
    case 'Zakończona': return 'badge-zakonczona';
    case 'Odwołana': return 'badge-odwolana';
    case 'Nieobecność': return 'badge-nieobecnosc';
    default: return 'badge-domyslny';
  }
};

// --- LIFECYCLE ---
onMounted(() => {
  fetchSummary();
  // Opcjonalnie: od razu generujemy raport dla domyślnych dat przy wejściu na widok
  fetchRaport();
});
</script>

<template>
  <div class="page">
    <h1 class="page-title">Raporty i statystyki</h1>

    <div v-if="blad" class="error-box">
      {{ blad }}
      <button @click="blad = ''" class="close-btn">✕</button>
    </div>

    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label">Pacjenci</div>
        <div v-if="ladowanieKafelkow" class="kpi-loading">...</div>
        <div v-else class="kpi-value">{{ summary?.pacjenci || 0 }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Lekarze</div>
        <div v-if="ladowanieKafelkow" class="kpi-loading">...</div>
        <div v-else class="kpi-value">{{ summary?.lekarze || 0 }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Wizyty (Dziś)</div>
        <div v-if="ladowanieKafelkow" class="kpi-loading">...</div>
        <div v-else class="kpi-value">{{ summary?.wizyty_dzis || 0 }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Wizyty (Ten miesiąc)</div>
        <div v-if="ladowanieKafelkow" class="kpi-loading">...</div>
        <div v-else class="kpi-value">{{ summary?.wizyty_miesiac || 0 }}</div>
      </div>
    </div>

    <div class="card filter-card">
      <div class="form-group">
        <label>Data od:</label>
        <input type="date" v-model="dataOd" />
      </div>
      <div class="form-group">
        <label>Data do:</label>
        <input type="date" v-model="dataDo" />
      </div>
      <div class="form-action">
        <button @click="fetchRaport" :disabled="ladowanie" class="btn-primary">
          {{ ladowanie ? 'Generowanie...' : 'Generuj raport' }}
        </button>
      </div>
    </div>

    <div v-if="ladowanie" class="loading-state">
      Przeliczanie danych, proszę czekać...
    </div>
    
    <div v-else-if="raport">
      
      <div class="raport-summary-bar">
        Wygenerowano raport za okres: <strong>{{ raport.okres.od }}</strong> do <strong>{{ raport.okres.do }}</strong>
        <span class="lacznie-badge">Łącznie wizyt: {{ raport.lacznie }}</span>
      </div>

      <div class="layout-grid">
        
        <div class="col-left">
          <div class="card">
            <h3 class="card-header">Wizyty per status</h3>
            <div v-if="raport.per_status.length === 0" class="empty-state">Brak wizyt w tym okresie.</div>
            <table v-else class="table">
              <thead>
                <tr>
                  <th>Status</th>
                  <th class="text-right">Liczba</th>
                  <th class="text-right">%</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="stat in raport.per_status" :key="stat.status">
                  <td><span :class="['badge', statusKolor(stat.status)]">{{ stat.status }}</span></td>
                  <td class="text-right fw-bold">{{ stat.liczba }}</td>
                  <td class="text-right text-gray">{{ stat.procent }}%</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="col-right">
          <div class="card" style="overflow-x: auto;">
            <h3 class="card-header">Wizyty per lekarz</h3>
            <div v-if="raport.per_lekarz.length === 0" class="empty-state">Brak wizyt w tym okresie.</div>
            <table v-else class="table table-sm">
              <thead>
                <tr>
                  <th>Lekarz</th>
                  <th>Specjalizacja</th>
                  <th class="text-center">Wszystkie</th>
                  <th class="text-center text-success">Zakończone</th>
                  <th class="text-center text-danger">Odwołane</th>
                  <th class="text-center text-warning">Nieobecność</th>
                  <th class="text-center text-primary">Zaplanowane</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="lek in raport.per_lekarz" :key="lek.lekarz">
                  <td class="fw-bold">{{ lek.lekarz }}</td>
                  <td class="text-sm text-gray">{{ lek.specjalizacje.join(', ') || '-' }}</td>
                  <td class="text-center fw-bold">{{ lek.wszystkie }}</td>
                  <td class="text-center">{{ lek.zakonczone }}</td>
                  <td class="text-center">{{ lek.odwolane }}</td>
                  <td class="text-center">{{ lek.nieobecnosci }}</td>
                  <td class="text-center">{{ lek.zaplanowane }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </div>

  </div>
</template>

<style scoped>
.page {
  padding: 32px;
  max-width: 1200px;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 24px 0;
}

/* Kafelki KPI */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.kpi-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  padding: 20px;
  text-align: center;
  border-top: 4px solid #3b82f6;
}

.kpi-label {
  font-size: 13px;
  font-weight: 700;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 8px;
}

.kpi-value {
  font-size: 32px;
  font-weight: 800;
  color: #1e293b;
}

.kpi-loading {
  font-size: 24px;
  color: #cbd5e1;
  font-weight: bold;
}

/* Karty */
.card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  padding: 24px;
  margin-bottom: 24px;
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

/* Filtry */
.filter-card {
  display: flex;
  gap: 20px;
  align-items: flex-end;
  flex-wrap: wrap;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group label {
  font-size: 13px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 6px;
}

.form-group input {
  padding: 10px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 14px;
  font-family: inherit;
  min-width: 150px;
}

.form-action {
  margin-bottom: 2px;
}

.btn-primary {
  background: #3b82f6;
  color: white;
  border: none;
  padding: 11px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: 0.2s;
  height: 41px;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
}

.btn-primary:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

/* Pasek podsumowania */
.raport-summary-bar {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 16px 20px;
  margin-bottom: 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  color: #475569;
}

.lacznie-badge {
  background: #1e293b;
  color: white;
  padding: 6px 12px;
  border-radius: 999px;
  font-weight: bold;
  font-size: 13px;
}

/* Layout Grid */
.layout-grid {
  display: flex;
  gap: 24px;
  align-items: flex-start;
  flex-wrap: wrap;
}

.col-left {
  flex: 1;
  min-width: 300px;
}

.col-right {
  flex: 2;
  min-width: 400px;
}

/* Tabela */
.table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.table th {
  background: #f8fafc;
  padding: 12px 16px;
  font-size: 12px;
  font-weight: 700;
  color: #64748b;
  border-bottom: 1px solid #e2e8f0;
  text-transform: uppercase;
}

.table td {
  padding: 12px 16px;
  border-bottom: 1px solid #e2e8f0;
  font-size: 14px;
  color: #1e293b;
  vertical-align: middle;
}

.table tbody tr:last-child td {
  border-bottom: none;
}

.table tbody tr:hover {
  background: #f8fafc;
}

.table-sm th, .table-sm td {
  padding: 10px 12px;
}

/* Narzędzia tabeli */
.text-right { text-align: right; }
.text-center { text-align: center; }
.text-gray { color: #64748b; }
.fw-bold { font-weight: 600; }
.text-sm { font-size: 13px; }

/* Kolory kolumn tabeli wg statusu */
.text-success { color: #166534; }
.text-danger { color: #b91c1c; }
.text-warning { color: #9a3412; }
.text-primary { color: #1d4ed8; }

/* Badges */
.badge {
  padding: 6px 12px;
  border-radius: 9999px;
  font-size: 12px;
  font-weight: 600;
  display: inline-block;
}

.badge-zaplanowana { background: #dbeafe; color: #1e40af; }
.badge-zakonczona { background: #dcfce7; color: #166534; }
.badge-odwolana { background: #fee2e2; color: #b91c1c; }
.badge-nieobecnosc { background: #ffedd5; color: #9a3412; }
.badge-domyslny { background: #f1f5f9; color: #475569; }

/* Użytkowe */
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

.close-btn {
  background: transparent;
  border: none;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  opacity: 0.7;
}

.close-btn:hover {
  opacity: 1;
}

.loading-state {
  text-align: center;
  padding: 40px;
  color: #3b82f6;
  font-style: italic;
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.empty-state {
  text-align: center;
  padding: 24px;
  color: #64748b;
  font-size: 14px;
  font-style: italic;
}
</style>