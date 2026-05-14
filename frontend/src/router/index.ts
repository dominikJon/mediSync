import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import HomeView from '../views/HomeView.vue'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import ScheduleView from '../views/ScheduleView.vue'
import RecordsView from '../views/RecordsView.vue'
import ReportsView from '../views/ReportsView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { hideSidebar: true } 
    },
    {
      path: '/register',
      name: 'register',
      component: RegisterView,
      meta: { hideSidebar: true }
    },
    {
      path: '/schedule',
      name: 'schedule',
      component: ScheduleView,
      meta: { hideSidebar: true }
    },
    { 
      path: '/records',
      name: 'records',
      component: RecordsView,
      meta: { hideSidebar: true }
    },
    {
      path: '/reports',
      name: 'reports',
      component: ReportsView,
      meta: { hideSidebar: true }
    }
  ]
})

// 'bramkarz' funkcja wywolywana przed kazda zmiana strony
router.beforeEach((to) => {
  const authStore = useAuthStore()
  
  // jeśli strona wymaga tokena a użytkownik nie jest zalogowany:
  if (to.name !== 'login' && to.name !== 'register' && !authStore.isAuthenticated) {
    return { name: 'login' } // wyrzuć do panelu logowania
  }
  // brak return = przepuść
})

export default router