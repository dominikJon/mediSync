import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'

//inicjalizacja apki Vue
const app = createApp(App)
//inicjalizacja Pinia
const pinia = createPinia()

app.use(pinia) // state managament
app.use(router) // podstrony i nawigacja

app.mount('#app')