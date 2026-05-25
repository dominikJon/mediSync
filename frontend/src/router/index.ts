import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import HomeView from '../views/HomeView.vue'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import ScheduleView from '../views/ScheduleView.vue'
import RecordsView from '../views/RecordsView.vue'
import ReportsView from '../views/ReportsView.vue'
import CompleteProfileView from '../views/CompleteProfileView.vue'
import AdminUsersView from '../views/AdminUsersView.vue'
import AdminAddDoctorView from '../views/AdminAddDoctorView.vue'
import AdminAddStaffView from '../views/AdminAddStaffView.vue'
import ReceptionOfficeView from '../views/ReceptionOfficeView.vue'
import ForgotPasswordView from '../views/ForgotPasswordView.vue'
import ResetPasswordView from '../views/ResetPasswordView.vue'
import ReceptionGraphicView from '../views/ReceptionGraphicView.vue'
import AdminUserView from '../views/AdminUserView.vue'

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
      path: '/forgot-password',
      name: 'forgot-password',
      component: ForgotPasswordView,
      meta: { hideSidebar: true, guestOnly: true }
    },
    {
      path: '/reset-password',
      name: 'reset-password',
      component: ResetPasswordView,
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
    },
    {
      path: '/admin/users',
      name: 'admin-users',
      component: AdminUsersView,
      meta: { requiresAuth: true }
    },
    {
      path: '/admin/user/:id',
      name: 'admin-user',
      component: AdminUserView,
      meta: { requiresAuth: true }
    },
    {
      path: '/admin/add-doctor',
      name: 'admin-add-doctor',
      component: AdminAddDoctorView,
      meta: { requiresAuth: true }
    },
    {
      path: '/admin/add-staff',
      name: 'admin-add-staff',
      component: AdminAddStaffView,
      meta: { requiresAuth: true }
    },
    {
      path: '/reception/office',
      name: 'reception-office',
      component: ReceptionOfficeView,
      meta: { requiresAuth: true }
    },
    {
      path: '/reception/graphic',
      name: 'reception-graphic',
      component: ReceptionGraphicView,
      meta: { requiresAuth: true }
    }
  ]
})

router.beforeEach((to) => {
  const authStore = useAuthStore()

  // 1. Niezalogowany próbuje wejść na chronioną stronę → /login
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return { name: 'login' }
  }

  // 2. Zalogowany z nieuzupełnionym profilem → tylko /complete-profile
  //    Używamy !profil_uzupelniony zamiast === false, żeby łapać też null/undefined
  if (
    authStore.isAuthenticated &&
    !authStore.user?.profil_uzupelniony &&
    to.name !== 'complete-profile'
  ) {
    return { name: 'complete-profile' }
  }

  // 3. Zalogowany z UZUPEŁNIONYM profilem nie powinien wchodzić na /complete-profile
  if (
    authStore.isAuthenticated &&
    authStore.user?.profil_uzupelniony === true &&
    to.name === 'complete-profile'
  ) {
    return { name: 'home' }
  }

  // 4. Zalogowany próbuje wejść na /login lub /register → /
  if (to.meta.guestOnly && authStore.isAuthenticated) {
    return { name: 'home' }
  }
})

export default router