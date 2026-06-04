<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const ladowanie = ref(true)
const blad = ref('')
const dane = ref<any>(null)

const pobierzDane = async () => {
  try {
    const res = await axios.get('/api/admin/pulpit')
    dane.value = res.data
  } catch {
    blad.value = 'Błąd podczas pobierania danych.'
  } finally {
    ladowanie.value = false
  }
}

const roleKolor = (rola: string) => {
  switch (rola) {
    case 'admin':      return 'badge-admin'
    case 'lekarz':     return 'badge-lekarz'
    case 'rejestracja': return 'badge-rejestracja'
    default:           return 'badge-pacjent'
  }
}

onMounted(pobierzDane)
</script>

<template>
  <div class="page">
    <div class="page-header">
      <h1>Panel administratora</h1>
      <p class="podtytul">
        {{ new Date().toLocaleDateString('pl-PL', {
          weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
        }) }}
      </p>
    </div>

    <div v-if="ladowanie" class="loading">Ładowanie...</div>
    <div v-else-if="blad" class="error-box">{{ blad }}</div>

    <template v-else-if="dane">

      <!-- Statystyki użytkowników -->
      <div class="stats-grid">
        <div class="stat-kafelek niebieski">
          <span class="stat-liczba">{{ dane.uzytkownicy['lekarz'] ?? 0 }}</span>
          <span class="stat-opis">Lekarzy</span>
        </div>
        <div class="stat-kafelek zielony">
          <span class="stat-liczba">{{ dane.uzytkownicy['pacjent'] ?? 0 }}</span>
          <span class="stat-opis">Pacjentów</span>
        </div>
        <div class="stat-kafelek fioletowy">
          <span class="stat-liczba">{{ dane.uzytkownicy['rejestracja'] ?? 0 }}</span>
          <span class="stat-opis">Pracowników recepcji</span>
        </div>
        <div class="stat-kafelek szary">
          <span class="stat-liczba">{{ dane.uzytkownicy['admin'] ?? 0 }}</span>
          <span class="stat-opis">Administratorów</span>
        </div>
      </div>

      <!-- Gabinety + szybkie akcje -->
      <div class="dwa-kolumny">

        <!-- Gabinety -->
        <div class="card">
          <div class="card-title">Gabinety</div>
          <div class="gabinety-row">
            <div class="gabinet-stat dostepny">
              <span class="gabinet-liczba">{{ dane.gabinety.dostepne }}</span>
              <span class="gabinet-opis">Dostępnych</span>
            </div>
            <div class="gabinet-divider"></div>
            <div class="gabinet-stat niedostepny">
              <span class="gabinet-liczba">{{ dane.gabinety.niedostepne }}</span>
              <span class="gabinet-opis">Niedostępnych</span>
            </div>
          </div>
          <button @click="router.push('/reception/office')" class="btn-link">
            Zarządzaj gabinetami →
          </button>
        </div>

        <!-- Szybkie akcje -->
        <div class="card">
          <div class="card-title">Szybkie akcje</div>
          <div class="akcje-lista">
            <button @click="router.push('/admin/add-doctor')" class="akcja-btn">
              <span class="akcja-ikona">👨‍⚕️</span>
              <span>Dodaj lekarza</span>
            </button>
            <button @click="router.push('/admin/add-staff')" class="akcja-btn">
              <span class="akcja-ikona">👤</span>
              <span>Dodaj pracownika</span>
            </button>
            <button @click="router.push('/admin/users')" class="akcja-btn">
              <span class="akcja-ikona">📋</span>
              <span>Lista użytkowników</span>
            </button>
            <button @click="router.push('/reception/graphic')" class="akcja-btn">
              <span class="akcja-ikona">🗓️</span>
              <span>Grafik pracy</span>
            </button>
          </div>
        </div>

      </div>

      <!-- Ostatnio dodani użytkownicy -->
      <div class="card">
        <div class="card-title">Ostatnio dodani użytkownicy</div>
        <div class="uzytkownicy-lista">
          <div
            v-for="u in dane.ostatni_uzytkownicy"
            :key="u.id"
            class="uzytkownik-row"
            @click="router.push(`/admin/user/${u.id}`)"
          >
            <div class="uzytkownik-info">
              <span class="uzytkownik-nazwa">
                {{ u.imie && u.nazwisko ? `${u.imie} ${u.nazwisko}` : u.email }}
              </span>
              <span class="uzytkownik-email">{{ u.email }}</span>
            </div>
            <span :class="['badge', roleKolor(u.rola)]">{{ u.rola }}</span>
            <span class="arrow">→</span>
          </div>
        </div>
        <button @click="router.push('/admin/users')" class="btn-link">
          Zobacz wszystkich użytkowników →
        </button>
      </div>

    </template>
  </div>
