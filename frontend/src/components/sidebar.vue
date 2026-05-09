<script setup lang="ts">
// Dodaliśmy ikony (emoji) do naszej tablicy z menu
const menuItems = [
  { name: 'Pulpit', path: '/', icon: '🏠' },
  { name: 'Harmonogram', path: '/schedule', icon: '📆' },
  { name: 'EDM / Kartoteka', path: '/records', icon: '📁' },
  { name: 'Raporty', path: '/reports', icon: '📊' }
]
</script>

<template>
  <aside class="sidebar">
    <!-- Górna sekcja: Dwukolorowe Logo -->
    <div class="logo">
      <h2><span class="text-blue">Medi</span><span class="text-green">Sync</span></h2>
    </div>
    
    <!-- Środkowa sekcja: Nawigacja do lewej -->
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
  </aside>
</template>

<style scoped>
/* Jasny motyw paska bocznego */
.sidebar {
  width: 260px;
  background-color: #ffffff;
  border-right: 1px solid #e0e0e0;
  height: 100vh;
  display: flex;
  flex-direction: column;
  box-sizing: border-box; /* Zapewnia, że padding nie psuje szerokości */
}

/* Sekcja Logo */
.logo {
  padding: 24px;
  text-align: center;
  border-bottom: 1px solid #e0e0e0;
  margin-bottom: 8px; /* Odstęp między linią a pierwszym linkiem */
}

.logo h2 {
  margin: 0;
  font-size: 26px;
  font-weight: bold;
}

.text-blue {
  color: #0056b3; /* Głęboki niebieski */
  font-weight: 500;
}

.text-green {
  color: #28a745; /* Medyczna zieleń */
  font-weight: 500;
}

/* Menu nawigacyjne */
.nav-menu {
  display: flex;
  flex-direction: column;
}

/* Pojedynczy link */
.nav-link {
  display: flex;
  align-items: center;
  text-decoration: none;
  color: #333333;
  padding: 16px 24px;
  font-size: 16px;
  font-weight: 600;
  border-right: 4px solid transparent; /* Niewidzialny pasek, żeby tekst nie skakał po najechaniu */
  transition: background-color 0.2s;
}

.nav-link:hover {
  background-color: #f8f9fa; /* Delikatne podświetlenie po najechaniu myszką */
}

/* Ikonki */
.icon {
  margin-right: 12px;
  font-size: 20px;
}

/* Wygląd AKTYWNEJ zakładki (to co na Twoim screenie) */
.nav-link.active {
  background-color: #EEF4FB; /* Jasnoniebieskie tło */
  color: #0056b3; /* Niebieski tekst */
  border-right: 4px solid #0056b3; /* Gruby niebieski pasek po prawej stronie */
}
</style>