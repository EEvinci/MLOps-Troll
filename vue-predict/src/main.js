import './assets/main.css'
import './permission' // permission control
import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import locale from 'element-plus/es/locale/lang/zh-cn'
const app = createApp(App)
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component)
}
// app.use(ElementPlus)
app.use(createPinia())
app.use(router)
app.use(ElementPlus, {locale})
app.mount('#app')
