<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

// Menu podstawowe dla wszystkich
const menuPodstawowe = [
  { name: 'Pulpit', path: '/', icon: '🏠' },
  { name: 'Harmonogram', path: '/schedule', icon: '📆' },
  { name: 'EDM / Kartoteka', path: '/records', icon: '📁' },
  { name: 'Raporty', path: '/reports', icon: '📊' },
]

// Menu tylko dla admina
const menuAdmin = [
  { name: 'Użytkownicy', path: '/admin/users', icon: '👥' },
  { name: 'Dodaj lekarza', path: '/admin/add-doctor', icon: '👨‍⚕️' },
  { name: 'Dodaj pracownika', path: '/admin/add-staff', icon: '👨‍💼' }
]

const isAdmin = computed(() => authStore.user?.rola === 'admin')

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}
</script>

<template>
  <aside class="sidebar">
    <div class="logo">
      <h2><span class="text-blue">Medi</span><span class="text-green">Sync</span></h2>
    </div>

    <nav class="nav-menu">
      <!-- Menu podstawowe -->
      <RouterLink
        v-for="item in menuPodstawowe"
        :key="item.path"
        :to="item.path"
        class="nav-link"
        active-class="active"
      >
        <span class="icon">{{ item.icon }}</span>
        {{ item.name }}
      </RouterLink>

      <!-- Sekcja admina — widoczna tylko dla roli admin -->
      <div v-if="isAdmin" class="section-divider">
        <span>Panel Admina</span>
      </div>

      <RouterLink
        v-if="isAdmin"
        v-for="item in menuAdmin"
        :key="item.path"
        :to="item.path"
        class="nav-link admin-link"
        active-class="active"
      >
        <span class="icon">{{ item.icon }}</span>
        {{ item.name }}
      </RouterLink>
    </nav>

    <div class="sidebar-footer">
      <div class="user-info">
        <div class="avatar">
          {{ authStore.user?.rola === 'lekarz' ? '👨‍⚕️' : authStore.user?.rola === 'admin' ? '⚙️' : '👤' }}
        </div>
        <div class="user-details">
          <span class="user-name">
            {{ authStore.user?.imie ? `${authStore.user.imie} ${authStore.user.nazwisko}` : authStore.user?.email }}
          </span>
          <span class="user-role">
            {{ authStore.user?.rola ? authStore.user.rola.charAt(0).toUpperCase() + authStore.user.rola.slice(1) : 'Gość' }}
          </span>
        </div>
      </div>
      <button @click="handleLogout" class="btn-logout">
        <span class="icon">🚪</span> Wyloguj się
      </button>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  width: 260px;
  background-color: #ffffff;
  border-right: 1px solid #e0e0e0;
  height: 100vh;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  position: sticky;
  top: 0;
}

.logo {
  padding: 24px;
  text-align: center;
  border-bottom: 1px solid #e0e0e0;
}

.logo h2 {
  margin: 0;
  font-size: 26px;
  font-weight: bold;
}

.text-blue { color: #0056b3; }
.text-green { color: #28a745; }

.nav-menu {
  display: flex;
  flex-direction: column;
  flex: 1;
  padding-top: 8px;
  overflow-y: auto;
}

.nav-link {
  display: flex;
  align-items: center;
  text-decoration: none;
  color: #333333;
  padding: 16px 24px;
  font-size: 15px;
  font-weight: 600;
  border-right: 4px solid transparent;
  transition: all 0.2s;
}

.nav-link:hover {
  background-color: #f8f9fa;
}

.nav-link.active {
  background-color: #EEF4FB;
  color: #0056b3;
  border-right: 4px solid #0056b3;
}

.admin-link.active {
  background-color: #fef3c7;
  color: #92400e;
  border-right: 4px solid #f59e0b;
}

.admin-link:hover {
  background-color: #fffbeb;
}

.section-divider {
  padding: 8px 24px;
  font-size: 11px;
  font-weight: 700;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-top: 8px;
}

.icon {
  margin-right: 12px;
  font-size: 20px;
}

.sidebar-footer {
  padding: 20px;
  border-top: 1px solid #e0e0e0;
  background-color: #fcfcfc;
}

.user-info {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.avatar {
  width: 40px;
  height: 40px;
  background-color: #e2e8f0;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  margin-right: 12px;
  flex-shrink: 0;
}

.user-details {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.user-name {
  font-size: 14px;
  font-weight: bold;
  color: #1e293b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-role {
  font-size: 12px;
  color: #64748b;
}

.btn-logout {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 10px;
  background-color: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  color: #ef4444;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-logout:hover {
  background-color: #fee2e2;
  border-color: #ef4444;
}
</style>