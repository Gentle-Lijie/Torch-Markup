import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../utils/api'

const STORAGE_KEY = 'torch-markup-token'
const USER_STORAGE_KEY = 'torch-markup-user'

export const useUserStore = defineStore('user', () => {
  // 尝试从 localStorage 恢复用户信息
  const savedUser = localStorage.getItem(USER_STORAGE_KEY)
  const user = ref(savedUser ? JSON.parse(savedUser) : null)
  const token = ref(localStorage.getItem(STORAGE_KEY) || null)
  const initialized = ref(!token.value) // 没有 token 时视为已初始化

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.is_admin || false)

  async function login(username, password) {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)

    const response = await api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })

    token.value = response.data.access_token
    user.value = response.data.user
    localStorage.setItem(STORAGE_KEY, token.value)
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(response.data.user))
    initialized.value = true

    return response.data
  }

  async function register(username, password, email) {
    const response = await api.post('/auth/register', {
      username,
      password,
      email: email || null
    })
    return response.data
  }

  async function fetchUser() {
    if (!token.value) {
      initialized.value = true
      return null
    }

    try {
      const response = await api.get('/auth/me')
      user.value = response.data
      localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(response.data))
      initialized.value = true
      return response.data
    } catch (error) {
      logout()
      throw error
    }
  }

  function logout() {
    user.value = null
    token.value = null
    initialized.value = true
    localStorage.removeItem(STORAGE_KEY)
    localStorage.removeItem(USER_STORAGE_KEY)
  }

  // 初始化时验证 token 有效性（后台刷新用户信息）
  if (token.value && user.value) {
    // 已有缓存的用户信息，标记为已初始化，后台刷新
    initialized.value = true
    fetchUser().catch(() => {})
  } else if (token.value) {
    // 有 token 但没有用户信息，需要获取
    fetchUser().catch(() => {})
  }

  return {
    user,
    token,
    initialized,
    isLoggedIn,
    isAdmin,
    login,
    register,
    fetchUser,
    logout
  }
})
