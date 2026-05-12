<script setup lang="ts">
import { RouterView } from 'vue-router'
import Sidebar from './components/sidebar.vue'
</script>

<template>
  <div class="app-layout">
    <Sidebar v-if="!$route.meta.hideSidebar" />
    
    <main :class="['main-content', { 'full-width': $route.meta.hideSidebar }]">
      <RouterView />
    </main>
  </div>
</template>

<style>
/* Globalny reset */
#app {
  width: 100%;
  max-width: 100%;
  margin: 0;
  padding: 0;
}

body {
  margin: 0;
  padding: 0;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background-color: #F8FAFC;
}

/* glowny uklad strony */
.app-layout {
  display: flex; 
  min-height: 100vh;
}

/* z sidebar */
.main-content {
  flex: 1; 
  padding: 32px;
  overflow-y: auto;
}

/* wyglad bez sidebar */
.main-content.full-width {
  padding: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #F8FAFC;
}
</style>