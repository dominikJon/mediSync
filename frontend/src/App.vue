<script setup lang="ts">
// import sidebar
import Sidebar from './components/sidebar.vue'
</script>

<template>
  <div class="app-layout">
    <Sidebar />
    <main class="main-content">
      <RouterView />
    </main>
  </div>
</template>

<style>
/* globalne style */
body {
  margin: 0;
  padding: 0;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background-color: #F8FAFC; 
}

.app-layout {
  display: flex; 
  min-height: 100vh;
}

/* glowna tresc */
.main-content {
  flex: 1; 
  padding: 32px;
  overflow-y: auto;
}
</style>