<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '../stores/auth'
import PacjentHome from '../components/home/PacjentHome.vue'
import LekarzHome from '../components/home/LekarzHome.vue'
import AdminHome from '../components/home/AdminHome.vue'
import RejestratorHome from '../components/home/RejestratorHome.vue'

const authStore = useAuthStore()
const rola = computed(() => authStore.user?.rola)
</script>

<template>
  <PacjentHome     v-if="rola === 'pacjent'" />
  <LekarzHome      v-else-if="rola === 'lekarz'" />
  <AdminHome       v-else-if="rola === 'admin'" />
  <RejestratorHome v-else-if="rola === 'rejestracja'" />
  <div v-else class="brak">
    Nieznana rola użytkownika.
  </div>
</template>

<style scoped>
.brak {
  padding: 32px;
  color: #94a3b8;
  font-size: 14px;
}
</style>