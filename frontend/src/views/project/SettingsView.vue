<template>
  <div class="settings-page">
    <div class="header-row">
      <div>
        <h1 class="page-title">项目设置</h1>
        <div class="page-desc">配置项目基础信息与成员协作，管理项目空间的各项参数与权限</div>
      </div>
      <el-button type="primary" size="large" class="save-btn" @click="save">保存设置</el-button>
    </div>

    <div class="settings-grid">
      <div class="teamflow-card panel">
        <div class="section-title">
          <el-icon style="margin-right: 8px; color: #4F46E5; font-size: 20px; vertical-align: -3px;"><Setting /></el-icon>项目信息
        </div>
        <el-form :model="form" label-position="top">
          <el-form-item label="项目名称"><el-input v-model="form.name" /></el-form-item>
          <el-form-item label="课程名称"><el-input v-model="form.course_name" /></el-form-item>
          <el-form-item label="项目简介"><el-input v-model="form.description" rows="4" type="textarea" /></el-form-item>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
            <el-form-item label="开始日期"><el-date-picker v-model="form.start_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" placeholder="选择开始日期" /></el-form-item>
            <el-form-item label="截止日期"><el-date-picker v-model="form.due_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" placeholder="选择截止日期" /></el-form-item>
          </div>
          <el-form-item label="代码仓库绑定"><el-input v-model="form.repo_url" /></el-form-item>
        </el-form>
      </div>

      <div class="teamflow-card panel">
        <div class="section-title">
          <el-icon style="margin-right: 8px; color: #10B981; font-size: 20px; vertical-align: -3px;"><User /></el-icon>成员管理
        </div>
        <div class="member-row" v-for="member in members" :key="member.user_id">
          <div class="member-info">
            <img :src="member.avatar" alt="avatar" />
            <div>
              <div>{{ member.name }}</div>
              <div class="tiny-muted">{{ member.email }}</div>
            </div>
          </div>
          <span class="status-tag blue">{{ member.role }}</span>
          <span>{{ member.workload }}%</span>
          <span class="status-tag green">{{ member.online_status }}</span>
        </div>
      </div>

      <div class="teamflow-card panel">
        <div class="section-title">
          <el-icon style="margin-right: 8px; color: #F59E0B; font-size: 20px; vertical-align: -3px;"><Message /></el-icon>邀请成员
        </div>
        <el-form :model="inviteForm" label-position="top">
          <el-form-item label="搜索用户">
            <el-select v-model="inviteForm.invitee_id" filterable remote :remote-method="searchUsers" style="width: 100%">
              <el-option v-for="user in searchResults" :key="user.id" :label="`${user.display_name} (${user.email})`" :value="user.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="角色">
            <el-select v-model="inviteForm.role"><el-option label="成员" value="成员" /><el-option label="前端开发" value="前端开发" /><el-option label="后端开发" value="后端开发" /></el-select>
          </el-form-item>
          <el-form-item label="邀请说明">
            <el-input v-model="inviteForm.message" rows="4" type="textarea" />
          </el-form-item>
          <el-button type="primary" @click="sendInvitation" style="background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%); border: none;">发送邀请</el-button>
        </el-form>
      </div>

      <div class="teamflow-card panel">
        <div class="section-title">
          <el-icon style="margin-right: 8px; color: #8B5CF6; font-size: 20px; vertical-align: -3px;"><List /></el-icon>邀请记录
        </div>
        <div class="invite-row" v-for="item in invitations" :key="item.id">
          <div>
            <div>{{ item.invitee?.name }}</div>
            <div class="tiny-muted">{{ item.created_at }}</div>
          </div>
          <span :class="['status-tag', item.status === 'pending' ? 'orange' : item.status === 'accepted' ? 'green' : 'red']">{{ item.status }}</span>
        </div>
      </div>
    </div>

    <div class="teamflow-card panel">
      <div class="section-title">
        <el-icon style="margin-right: 8px; color: #EF4444; font-size: 20px; vertical-align: -3px;"><Lock /></el-icon>成员协作权限矩阵
      </div>
      <el-table :data="permissionRows" stripe style="width: 100%; border-radius: 12px; overflow: hidden; border: 1px solid #f1f5f9;">
        <el-table-column label="角色" prop="role" />
        <el-table-column label="邀请成员" prop="invite" align="center" />
        <el-table-column label="分配任务" prop="assign" align="center" />
        <el-table-column label="查看审计" prop="audit" align="center" />
        <el-table-column label="导出报告" prop="report" align="center" />
        <el-table-column label="删除内容" prop="delete" align="center" />
        <el-table-column label="项目设置" prop="settings" align="center" />
      </el-table>
    </div>

    <div class="teamflow-card panel">
      <div class="section-title">
        <el-icon style="margin-right: 8px; color: #8B5CF6; font-size: 20px; vertical-align: -3px;"><MagicStick /></el-icon>AI 模型配置
        <span class="tiny-muted" style="font-size: 13px; font-weight: 400; margin-left: 8px;">个人配置，仅当前账号生效；留空则使用服务端默认</span>
      </div>
      <el-form :model="llmForm" label-position="top">
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
          <el-form-item label="模型提供商">
            <el-select v-model="llmForm.provider" @change="onProviderChange" style="width: 100%">
              <el-option v-for="p in providers" :key="p.key" :label="providerLabel(p.key)" :value="p.key" />
            </el-select>
          </el-form-item>
          <el-form-item label="模型名称">
            <el-input v-model="llmForm.model" :placeholder="llmForm.provider === 'custom' ? '如 gpt-4o-mini / glm-4-flash' : '留空使用该提供商默认模型'" />
          </el-form-item>
        </div>
        <el-form-item label="Base URL（OpenAI 兼容接口）">
          <el-input v-model="llmForm.base_url" :placeholder="llmForm.provider === 'custom' ? '如 https://api.openai.com/v1' : '留空使用该提供商默认地址'" />
        </el-form-item>
        <el-form-item :label="apiKeyLabel">
          <el-input v-model="llmForm.api_key" type="password" show-password placeholder="sk-..." />
        </el-form-item>
        <div class="llm-actions">
          <el-button :loading="llmTesting" @click="testLlmConfig">测试连接</el-button>
          <el-button type="primary" :loading="llmSaving" @click="saveLlmConfig" class="save-btn">保存配置</el-button>
        </div>
        <div v-if="llmTestResult" :class="['llm-test-result', llmTestResult.ok ? 'ok' : 'fail']">
          {{ llmTestResult.ok ? '✓ ' : '✗ ' }}{{ llmTestResult.message }}
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { Setting, User, Message, List, Lock, MagicStick } from '@element-plus/icons-vue'
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'

