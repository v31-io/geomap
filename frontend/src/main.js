import { createApp } from 'vue'
import VueKeycloak from '@dsb-norge/vue-keycloak-js'
import App from './App.vue'

const app = createApp(App)

app.use(VueKeycloak, {
  init: {
    onLoad: 'login-required',
    checkLoginIframe: false
  },
  config: {
    url: import.meta.env.VITE_KEYCLOAK_URL,
    realm: 'default',
    clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID
  },
  onInitError: (error) => console.error('Keycloak initialization error:', error),
  onReady: (keycloak) => {
    if (!keycloak.hasResourceRole('access')) {
      keycloak.logout()
    }
    app.mount('#app')
  }
})