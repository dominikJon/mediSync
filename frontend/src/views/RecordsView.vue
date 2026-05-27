<template>
  <div class="page">
    <h1 class="page-title">Moje wizyty</h1>

    <div v-if="blad" class="error-box">
      {{ blad }}
      <button @click="blad = ''" class="close-btn">✕</button>
    </div>
    <div v-if="sukces" class="sukces-box">
      {{ sukces }}
      <button @click="sukces = ''" class="close-btn">✕</button>
    </div>

    <div v-if="ladowanie" class="loading-state">
      Ładowanie historii wizyt...
    </div>

    <div v-else-if="wizyty.length === 0" class="empty-state">
      <span class="empty-icon">📂</span>
      <p>Nie masz jeszcze żadnych wizyt.</p>
      <RouterLink to="/schedule" class="link-primary">Zarezerwuj pierwszą wizytę →</RouterLink>
    </div>

    <div v-else class="card" style="padding: 0; overflow: hidden;">
      <table class="table">
        <thead>
          <tr>
            <th>Data i godzina</th>
            <th>Lekarz</th>
            <th>Specjalizacja</th>
            <th>Gabinet</th>
            <th>Cena</th>
            <th>Status</th>
            <th>Akcja</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="w in wizyty" :key="w.id">
            <td>
              <div class="fw-bold">{{ w.termin_od.substring(0, 10) }}</div>
              <div class="text-sm text-gray">{{ w.termin_od.substring(11, 16) }} – {{ w.termin_do.substring(11, 16) }}</div>
            </td>
            <td>dr {{ w.lekarz_imie }} {{ w.lekarz_nazwisko }}</td>
            <td>{{ w.specjalizacje.join(', ') }}</td>
            <td>{{ w.gabinet }}</td>
            <td>{{ w.cena }} zł</td>
            <td>
              <span :class="['badge', statusKolor(w.status)]">{{ w.status }}</span>
            </td>
            <td>
              <div v-if="moznaOdwolac(w)">
                <div v-if="wizytaDoOdwolania === w.id" class="confirm-actions">
                  <span class="confirm-text">Na pewno?</span>
                  <button @click="odwolaj(w.id)" class="btn-danger btn-sm">Tak</button>
                  <button @click="wizytaDoOdwolania = null" class="btn-secondary btn-sm">Nie</button>
                </div>
                <button v-else @click="wizytaDoOdwolania = w.id" class="btn-danger btn-outline">
                  Odwołaj
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import axios from 'axios';

// ts interfejsy
interface Wizyta {
  id: number;
  status: string;
  termin_od: string;
  termin_do: string;
  lekarz_imie: string;
  lekarz_nazwisko: string;
  specjalizacje: string[];
  gabinet: string;
  cena: string;
}

// stany
const wizyty = ref<Wizyta[]>([]);
const ladowanie = ref(false);
const wizytaDoOdwolania = ref<number | null>(null);

const blad = ref<string>('');
const sukces = ref<string>('');

// metody
const fetchWizyty = async () => {
  ladowanie.value = true;
  blad.value = '';
  try {
    const response = await axios.get('/api/wizyty/moje');
    wizyty.value = response.data.wizyty;
  } catch (error) {
    console.error("Błąd podczas pobierania wizyt:", error);
    blad.value = 'Błąd podczas pobierania wizyt.';
  } finally {
    ladowanie.value = false;
  }
};

const odwolaj = async (id: number) => {
  // Czyszczenie starych komunikatów przy nowej akcji
  blad.value = '';
  sukces.value = '';
  
  try {
    await axios.delete(`/api/wizyty/${id}`);
    wizytaDoOdwolania.value = null;
    sukces.value = "Wizyta została pomyślnie odwołana.";
    await fetchWizyty(); // Odświeżenie danych w tabeli
  } catch (error: any) {
    blad.value = error.response?.data?.detail || "Nie udało się odwołać wizyty.";
  }
};

const moznaOdwolac = (wizyta: Wizyta) => {
  if (wizyta.status !== 'Zaplanowana') return false;
  const termin = new Date(wizyta.termin_od + (wizyta.termin_od.includes('+') || wizyta.termin_od.endsWith('Z') ? '' : 'Z'));
  return termin > new Date(Date.now() + 24 * 60 * 60 * 1000);
};

const statusKolor = (status: string) => {
  switch (status) {
    case 'Zaplanowana': return 'badge-zaplanowana';
    case 'Zakończona': return 'badge-zakonczona';
    case 'Odwołana': return 'badge-odwolana';
    default: return '';
  }
};

// --- LIFECYCLE ---
onMounted(() => {
  fetchWizyty();
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

.card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.loading-state {
  text-align: center;
  padding: 32px;
  color: #3b82f6;
  font-size: 14px;
  font-style: italic;
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

.link-primary {
  color: #3b82f6;
  font-weight: 600;
  text-decoration: none;
}

.link-primary:hover {
  text-decoration: underline;
}

/* Tabela */
.table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.table th {
  background: #f8fafc;
  padding: 16px 20px;
  font-size: 13px;
  font-weight: 600;
  color: #475569;
  border-bottom: 1px solid #e2e8f0;
}

.table td {
  padding: 16px 20px;
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

.fw-bold {
  font-weight: 600;
}

.text-sm {
  font-size: 12px;
}

.text-gray {
  color: #64748b;
  margin-top: 4px;
}

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

/* Przyciski i akcje */
.confirm-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.confirm-text {
  font-size: 12px;
  font-weight: 600;
  color: #ef4444;
}

.btn-danger {
  background: #ef4444;
  color: white;
  border: none;
  padding: 8px 14px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: 0.2s;
}

.btn-danger:hover {
  background: #dc2626;
}

.btn-danger.btn-outline {
  background: white;
  color: #ef4444;
  border: 1px solid #ef4444;
}

.btn-danger.btn-outline:hover {
  background: #fef2f2;
}

.btn-secondary {
  background: #e2e8f0;
  color: #475569;
  border: none;
  padding: 8px 14px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: 0.2s;
}

.btn-secondary:hover {
  background: #cbd5e1;
}

.btn-sm {
  padding: 6px 10px;
  font-size: 12px;
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
</style>