import { authApi, llmConfigApi, projectApi } from '@/api'
import { useProjectStore } from '@/stores/project'

const route = useRoute()
const projectStore = useProjectStore()
const projectId = computed(() => route.params.id as string)
const members = ref<any[]>([])
const invitations = ref<any[]>([])
const searchResults = ref<any[]>([])
const form = reactive<any>({
  name: '',
  course_name: '',
  description: '',
  start_date: '',
  due_date: '',
  repo_url: '',
  advisor_name: '',
  advisor_email: '',
  category: '课程设计',
  tags: ['课程设计'],
})
const inviteForm = reactive({
  invitee_id: null as number | null,
  role: '成员',
  message: '',
})

const permissionRows = [
  { role: '组长（Leader）', invite: '√', assign: '√', audit: '√', report: '√', delete: '√', settings: '√' },
  { role: '成员（Member）', invite: '—', assign: '√', audit: '√', report: '√', delete: '—', settings: '—' },
  { role: '教师（Teacher）', invite: '—', assign: '—', audit: '√', report: '√', delete: '—', settings: '√' },
]

const PROVIDER_LABELS: Record<string, string> = {
  mimo: 'MiMo（小米）',
  openai: 'OpenAI',
  deepseek: 'DeepSeek',
  qwen: '通义千问',
  glm: '智谱 GLM',
  moonshot: 'Moonshot（Kimi）',
  custom: '自定义',
}
const providerLabel = (key: string) => PROVIDER_LABELS[key] || key

const llmForm = reactive({ provider: 'mimo', base_url: '', api_key: '', model: '' })
const providers = ref<{ key: string; base_url: string; model: string }[]>([])
const llmKeyMasked = ref('')
const llmSaving = ref(false)
const llmTesting = ref(false)
const llmTestResult = ref<{ ok: boolean; message: string } | null>(null)
const apiKeyLabel = computed(() =>
  llmKeyMasked.value ? `API Key（已保存：${llmKeyMasked.value}，留空则不修改）` : 'API Key',
)

const onProviderChange = () => {
  const preset = providers.value.find((p) => p.key === llmForm.provider)
  if (preset && llmForm.provider !== 'custom') {
    if (!llmForm.base_url) llmForm.base_url = preset.base_url
    if (!llmForm.model) llmForm.model = preset.model
  }
}

const loadLlmConfig = async () => {
  try {
    const { data } = await llmConfigApi.get()
    providers.value = data.providers || []
    llmForm.provider = data.provider || 'mimo'
    llmForm.base_url = data.has_user_override ? data.base_url : ''
    llmForm.model = data.has_user_override ? data.model : ''
    llmForm.api_key = ''
    llmKeyMasked.value = data.api_key_masked || ''
  } catch {
    // 未登录或接口不可用时静默
  }
}

