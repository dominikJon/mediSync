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

  display: flex;
  flex-direction: column;  
  align-items: center;    
  justify-content: flex-start; 
}

/* omijamy .full-width (czyli logowanie/rejestrację/odzyskiwanie hasła)
   zwezony widok dla RecordView */
.main-content:not(.full-width) > .page:not(.narrow-page),
.main-content:not(.full-width) > .grafik-view:not(.narrow-page) {
  width: 90% !important;
  max-width: 1600px !important;
  margin: 0 auto !important;
}

.main-content > * {
  width: 100%;
}

/* wyglad bez sidebar (Ekrany logowania / rejestracji) */
.main-content.full-width {
  padding: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #F8FAFC;
}
</style>