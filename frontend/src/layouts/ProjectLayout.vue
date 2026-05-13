<template>
  <div class="layout">
    <!-- Sidebar -->
    <aside class="sidebar">
      <div class="sidebar-logo">
        <div class="logo-mark">
          <el-icon size="20"><Connection /></el-icon>
        </div>
        <span class="logo-text">TeamFlow</span>
      </div>

      <div class="sidebar-project" v-if="projectStore.current">
        <div class="project-name">{{ projectStore.current.name }}</div>
        <div class="project-course" v-if="projectStore.current.course_name">{{ projectStore.current.course_name }}</div>
      </div>

      <nav class="sidebar-nav">
        <router-link
          v-for="item in navItems"
          :key="item.name"
          :to="`/projects/${projectId}/${item.path}`"
          class="nav-item"
          :class="{ active: isActive(item.path) }"
          :id="`nav-${item.name}`"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
          <span v-if="item.badge" class="nav-badge">{{ item.badge }}</span>
        </router-link>
      </nav>

      <div class="sidebar-bottom">
        <div class="user-info" @click="router.push('/projects')">
          <div class="avatar avatar-sm" :style="{ background: avatarColor(userStore.user?.nickname) }">
            {{ userStore.user?.nickname?.[0]?.toUpperCase() }}
          </div>
          <div class="user-details">
            <div class="user-name">{{ userStore.user?.nickname }}</div>
            <div class="user-role">{{ userStore.user?.role }}</div>
          </div>
        </div>
        <el-button text @click="handleLogout" class="logout-btn" id="logout-btn">
          <el-icon><SwitchButton /></el-icon>
        </el-button>
      </div>
    </aside>

    <!-- Main content -->
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useProjectStore } from '@/stores/project'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const projectStore = useProjectStore()

const projectId = computed(() => Number(route.params.id))

type NavItem = {
  name: string
  path: string
  label: string
  icon: string
  badge?: string
}

const navItems: NavItem[] = [
  { name: 'dashboard', path: '', label: '仪表盘', icon: 'DataBoard' },
  { name: 'tasks', path: 'tasks', label: '任务看板', icon: 'Tickets' },
  { name: 'messages', path: 'messages', label: '即时消息', icon: 'ChatDotRound' },
  { name: 'documents', path: 'documents', label: '协作文档', icon: 'Document' },
  { name: 'files', path: 'files', label: '文件共享', icon: 'FolderOpened' },
  { name: 'graph', path: 'graph', label: 'Git Graph', icon: 'Share' },
  { name: 'contribution', path: 'contribution', label: '贡献审计', icon: 'Trophy' },
  { name: 'risk', path: 'risk', label: '风险雷达', icon: 'Warning' },
  { name: 'git', path: 'git', label: '代码提交', icon: 'Cpu' },
  { name: 'ai', path: 'ai', label: 'AI 项目经理', icon: 'MagicStick' },
  { name: 'project-settings', path: 'settings', label: '项目设置', icon: 'Setting' },
]

function isActive(path: string) {
  const currentPath = route.path
  const projectBase = `/projects/${projectId.value}`
  if (path === '') return currentPath === projectBase || currentPath === `${projectBase}/`
  return currentPath.startsWith(`${projectBase}/${path}`)
}

function avatarColor(name?: string) {
  const colors = ['#4F46E5', '#7C3AED', '#0891B2', '#059669', '#D97706', '#DC2626']
  if (!name) return colors[0]
  return colors[name.charCodeAt(0) % colors.length]
}

function handleLogout() {
  userStore.logout()
  router.push('/login')
}

onMounted(() => {
  if (projectId.value) {
    projectStore.fetchDashboard(projectId.value)
  }
})
</script>

<style scoped>
.layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.sidebar {
  width: 220px;
  flex-shrink: 0;
  background: var(--sidebar-bg);
  display: flex;
  flex-direction: column;
  padding: 0;
  overflow-y: auto;
}

.sidebar-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px 16px;
  border-bottom: 1px solid rgba(255,255,255,0.08);
}

.logo-mark {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #4F46E5, #8B5CF6);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.logo-text {
  font-size: 16px;
  font-weight: 800;
  color: white;
  letter-spacing: -0.3px;
}

.sidebar-project {
  padding: 12px 16px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
  background: rgba(255,255,255,0.03);
}

.project-name {
  font-size: 13px;
  font-weight: 600;
  color: rgba(255,255,255,0.9);
  truncate: ellipsis;
  white-space: nowrap;
  overflow: hidden;
}

.project-course {
  font-size: 11px;
  color: rgba(255,255,255,0.4);
  margin-top: 2px;
}

.sidebar-nav {
  flex: 1;
  padding: 10px 10px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 12px;
  border-radius: 8px;
  color: var(--sidebar-text);
  text-decoration: none;
  font-size: 13.5px;
  font-weight: 500;
  transition: all 0.15s;
  position: relative;
}

.nav-item:hover {
  background: rgba(255,255,255,0.08);
  color: white;
}

.nav-item.active {
  background: rgba(79,70,229,0.35);
  color: white;
}

.nav-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 60%;
  background: #818CF8;
  border-radius: 0 2px 2px 0;
}

.nav-badge {
  margin-left: auto;
  background: var(--danger);
  color: white;
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 8px;
  font-weight: 600;
}

.sidebar-bottom {
  padding: 12px;
  border-top: 1px solid rgba(255,255,255,0.08);
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  cursor: pointer;
  padding: 6px 8px;
  border-radius: 8px;
  transition: background 0.15s;
}
.user-info:hover { background: rgba(255,255,255,0.06); }

.user-details { min-width: 0; }
.user-name { font-size: 12.5px; font-weight: 600; color: rgba(255,255,255,0.9); truncate: ellipsis; }
.user-role { font-size: 11px; color: rgba(255,255,255,0.4); }

.logout-btn { color: rgba(255,255,255,0.35) !important; }
.logout-btn:hover { color: white !important; }

.main-content {
  flex: 1;
  overflow-y: auto;
  background: var(--bg);
}
</style>
