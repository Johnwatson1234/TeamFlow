import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api'

export const useUserStore = defineStore('user', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<any | null>(null)

  const isLoggedIn = computed(() => !!token.value)

  async function login(username: string, password: string) {
    const res: any = await authApi.login({ username, password })
    token.value = res.access_token
    user.value = res.user
    localStorage.setItem('token', res.access_token)
    return res
  }

  async function register(data: any) {
    const res: any = await authApi.register(data)
    token.value = res.access_token
    user.value = res.user
    localStorage.setItem('token', res.access_token)
    return res
  }

  async function fetchMe() {
    if (!token.value) return
    try {
      const res: any = await authApi.me()
      user.value = res
    } catch {
      logout()
    }
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
  }

  return { token, user, isLoggedIn, login, register, fetchMe, logout }
})