const saveLlmConfig = async () => {
  llmSaving.value = true
  try {
    const { data } = await llmConfigApi.update({
      provider: llmForm.provider,
      base_url: llmForm.base_url,
      api_key: llmForm.api_key,
      model: llmForm.model,
    })
    providers.value = data.providers || providers.value
    llmKeyMasked.value = data.api_key_masked || ''
    llmForm.api_key = ''
    llmForm.base_url = data.has_user_override ? data.base_url : ''
    llmForm.model = data.has_user_override ? data.model : ''
    ElMessage.success('AI 模型配置已保存')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '保存失败')
  } finally {
    llmSaving.value = false
  }
}

const testLlmConfig = async () => {
  llmTesting.value = true
  llmTestResult.value = null
  try {
    const { data } = await llmConfigApi.test({
      provider: llmForm.provider,
      base_url: llmForm.base_url,
      api_key: llmForm.api_key,
      model: llmForm.model,
    })
    llmTestResult.value = { ok: data.ok, message: data.message + (data.reply ? `（模型回复：${data.reply}）` : '') }
  } catch (e: any) {
    llmTestResult.value = { ok: false, message: e?.response?.data?.detail || '测试请求失败' }
  } finally {
    llmTesting.value = false
  }
}

const load = async () => {
  const [detailRes, memberRes, inviteRes] = await Promise.all([
    projectApi.detail(projectId.value),
    projectApi.members(projectId.value),
    projectApi.invitations(projectId.value),
  ])
  Object.assign(form, detailRes.data)
  members.value = memberRes.data
  invitations.value = inviteRes.data
}

const searchUsers = async (keyword: string) => {
  const { data } = await authApi.searchUsers(keyword)
  searchResults.value = data
}

const sendInvitation = async () => {
  if (!inviteForm.invitee_id) return
  await projectApi.sendInvitation(projectId.value, inviteForm)
  ElMessage.success('邀请已发送')
  inviteForm.invitee_id = null
  inviteForm.message = ''
  await load()
}

const save = async () => {
  await projectApi.update(projectId.value, form)
  await projectStore.fetchProject(projectId.value)
  ElMessage.success('设置已保存')
}

onMounted(() => {
  load()
  loadLlmConfig()
})
</script>

<style scoped>
.settings-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.header-row,
.member-row,
.member-info,
.invite-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.settings-grid {
  display: grid;
  gap: 18px;
  grid-template-columns: 1.05fr 1fr;
}

.panel {
  padding: 24px;
  background: #FFFFFF;
  border-radius: 16px;
  border: 1px solid #E2E8F0;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
}

.section-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 24px;
}

.save-btn {
  background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%);
  border: none;
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
  transition: all 0.3s;
}

.save-btn:hover {
  box-shadow: 0 6px 16px rgba(79, 70, 229, 0.4);
  transform: translateY(-1px);
}

:deep(.el-form-item__label) {
  font-weight: 600;
  color: #475569;
}

:deep(.el-input__wrapper), :deep(.el-textarea__inner) {
  background-color: #F8FAFC;
  border: 1px solid #E2E8F0;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.02) !important;
  transition: all 0.2s;
  border-radius: 8px;
}

:deep(.el-input__wrapper:hover), :deep(.el-textarea__inner:hover) {
  background-color: #FFFFFF;
  border-color: #CBD5E1;
}

:deep(.el-input__wrapper.is-focus), :deep(.el-textarea__inner:focus) {
  background-color: #FFFFFF;
  border-color: var(--primary);
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.1) !important;
}

.member-row,
.invite-row {
  padding: 16px;
  background: #FFFFFF;
  border-radius: 12px;
  margin-bottom: 12px;
  border: 1px solid #E2E8F0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
  transition: all 0.2s;
}

.member-row:hover,
.invite-row:hover {
  background: #F8FAFC;
  border-color: #CBD5E1;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
  transform: translateY(-2px);
}

.member-info {
  gap: 12px;
}

.member-info img {
  width: 42px;
  height: 42px;
  border-radius: 50%;
}

@media (max-width: 1200px) {
  .settings-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .header-row,
  .member-row,
  .invite-row {
    align-items: flex-start;
    gap: 10px;
    flex-direction: column;
  }
}

.tiny-muted {
  color: var(--text-muted, #94a3b8);
}

.llm-actions {
  display: flex;
  gap: 12px;
  margin-top: 4px;
}

.llm-test-result {
  margin-top: 12px;
  padding: 10px 14px;
  border-radius: 10px;
  font-size: 13px;
  line-height: 1.5;
}

.llm-test-result.ok {
  background: rgba(16, 185, 129, 0.08);
  color: #047857;
  border: 1px solid rgba(16, 185, 129, 0.25);
}

.llm-test-result.fail {
  background: rgba(239, 68, 68, 0.08);
  color: #b91c1c;
  border: 1px solid rgba(239, 68, 68, 0.25);
}
</style>