</template>

<style scoped>
.page { padding: 32px; max-width: 900px; }
.page-header { margin-bottom: 28px; }
.page-header h1 { font-size: 26px; font-weight: 700; color: #1e293b; margin: 0; }
.podtytul { color: #64748b; margin: 4px 0 0 0; font-size: 14px; }
.loading { color: #64748b; padding: 20px; }
.error-box { background: #fee2e2; color: #dc2626; padding: 12px 16px; border-radius: 8px; margin-bottom: 16px; }

.stats-grid {
  display: grid; grid-template-columns: repeat(4, 1fr);
  gap: 12px; margin-bottom: 16px;
}

.stat-kafelek {
  border-radius: 12px; padding: 20px;
  display: flex; flex-direction: column; gap: 6px;
}
.stat-kafelek.niebieski  { background: #dbeafe; }
.stat-kafelek.zielony    { background: #dcfce7; }
.stat-kafelek.fioletowy  { background: #ede9fe; }
.stat-kafelek.szary      { background: #f1f5f9; }

.stat-liczba { font-size: 32px; font-weight: 800; color: #1e293b; line-height: 1; }
.stat-opis   { font-size: 12px; font-weight: 600; color: #475569; }

.dwa-kolumny {
  display: grid; grid-template-columns: 1fr 1fr;
  gap: 16px; margin-bottom: 16px;
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

.gabinety-row {
  display: flex; align-items: center;
  justify-content: space-around; padding: 16px 0;
}
.gabinet-stat { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.gabinet-liczba { font-size: 36px; font-weight: 800; color: #1e293b; }
.gabinet-opis   { font-size: 13px; font-weight: 600; color: #64748b; }
.gabinet-stat.dostepny .gabinet-liczba  { color: #16a34a; }
.gabinet-stat.niedostepny .gabinet-liczba { color: #dc2626; }
.gabinet-divider { width: 1px; height: 60px; background: #e2e8f0; }

.akcje-lista { display: flex; flex-direction: column; gap: 8px; }
.akcja-btn {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 16px; background: #f8fafc;
  border: 1px solid #e2e8f0; border-radius: 8px;
  cursor: pointer; transition: 0.15s;
  font-size: 14px; font-weight: 600; color: #475569;
  text-align: left;
}
.akcja-btn:hover { background: #eff6ff; border-color: #3b82f6; color: #3b82f6; }
.akcja-ikona { font-size: 18px; }

.uzytkownicy-lista { display: flex; flex-direction: column; gap: 8px; margin-bottom: 12px; }
.uzytkownik-row {
  display: flex; align-items: center; gap: 12px;
  padding: 12px; border-radius: 8px; background: #f8fafc;
  cursor: pointer; transition: 0.15s;
}
.uzytkownik-row:hover { background: #eff6ff; }
.uzytkownik-info { display: flex; flex-direction: column; flex: 1; }
.uzytkownik-nazwa { font-size: 14px; font-weight: 600; color: #1e293b; }
.uzytkownik-email { font-size: 12px; color: #94a3b8; margin-top: 2px; }

.badge {
  padding: 4px 10px; border-radius: 20px;
  font-size: 12px; font-weight: 600;
}
.badge-admin      { background: #fef3c7; color: #92400e; }
.badge-lekarz     { background: #dbeafe; color: #1e40af; }
.badge-rejestracja { background: #ede9fe; color: #6d28d9; }
.badge-pacjent    { background: #dcfce7; color: #166534; }

.arrow { color: #cbd5e1; font-size: 16px; }

.btn-link {
  background: none; border: none; color: #3b82f6;
  font-weight: 600; font-size: 13px; cursor: pointer;
  padding: 8px 0 0 0; display: block;
}
.btn-link:hover { color: #2563eb; }
</style>