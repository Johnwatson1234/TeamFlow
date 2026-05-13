<template>
  <div class="projects-page">
    <!-- Top bar -->
    <header class="top-bar">
      <div class="top-logo">
        <div class="logo-icon"><el-icon size="20"><Connection /></el-icon></div>
        <span class="logo-text">TeamFlow</span>
      </div>
      <div class="top-actions">
        <el-button type="primary" @click="showCreate = true" id="btn-create-project">
          <el-icon><Plus /></el-icon> 新建项目
        </el-button>
        <div class="user-pill" @click="showUserMenu = !showUserMenu">
          <div class="avatar avatar-sm" :style="{ background: avatarColor(userStore.user?.nickname) }">
            {{ userStore.user?.nickname?.[0]?.toUpperCase() }}
          </div>
          <span>{{ userStore.user?.nickname }}</span>
          <el-icon><ArrowDown /></el-icon>
        </div>
        <div v-if="showUserMenu" class="user-menu" v-click-outside="() => showUserMenu = false">
          <div class="menu-item" @click="handleLogout">
            <el-icon><SwitchButton /></el-icon> 退出登录
          </div>
        </div>
      </div>
    </header>

    <div class="projects-body">
      <!-- Hero -->
      <div class="hero-section">
        <h1 class="hero-title">我的项目</h1>
        <p class="hero-subtitle">管理你的课程设计小组，追踪每一行协作过程</p>
      </div>

      <!-- Stats bar -->
      <div class="stats-bar" v-if="projects.length > 0">
        <div class="stat-item">
          <span class="stat-num">{{ projects.length }}</span>
          <span class="stat-label">个项目</span>
        </div>
        <div class="stat-item">
          <span class="stat-num">{{ activeCount }}</span>
          <span class="stat-label">活跃中</span>
        </div>
        <div class="stat-item">
          <span class="stat-num">{{ archivedCount }}</span>
          <span class="stat-label">已归档</span>
        </div>
      </div>

      <!-- Projects grid -->
      <div v-if="loading" class="loading-state">
        <el-skeleton :rows="3" animated />
      </div>
      <div v-else-if="projects.length === 0" class="empty-state">
        <div class="empty-icon">🚀</div>
        <h3>还没有项目</h3>
        <p>创建你的第一个课程设计项目，开始协作之旅</p>
        <el-button type="primary" size="large" @click="showCreate = true">
          <el-icon><Plus /></el-icon> 创建项目
        </el-button>
      </div>
      <div v-else class="projects-grid">
        <div
          v-for="project in projects"
          :key="project.id"
          class="project-card"
          @click="router.push(`/projects/${project.id}`)"
          :id="`project-${project.id}`"
        >
          <div class="project-cover" :style="{ background: projectGradient(project.id) }">
            <span class="project-initial">{{ project.name[0] }}</span>
            <div class="project-status-badge" :class="project.status">
              {{ project.status === 'active' ? '进行中' : '已归档' }}
            </div>
          </div>
          <div class="project-info">
            <h3 class="project-name">{{ project.name }}</h3>
            <p class="project-desc">{{ project.description || '暂无描述' }}</p>
            <div class="project-meta">
              <span v-if="project.course_name" class="tag tag-primary">{{ project.course_name }}</span>
              <span class="project-date">{{ formatDate(project.created_at) }}</span>
            </div>
            <div v-if="project.deadline" class="project-deadline">
              <el-icon><Clock /></el-icon>
              截止 {{ formatDate(project.deadline) }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Create project dialog -->
    <el-dialog v-model="showCreate" title="创建新项目" width="500px" :close-on-click-modal="false">
      <el-form :model="createForm" ref="createFormRef" label-position="top">
        <el-form-item label="项目名称" required>
          <el-input v-model="createForm.name" placeholder="例如：软件工程课程设计" id="create-proj-name" />
        </el-form-item>
        <el-form-item label="项目简介">
          <el-input v-model="createForm.description" type="textarea" :rows="2" placeholder="简单描述项目目标..." />
        </el-form-item>
        <el-form-item label="课程名称">
          <el-input v-model="createForm.course_name" placeholder="例如：软件工程" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="开始日期">
              <el-date-picker v-model="createForm.start_date" type="date" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="截止日期">
              <el-date-picker v-model="createForm.deadline" type="datetime" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreate" id="confirm-create-project">创建项目</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { projectApi } from '@/api'
import dayjs from 'dayjs'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const creating = ref(false)
const showCreate = ref(false)
const showUserMenu = ref(false)
const projects = ref<any[]>([])

const createForm = reactive({
  name: '', description: '', course_name: '', start_date: null as any, deadline: null as any
})

const activeCount = computed(() => projects.value.filter(p => p.status === 'active').length)
const archivedCount = computed(() => projects.value.filter(p => p.status !== 'active').length)

function avatarColor(name?: string) {
  const colors = ['#4F46E5', '#7C3AED', '#0891B2', '#059669', '#D97706', '#DC2626']
  if (!name) return colors[0]
  return colors[name.charCodeAt(0) % colors.length]
}

function projectGradient(id: number) {
  const gradients = [
    'linear-gradient(135deg, #4F46E5, #7C3AED)',
    'linear-gradient(135deg, #0891B2, #06B6D4)',
    'linear-gradient(135deg, #059669, #22C55E)',
    'linear-gradient(135deg, #D97706, #F59E0B)',
    'linear-gradient(135deg, #DC2626, #EF4444)',
    'linear-gradient(135deg, #7C3AED, #EC4899)',
  ]
  return gradients[id % gradients.length]
}

function formatDate(dt: string) {
  if (!dt) return ''
  return dayjs(dt).format('YYYY/MM/DD')
}

async function fetchProjects() {
  loading.value = true
  try {
    const res: any = await projectApi.list()
    projects.value = res
  } catch {
    ElMessage.error('加载项目失败')
  } finally {
    loading.value = false
  }
}

async function handleCreate() {
  if (!createForm.name) return ElMessage.warning('请输入项目名称')
  creating.value = true
  
  // Format data for backend
  const payload = {
    ...createForm,
    start_date: createForm.start_date ? dayjs(createForm.start_date).format('YYYY-MM-DD') : null,
    deadline: createForm.deadline ? dayjs(createForm.deadline).toISOString() : null
  }

  try {
    const res: any = await projectApi.create(payload)
    projects.value.unshift(res)
    showCreate.value = false
    // Clear form
    Object.assign(createForm, { name: '', description: '', course_name: '', start_date: null, deadline: null })
    ElMessage.success('项目创建成功')
    router.push(`/projects/${res.id}`)
  } catch (e: any) {
    console.error('Project creation error:', e)
    let msg = '创建失败'
    if (e.detail) {
      if (Array.isArray(e.detail)) {
        msg = e.detail.map((err: any) => `${err.loc.join('.')}: ${err.msg}`).join('; ')
      } else {
        msg = e.detail
      }
    }
    ElMessage.error(msg)
  } finally {
    creating.value = false
  }
}

function handleLogout() {
  userStore.logout()
  router.push('/login')
}

onMounted(fetchProjects)
</script>

<style scoped>
.projects-page { min-height: 100vh; background: var(--bg); }

.top-bar {
  background: white;
  border-bottom: 1px solid var(--border);
  padding: 0 32px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: var(--shadow-sm);
}

.top-logo { display: flex; align-items: center; gap: 10px; }
.logo-icon {
  width: 36px; height: 36px;
  background: linear-gradient(135deg, #4F46E5, #8B5CF6);
  border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white;
}
.logo-text { font-size: 18px; font-weight: 800; color: var(--text); }

.top-actions { display: flex; align-items: center; gap: 12px; position: relative; }

.user-pill {
  display: flex; align-items: center; gap: 8px;
  padding: 6px 12px;
  border-radius: 20px;
  border: 1px solid var(--border);
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: background 0.15s;
}
.user-pill:hover { background: var(--bg-dark); }

.user-menu {
  position: absolute; top: 46px; right: 0;
  background: white; border: 1px solid var(--border); border-radius: var(--radius);
  box-shadow: var(--shadow-lg); width: 160px; overflow: hidden; z-index: 200;
}
.menu-item {
  display: flex; align-items: center; gap: 8px;
  padding: 12px 16px; cursor: pointer; font-size: 13px; transition: background 0.15s;
}
.menu-item:hover { background: var(--bg); }

.projects-body { max-width: 1200px; margin: 0 auto; padding: 40px 32px; }

.hero-section { margin-bottom: 32px; }
.hero-title { font-size: 28px; font-weight: 800; color: var(--text); }
.hero-subtitle { font-size: 15px; color: var(--text-muted); margin-top: 6px; }

.stats-bar {
  display: flex; gap: 32px;
  padding: 16px 24px;
  background: white; border: 1px solid var(--border);
  border-radius: var(--radius); margin-bottom: 28px;
  box-shadow: var(--shadow-sm);
}
.stat-item { display: flex; align-items: baseline; gap: 6px; }
.stat-num { font-size: 24px; font-weight: 800; color: var(--primary); }
.stat-label { font-size: 13px; color: var(--text-muted); }

.loading-state { padding: 20px; }

.empty-state {
  text-align: center; padding: 80px 20px;
}
.empty-icon { font-size: 64px; margin-bottom: 16px; }
.empty-state h3 { font-size: 20px; font-weight: 700; margin-bottom: 8px; }
.empty-state p { color: var(--text-muted); margin-bottom: 24px; }

.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.project-card {
  background: white;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border);
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  box-shadow: var(--shadow-sm);
}
.project-card:hover { transform: translateY(-4px); box-shadow: var(--shadow-lg); }

.project-cover {
  height: 100px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  position: relative;
}

.project-initial {
  font-size: 40px;
  font-weight: 800;
  color: rgba(255,255,255,0.8);
  line-height: 1;
}

.project-status-badge {
  position: absolute; top: 12px; right: 12px;
  padding: 3px 10px; border-radius: 10px;
  font-size: 11px; font-weight: 600;
  background: rgba(255,255,255,0.2); color: white;
}
.project-status-badge.active { background: rgba(34,197,94,0.3); }

.project-info { padding: 16px; }
.project-name { font-size: 16px; font-weight: 700; margin-bottom: 6px; }
.project-desc { font-size: 13px; color: var(--text-muted); line-height: 1.5; margin-bottom: 12px;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }

.project-meta { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.project-date { font-size: 12px; color: var(--text-light); }

.project-deadline {
  display: flex; align-items: center; gap: 4px;
  font-size: 12px; color: var(--warning);
}
</style>
