<template>
  <div class="auth-page">
    <div class="auth-bg">
      <div class="bg-orb orb1"></div>
      <div class="bg-orb orb2"></div>
      <div class="bg-orb orb3"></div>
    </div>
    <div class="auth-container">
      <div class="auth-card">
        <div class="auth-logo">
          <div class="logo-icon">
            <el-icon size="28"><Connection /></el-icon>
          </div>
          <div>
            <h1 class="logo-name">TeamFlow</h1>
            <p class="logo-tagline">协作过程审计平台</p>
          </div>
        </div>

        <h2 class="auth-title">欢迎回来</h2>
        <p class="auth-desc">登录以继续管理您的协作项目</p>

        <el-form :model="form" :rules="rules" ref="formRef" @submit.prevent="handleLogin">
          <el-form-item prop="username">
            <el-input
              v-model="form.username"
              placeholder="用户名"
              size="large"
              prefix-icon="User"
              id="login-username"
            />
          </el-form-item>
          <el-form-item prop="password">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="密码"
              size="large"
              prefix-icon="Lock"
              show-password
              id="login-password"
              @keyup.enter="handleLogin"
            />
          </el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            @click="handleLogin"
            class="auth-btn"
            id="login-submit"
          >
            登录
          </el-button>
        </el-form>

        <div class="auth-footer">
          还没有账号？
          <router-link to="/register" class="auth-link">立即注册</router-link>
        </div>
      </div>

      <div class="auth-features">
        <div v-for="f in features" :key="f.title" class="feature-item">
          <div class="feature-icon">{{ f.icon }}</div>
          <div>
            <div class="feature-title">{{ f.title }}</div>
            <div class="feature-desc">{{ f.desc }}</div>
          </div>
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

const form = reactive({ username: '', password: '' })
const rules = {
  username: [{ required: true, message: '请输入用户名' }],
  password: [{ required: true, message: '请输入密码' }],
}

const features = [
  { icon: '🔍', title: 'Git Graph 协作追踪', desc: '可视化每位成员的贡献过程' },
  { icon: '🤖', title: 'AI 项目经理', desc: '智能拆解任务与生成排期' },
  { icon: '🛡️', title: '防摸鱼贡献审计', desc: '基于证据链的公平评分' },
  { icon: '⚠️', title: '风险预警雷达', desc: '及时识别延期与突击风险' },
]

async function handleLogin() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid: boolean) => {
    if (!valid) return
    loading.value = true
    try {
      await userStore.login(form.username, form.password)
      ElMessage.success('登录成功')
      router.push('/projects')
    } catch (e: any) {
      ElMessage.error(e?.detail || '登录失败，请检查用户名和密码')
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

.auth-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.bg-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.3;
}
.orb1 { width: 400px; height: 400px; background: #4F46E5; top: -100px; left: -100px; }
.orb2 { width: 300px; height: 300px; background: #8B5CF6; bottom: -80px; right: -80px; }
.orb3 { width: 250px; height: 250px; background: #06B6D4; top: 50%; left: 50%; transform: translate(-50%, -50%); }

.auth-container {
  display: flex;
  gap: 60px;
  align-items: center;
  z-index: 1;
  padding: 40px;
}

.auth-card {
  background: rgba(255,255,255,0.05);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 20px;
  padding: 40px;
  width: 400px;
  box-shadow: 0 25px 50px rgba(0,0,0,0.4);
}

.auth-logo {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 32px;
}

.logo-icon {
  width: 52px;
  height: 52px;
  background: linear-gradient(135deg, #4F46E5, #8B5CF6);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.logo-name {
  font-size: 22px;
  font-weight: 800;
  color: white;
  letter-spacing: -0.5px;
}

.logo-tagline {
  font-size: 12px;
  color: rgba(255,255,255,0.5);
  margin-top: 1px;
}

.auth-title {
  font-size: 24px;
  font-weight: 700;
  color: white;
  margin-bottom: 8px;
}

.auth-desc {
  font-size: 14px;
  color: rgba(255,255,255,0.5);
  margin-bottom: 28px;
}

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
  width: 100%;
  height: 46px;
  font-size: 15px;
  font-weight: 600;
  border-radius: 10px !important;
  background: linear-gradient(135deg, #4F46E5, #7C3AED) !important;
  border: none !important;
  margin-top: 8px;
  letter-spacing: 0.3px;
}
.auth-btn:hover { opacity: 0.9; transform: translateY(-1px); }

.auth-footer {
  text-align: center;
  margin-top: 24px;
  color: rgba(255,255,255,0.45);
  font-size: 13px;
}
.auth-link {
  color: #818CF8;
  text-decoration: none;
  font-weight: 500;
}
.auth-link:hover { color: white; }

.auth-features {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.feature-item {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 16px 20px;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px;
  transition: background 0.2s;
}
.feature-item:hover { background: rgba(255,255,255,0.08); }

.feature-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.feature-title {
  font-size: 14px;
  font-weight: 600;
  color: rgba(255,255,255,0.9);
  margin-bottom: 3px;
}

.feature-desc {
  font-size: 12px;
  color: rgba(255,255,255,0.45);
}

@media (max-width: 900px) {
  .auth-features { display: none; }
  .auth-container { padding: 20px; }
}
</style>
