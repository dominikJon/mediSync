<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

// Menu nawigacyjne
const menuItems = [
  { name: 'Pulpit', path: '/', icon: '🏠' },
  { name: 'Harmonogram', path: '/schedule', icon: '📆' },
  { name: 'EDM / Kartoteka', path: '/records', icon: '📁' },
  { name: 'Raporty', path: '/reports', icon: '📊' }
]

// Funkcja wylogowania
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
      <RouterLink 
        v-for="item in menuItems" 
        :key="item.path" 
        :to="item.path"
        class="nav-link"
        active-class="active"
      >
        <span class="icon">{{ item.icon }}</span>
        {{ item.name }}
      </RouterLink>
    </nav>

    <div class="sidebar-footer">
      <div class="user-info">
        <div class="avatar">
          {{ authStore.user?.rola === 'lekarz' ? '👨‍⚕️' : '👤' }}
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

/* Kluczowe: nav-menu rośnie, wypychając footer na dół */
.nav-menu {
  display: flex;
  flex-direction: column;
  flex: 1; 
  padding-top: 8px;
}

.nav-link {
  display: flex;
  align-items: center;
  text-decoration: none;
  color: #333333;
  padding: 16px 24px;
  font-size: 16px;
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

.icon {
  margin-right: 12px;
  font-size: 20px;
}

/* Sekcja użytkownika na dole */
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
}

.user-details {
  display: flex;
  flex-direction: column;
}

.user-name {
  font-size: 14px;
  font-weight: bold;
  color: #1e293b;
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