import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'
import './style.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(ElementPlus)

app.directive('click-outside', {
  beforeMount(el, binding) {
    const element = el as HTMLElement & { __clickOutsideHandler__?: EventListener }
    element.__clickOutsideHandler__ = (event: Event) => {
      if (!(el === event.target || el.contains(event.target as Node))) {
        binding.value(event)
      }
    }
    document.addEventListener('click', element.__clickOutsideHandler__)
  },
  unmounted(el) {
    const element = el as HTMLElement & { __clickOutsideHandler__?: EventListener }
    if (element.__clickOutsideHandler__) {
      document.removeEventListener('click', element.__clickOutsideHandler__)
    }
  },
})

// Register all icons
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.mount('#app')
