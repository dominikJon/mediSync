import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import HomeView from '../views/HomeView.vue'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'

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
    }
  ]
})

// 'bramkarz' funkcja wywolywana przed kazda zmiana strony
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  // jesli strona wymaga tokena a uzytkownik nie jest zalogowany:
  if (to.name !== 'login' && to.name !== 'register' && !authStore.isAuthenticated) {
    next({ name: 'login' }) // wyrzuc do panelu logowania
  } else {
    next() // wpusc
  }
})

export default router