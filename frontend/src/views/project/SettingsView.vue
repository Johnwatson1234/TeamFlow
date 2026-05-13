<template>
  <div class="settings-page">
    <div class="page-header">
      <h1 class="page-title">项目设置</h1>
    </div>
    <div class="settings-layout">
      <!-- Project info -->
      <div class="card">
        <h3 class="section-title">项目信息</h3>
        <el-form :model="form" label-position="top" v-if="project">
          <el-form-item label="项目名称">
            <el-input v-model="form.name" id="settings-name" />
          </el-form-item>
          <el-form-item label="项目简介">
            <el-input v-model="form.description" type="textarea" :rows="3" />
          </el-form-item>
          <el-form-item label="课程名称">
            <el-input v-model="form.course_name" />
          </el-form-item>
          <el-form-item label="截止日期">
            <el-date-picker v-model="form.deadline" type="datetime" style="width:100%" />
          </el-form-item>
          <el-button type="primary" @click="saveSettings" :loading="saving" id="btn-save-settings">保存设置</el-button>
        </el-form>
      </div>

      <!-- Members management -->
      <div class="card">
        <h3 class="section-title">成员管理</h3>
        <div class="members-list">
          <div v-for="m in members" :key="m.user_id" class="member-row">
            <div class="avatar avatar-sm" :style="{ background: avatarColor(m.user?.nickname) }">
              {{ m.user?.nickname?.[0]?.toUpperCase() }}
            </div>
            <div class="member-info">
              <div class="member-name">{{ m.user?.nickname }}</div>
              <div class="member-username">@{{ m.user?.username }}</div>
            </div>
            <el-select v-model="m.role" size="small" style="width:100px" @change="() => updateRole(m)">
              <el-option label="组长" value="leader" />
              <el-option label="成员" value="member" />
              <el-option label="教师" value="teacher" />
            </el-select>
            <el-button text type="danger" size="small" @click="removeMember(m.user_id)"><el-icon><Delete /></el-icon></el-button>
          </div>
        </div>

        <div class="invite-section">
          <h4>邀请成员</h4>
          <div class="invite-row">
            <el-input v-model="searchQ" placeholder="搜索用户名或昵称" @input="searchUsers" id="search-user" />
            <el-select v-model="inviteRole" style="width:100px">
              <el-option label="成员" value="member" />
              <el-option label="组长" value="leader" />
            </el-select>
          </div>
          <div v-if="searchResults.length" class="search-results">
            <div v-for="u in searchResults" :key="u.id" class="search-result-item" @click="invite(u)">
              <div class="avatar avatar-sm" :style="{ background: avatarColor(u.nickname) }">{{ u.nickname?.[0]?.toUpperCase() }}</div>
              <div><div class="member-name">{{ u.nickname }}</div><div class="member-username">@{{ u.username }}</div></div>
              <el-button size="small" type="primary">邀请</el-button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { projectApi, authApi } from '@/api'

const route = useRoute()
const projectId = computed(() => Number(route.params.id))
const project = ref<any>(null)
const members = ref<any[]>([])
const saving = ref(false)
const searchQ = ref('')
const searchResults = ref<any[]>([])
const inviteRole = ref('member')

const form = reactive({ name: '', description: '', course_name: '', deadline: null as any })

function avatarColor(name?: string) {
  const colors = ['#4F46E5','#7C3AED','#0891B2','#059669','#D97706','#DC2626']
  if (!name) return colors[0]
  return colors[name.charCodeAt(0) % colors.length]
}

async function fetchProject() {
  try {
    const p: any = await projectApi.get(projectId.value)
    project.value = p
    Object.assign(form, { name: p.name, description: p.description || '', course_name: p.course_name || '', deadline: p.deadline })
    const ms: any = await projectApi.members(projectId.value)
    members.value = ms
  } catch { ElMessage.error('加载失败') }
}

async function saveSettings() {
  saving.value = true
  try {
    await projectApi.update(projectId.value, form)
    ElMessage.success('设置已保存')
  } catch { ElMessage.error('保存失败') } finally { saving.value = false }
}

async function searchUsers() {
  if (!searchQ.value || searchQ.value.length < 2) { searchResults.value = []; return }
  try { searchResults.value = (await authApi.searchUsers(searchQ.value) as any[]) } catch {}
}

async function invite(user: any) {
  try {
    await projectApi.inviteMember(projectId.value, { user_id: user.id, role: inviteRole.value })
    ElMessage.success(`已邀请 ${user.nickname}`)
    searchResults.value = []
    searchQ.value = ''
    fetchProject()
  } catch { ElMessage.error('邀请失败') }
}

async function removeMember(userId: number) {
  try {
    await projectApi.removeMember(projectId.value, userId)
    members.value = members.value.filter(m => m.user_id !== userId)
    ElMessage.success('成员已移除')
  } catch { ElMessage.error('移除失败') }
}

async function updateRole(m: any) {
  // Role update through re-invite
  try {
    await projectApi.inviteMember(projectId.value, { user_id: m.user_id, role: m.role })
    ElMessage.success('角色已更新')
  } catch { ElMessage.error('更新失败') }
}

watch(projectId, fetchProject)
onMounted(fetchProject)
</script>

<style scoped>
.settings-page { padding: 28px 32px; }
.settings-layout { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.card { background: white; border: 1px solid var(--border); border-radius: var(--radius); padding: 24px; box-shadow: var(--shadow-sm); }
.section-title { font-size: 15px; font-weight: 700; margin-bottom: 16px; }
.members-list { display: flex; flex-direction: column; gap: 10px; margin-bottom: 20px; }
.member-row { display: flex; align-items: center; gap: 10px; padding: 8px 0; border-bottom: 1px solid var(--border); }
.member-row:last-child { border-bottom: none; }
.member-info { flex: 1; }
.member-name { font-size: 13px; font-weight: 600; }
.member-username { font-size: 11px; color: var(--text-muted); }
.invite-section { border-top: 1px solid var(--border); padding-top: 16px; }
.invite-section h4 { font-size: 13px; font-weight: 600; margin-bottom: 10px; }
.invite-row { display: flex; gap: 8px; margin-bottom: 10px; }
.search-results { border: 1px solid var(--border); border-radius: var(--radius-sm); overflow: hidden; }
.search-result-item { display: flex; align-items: center; gap: 10px; padding: 10px 12px; cursor: pointer; border-bottom: 1px solid var(--border); }
.search-result-item:last-child { border-bottom: none; }
.search-result-item:hover { background: var(--bg); }
</style>
