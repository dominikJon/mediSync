import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import HomeView from '../views/HomeView.vue'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import ScheduleView from '../views/ScheduleView.vue'
import RecordsView from '../views/RecordsView.vue'
import ReportsView from '../views/ReportsView.vue'
import CompleteProfileView from '../views/CompleteProfileView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
      meta: { requiresAuth: true }
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { hideSidebar: true, guestOnly: true }
    },
    {
      path: '/register',
      name: 'register',
      component: RegisterView,
      meta: { hideSidebar: true, guestOnly: true }
    },
    {
      path: '/schedule',
      name: 'schedule',
      component: ScheduleView,
      meta: { requiresAuth: true }
    },
    {
      path: '/records',
      name: 'records',
      component: RecordsView,
      meta: { requiresAuth: true }
    },
    {
      path: '/reports',
      name: 'reports',
      component: ReportsView,
      meta: { requiresAuth: true }
    },
    {
      path: '/complete-profile',
      name: 'complete-profile',
      component: CompleteProfileView,
      meta: { hideSidebar: true, requiresAuth: true }
    }
  ]
})

router.beforeEach((to) => {
  const authStore = useAuthStore()

  // Zalogowany z nieuzupełnionym profilem → tylko /complete-profile
  if (
    authStore.isAuthenticated &&
    authStore.user?.profil_uzupelniony === false &&
    to.name !== 'complete-profile'
  ) {
    return { name: 'complete-profile' }
  }

  // Niezalogowany próbuje wejść na chronioną stronę → /login
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return { name: 'login' }
  }

  // Zalogowany próbuje wejść na /login lub /register → /
  if (to.meta.guestOnly && authStore.isAuthenticated) {
    return { name: 'home' }
  }
})

export default router