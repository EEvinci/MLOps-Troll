import router from './router'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'
import { getToken } from '@/utils/auth'
NProgress.configure({ showSpinner: false });
const whiteList = ['/login'];

router.beforeEach((to, from, next) => {
  NProgress.start()
  if (getToken()) {

    if (to.path === '/login') {
      next()
      NProgress.done()
    } else if (whiteList.indexOf(to.path) !== -1) {
      next()
    }  else {
        next()
      }

  } else {
    // 没有token
    if (whiteList.indexOf(to.path) !== -1) {
      // 在免登录白名单，直接进入
      next()
    } else {
      next(`/login?redirect=${to.fullPath}`) // 否则全部重定向到登录页
      NProgress.done()
    }
  }
})

router.afterEach(() => {
  NProgress.done()
})
