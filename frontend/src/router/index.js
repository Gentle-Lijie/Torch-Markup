import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../stores/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { guest: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue'),
    meta: { guest: true }
  },
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/Home.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/annotate/:datasetId',
    name: 'Annotation',
    component: () => import('../views/Annotation.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/tutorial',
    name: 'Tutorial',
    component: () => import('../views/Tutorial.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/admin',
    name: 'Admin',
    component: () => import('../views/Admin/Layout.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      {
        path: '',
        name: 'AdminDashboard',
        component: () => import('../views/Admin/Dashboard.vue')
      },
      {
        path: 'datasets',
        name: 'AdminDatasets',
        component: () => import('../views/Admin/Datasets.vue')
      },
      {
        path: 'categories/:datasetId',
        name: 'AdminCategories',
        component: () => import('../views/Admin/Categories.vue')
      },
      {
        path: 'users',
        name: 'AdminUsers',
        component: () => import('../views/Admin/Users.vue')
      },
      {
        path: 'statistics',
        name: 'AdminStatistics',
        component: () => import('../views/Admin/Statistics.vue')
      },
      {
        path: 'export',
        name: 'AdminExport',
        component: () => import('../views/Admin/Export.vue')
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()

  // 等待用户信息初始化完成
  if (!userStore.initialized && userStore.token) {
    try {
      await userStore.fetchUser()
    } catch {
      // 忽略错误，fetchUser 内部会处理
    }
  }

  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else if (to.meta.requiresAdmin && !userStore.isAdmin) {
    next({ name: 'Home' })
  } else if (to.meta.guest && userStore.isLoggedIn) {
    next({ name: 'Home' })
  } else {
    next()
  }
})

export default router
