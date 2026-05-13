<template>
  <div class="auth-page">
    <div class="auth-bg">
      <div class="bg-orb orb1"></div>
      <div class="bg-orb orb2"></div>
    </div>
    <div class="auth-container">
      <div class="auth-card">
        <div class="auth-logo">
          <div class="logo-icon"><el-icon size="24"><Connection /></el-icon></div>
          <div>
            <h1 class="logo-name">TeamFlow</h1>
            <p class="logo-tagline">协作过程审计平台</p>
          </div>
        </div>

        <h2 class="auth-title">创建账号</h2>
        <p class="auth-desc">加入 TeamFlow，开始高效协作</p>

        <el-form :model="form" :rules="rules" ref="formRef" @submit.prevent="handleRegister">
          <el-form-item prop="username">
            <el-input v-model="form.username" placeholder="用户名（用于登录）" size="large" prefix-icon="User" id="reg-username" />
          </el-form-item>
          <el-form-item prop="nickname">
            <el-input v-model="form.nickname" placeholder="昵称（显示名称）" size="large" prefix-icon="UserFilled" id="reg-nickname" />
          </el-form-item>
          <el-form-item prop="email">
            <el-input v-model="form.email" placeholder="邮箱（选填）" size="large" prefix-icon="Message" id="reg-email" />
          </el-form-item>
          <el-form-item prop="password">
            <el-input v-model="form.password" type="password" placeholder="密码（至少6位）" size="large" prefix-icon="Lock" show-password id="reg-password" />
          </el-form-item>
          <el-button type="primary" size="large" :loading="loading" @click="handleRegister" class="auth-btn" id="reg-submit">
            注册账号
          </el-button>
        </el-form>

        <div class="auth-footer">
          已有账号？<router-link to="/login" class="auth-link">立即登录</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref()
const loading = ref(false)

const form = reactive({ username: '', nickname: '', email: '', password: '' })
const rules = {
  username: [{ required: true, message: '请输入用户名' }, { min: 3, message: '用户名至少3个字符' }],
  nickname: [{ required: true, message: '请输入昵称' }],
  password: [{ required: true, message: '请输入密码' }, { min: 6, message: '密码至少6位' }],
}

async function handleRegister() {
  await formRef.value?.validate(async (valid: boolean) => {
    if (!valid) return
    loading.value = true
    try {
      await userStore.register(form)
      ElMessage.success('注册成功，欢迎加入 TeamFlow！')
      router.push('/projects')
    } catch (e: any) {
      ElMessage.error(e?.detail || '注册失败')
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0F0C29 0%, #302B63 50%, #24243E 100%);
  position: relative;
  overflow: hidden;
}
.auth-bg { position: absolute; inset: 0; pointer-events: none; }
.bg-orb { position: absolute; border-radius: 50%; filter: blur(80px); opacity: 0.3; }
.orb1 { width: 400px; height: 400px; background: #4F46E5; top: -100px; right: -100px; }
.orb2 { width: 300px; height: 300px; background: #8B5CF6; bottom: -80px; left: -80px; }
.auth-container { z-index: 1; padding: 40px; }
.auth-card {
  background: rgba(255,255,255,0.05);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 20px;
  padding: 40px;
  width: 400px;
  box-shadow: 0 25px 50px rgba(0,0,0,0.4);
}
.auth-logo { display: flex; align-items: center; gap: 12px; margin-bottom: 28px; }
.logo-icon {
  width: 46px; height: 46px;
  background: linear-gradient(135deg, #4F46E5, #8B5CF6);
  border-radius: 12px; display: flex; align-items: center; justify-content: center; color: white;
}
.logo-name { font-size: 20px; font-weight: 800; color: white; }
.logo-tagline { font-size: 12px; color: rgba(255,255,255,0.5); }
.auth-title { font-size: 22px; font-weight: 700; color: white; margin-bottom: 6px; }
.auth-desc { font-size: 14px; color: rgba(255,255,255,0.5); margin-bottom: 24px; }
:deep(.el-input__wrapper) {
  background: rgba(255,255,255,0.08) !important;
  border: 1px solid rgba(255,255,255,0.15) !important;
  border-radius: 10px !important;
  box-shadow: none !important;
}
:deep(.el-input__inner) { color: white !important; }
:deep(.el-input__inner::placeholder) { color: rgba(255,255,255,0.35) !important; }
:deep(.el-input__prefix-icon) { color: rgba(255,255,255,0.4) !important; }
.auth-btn {
  width: 100%; height: 46px; font-size: 15px; font-weight: 600;
  border-radius: 10px !important;
  background: linear-gradient(135deg, #4F46E5, #7C3AED) !important;
  border: none !important; margin-top: 8px;
}
.auth-footer { text-align: center; margin-top: 20px; color: rgba(255,255,255,0.45); font-size: 13px; }
.auth-link { color: #818CF8; text-decoration: none; font-weight: 500; }
</style>
