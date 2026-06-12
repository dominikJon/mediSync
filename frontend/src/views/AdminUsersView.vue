<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'

interface Uzytkownik {
  id: number
  email: string
  rola: string
  profil_uzupelniony: boolean
  imie: string | null
  nazwisko: string | null
}

const uzytkownicy = ref<Uzytkownik[]>([])
const ladowanie = ref(true)
const blad = ref('')

// zmienne do wyszukiwarki userow - imie, naziwsko, email
const frazaSzukana = ref('')

const przefiltrowaniUzytkownicy = computed(() => {
  if (!frazaSzukana.value) {
    return uzytkownicy.value
  }
  
  const szukane = frazaSzukana.value.toLowerCase()
  
  return uzytkownicy.value.filter(u => {
    const emailMatch = u.email?.toLowerCase().includes(szukane)
    const imieMatch = u.imie?.toLowerCase().includes(szukane)
    const nazwiskoMatch = u.nazwisko?.toLowerCase().includes(szukane)
    
    return emailMatch || imieMatch || nazwiskoMatch
  })
})


const pobierzUzytkownikow = async () => {
  try {
    const response = await axios.get('/api/admin/users')
    uzytkownicy.value = response.data.uzytkownicy
  } catch (error: any) {
    if (error.response?.status === 403) {
      blad.value = 'Brak uprawnień do tej strony.'
    } else {
      blad.value = 'Błąd podczas pobierania listy użytkowników.'
    }
  } finally {
    ladowanie.value = false
  }
}

const roleKolor = (rola: string) => {
  switch (rola) {
    case 'admin': return 'badge-admin'
    case 'lekarz': return 'badge-lekarz'
    case 'rejestracja': return 'badge-rejestracja'
    default: return 'badge-pacjent'
  }
}

onMounted(pobierzUzytkownikow)
</script>

<template>
  <div class="page">
    <div class="page-header">
      <h1>Użytkownicy systemu</h1>
        <div class="header-actions">
          <RouterLink to="/admin/add-doctor" class="btn-primary">
            + Dodaj lekarza
          </RouterLink>
          
          <RouterLink to="/admin/add-staff" class="btn-primary">
            + Dodaj pracownika
          </RouterLink>
      </div>
    </div>
    
    <div class="search-bar" v-if="!ladowanie && !blad">
      <input 
        type="text" 
        v-model="frazaSzukana" 
        placeholder="🔍 Szukaj (e-mail, imię, nazwisko)..." 
        class="search-input"
      >
    </div>

    <div v-if="ladowanie" class="loading">Ładowanie...</div>

    <div v-else-if="blad" class="error-box">{{ blad }}</div>

    <div v-else class="table-wrapper">
      <table class="table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Email</th>
            <th>Imię i nazwisko</th>
            <th>Rola</th>
            <th>Kartoteka</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in przefiltrowaniUzytkownicy" :key="u.id">
            <td class="id-cell">{{ u.id }}</td>
            <td>{{ u.email }}</td>
            <td>
              {{ u.imie && u.nazwisko ? `${u.imie} ${u.nazwisko}` : '—' }}
            </td>
            <td>
              <span :class="['badge', roleKolor(u.rola)]">
                {{ u.rola }}
              </span>
            </td>
            <td>
              <span :class="u.profil_uzupelniony ? 'status-ok' : 'status-brak'">
                {{ u.profil_uzupelniony ? '✓ Uzupełniona' : '✗ Brak' }}
              </span>
            </td>
            <td>
              <button class="btn-edit" @click="$router.push(`/admin/user/${u.id}`)">
                <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                </svg>
              </button>
            </td>
          </tr>
          <tr v-if="przefiltrowaniUzytkownicy.length === 0">
            <td colspan="6" class="empty-state">Brak wyników wyszukiwania.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
/* dla search baru */ 
.search-bar {
  margin-bottom: 20px;
}

.search-input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.search-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.empty-state {
  text-align: center;
  padding: 30px;
  color: #64748b;
  font-style: italic;
}

.page {
  padding: 32px;
  max-width: 1100px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
}

.header-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.btn-primary {
  padding: 10px 20px;
  background-color: #3b82f6;
  color: white;
  border-radius: 8px;
  font-weight: 600;
  text-decoration: none;
  font-size: 14px;
  transition: 0.2s;
}

.btn-primary:hover {
  background-color: #2563eb;
}

.loading {
  color: #64748b;
  padding: 20px;
}

.error-box {
  background: #fee2e2;
  color: #dc2626;
  padding: 12px 16px;
  border-radius: 8px;
}

.table-wrapper {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  overflow: hidden;
}

.table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.table thead {
  background-color: #f8fafc;
}

.table th {
  padding: 14px 16px;
  text-align: left;
  font-size: 12px;
  font-weight: 700;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid #e2e8f0;
}

.table td {
  padding: 14px 16px;
  border-bottom: 1px solid #f1f5f9;
  color: #1e293b;
}

.table tbody tr:hover {
  background-color: #f8fafc;
}

.table tbody tr:last-child td {
  border-bottom: none;
}

.id-cell {
  color: #94a3b8;
  font-size: 12px;
}

.badge {
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

.badge-admin {
  background: #fef3c7;
  color: #92400e;
}

.badge-lekarz {
  background: #dbeafe;
  color: #1e40af;
}

.badge-rejestracja {
  background: #dfbbf7;
  color: #7f1eaf;
}

.badge-pacjent {
  background: #dcfce7;
  color: #166534;
}

.status-ok {
  color: #16a34a;
  font-weight: 600;
  font-size: 13px;
}

.status-brak {
  color: #dc2626;
  font-weight: 600;
  font-size: 13px;
}

.btn-edit {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: #f1f5f9;
  color: #64748b;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  cursor: pointer;
  transition: 0.2s;
}

.btn-edit:hover {
  background: #dbeafe;
  color: #3b82f6;
  border-color: #3b82f6;
}
</style>