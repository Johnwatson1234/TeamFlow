<template>
  <div class="git-page">
    <div class="page-header">
      <div><h1 class="page-title">代码提交记录</h1><p class="page-subtitle">{{ commits.length }} 次提交</p></div>
      <el-button type="primary" @click="showCommit = true" id="btn-add-commit"><el-icon><Plus /></el-icon> 记录提交</el-button>
    </div>
    <div v-if="!commits.length && !loading" class="empty-state">
      <div style="font-size:48px">💻</div>
      <p>还没有代码提交记录，开始记录第一次提交</p>
    </div>
    <div class="commits-list">
      <div v-for="c in commits" :key="c.id" class="commit-card">
        <div class="commit-hash">{{ c.commit_hash }}</div>
        <div class="commit-main">
          <div class="commit-msg">{{ c.commit_message }}</div>
          <div class="commit-meta">
            <div class="avatar avatar-sm" :style="{ background: avatarColor(c.author?.nickname) }">{{ c.author?.nickname?.[0]?.toUpperCase() }}</div>
            <span>{{ c.author?.nickname }}</span>
            <span class="commit-branch"><el-icon><Cpu /></el-icon> {{ c.branch_name }}</span>
            <span class="commit-time">{{ formatDate(c.commit_time) }}</span>
          </div>
        </div>
        <div class="commit-stats">
          <span class="additions">+{{ c.added_lines }}</span>
          <span class="deletions">-{{ c.deleted_lines }}</span>
        </div>
      </div>
    </div>

    <el-dialog v-model="showCommit" title="记录代码提交" width="480px">
      <el-form :model="form" label-position="top">
        <el-form-item label="提交说明" required>
          <el-input v-model="form.commit_message" placeholder="feat: 完成用户登录功能" id="commit-msg" />
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="分支名">
              <el-input v-model="form.branch_name" placeholder="main" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="新增/删除行">
              <el-input-number v-model="form.added_lines" :min="0" style="width:49%" />
              <el-input-number v-model="form.deleted_lines" :min="0" style="width:49%; margin-left:2%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="修改文件（逗号分隔）">
          <el-input v-model="form.changed_files" placeholder="src/api.py, src/models.py" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCommit = false">取消</el-button>
        <el-button type="primary" @click="handleCommit" id="confirm-commit">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { collabApi } from '@/api'
import dayjs from 'dayjs'

const route = useRoute()
const projectId = computed(() => Number(route.params.id))
const loading = ref(false)
const commits = ref<any[]>([])
const showCommit = ref(false)
const form = reactive({ commit_message: '', branch_name: 'main', added_lines: 0, deleted_lines: 0, changed_files: '' })

function avatarColor(name?: string) {
  const colors = ['#4F46E5','#7C3AED','#0891B2','#059669','#D97706','#DC2626']
  if (!name) return colors[0]
  return colors[name.charCodeAt(0) % colors.length]
}
function formatDate(dt: string) { return dayjs(dt).format('YYYY/MM/DD HH:mm') }

async function fetchCommits() {
  loading.value = true
  try { commits.value = (await collabApi.commits(projectId.value) as any[]) } finally { loading.value = false }
}

async function handleCommit() {
  if (!form.commit_message) return ElMessage.warning('请输入提交说明')
  try {
    await collabApi.addCommit(projectId.value, form)
    ElMessage.success('提交记录已保存')
    showCommit.value = false
    fetchCommits()
  } catch { ElMessage.error('保存失败') }
}

watch(projectId, fetchCommits)
onMounted(fetchCommits)
</script>

<style scoped>
.git-page { padding: 28px 32px; }
.empty-state { text-align: center; padding: 60px 20px; display: flex; flex-direction: column; align-items: center; gap: 12px; color: var(--text-muted); }
.commits-list { display: flex; flex-direction: column; gap: 8px; }
.commit-card { display: flex; align-items: center; gap: 16px; background: white; border: 1px solid var(--border); border-radius: var(--radius); padding: 14px 18px; box-shadow: var(--shadow-sm); }
.commit-hash { font-family: monospace; font-size: 12px; color: var(--primary); background: #EEF2FF; padding: 3px 8px; border-radius: 6px; flex-shrink: 0; }
.commit-main { flex: 1; min-width: 0; }
.commit-msg { font-size: 14px; font-weight: 600; margin-bottom: 6px; }
.commit-meta { display: flex; align-items: center; gap: 10px; font-size: 12px; color: var(--text-muted); }
.commit-branch { display: flex; align-items: center; gap: 3px; }
.commit-time { margin-left: auto; }
.commit-stats { display: flex; gap: 8px; flex-shrink: 0; font-size: 12px; font-weight: 700; font-family: monospace; }
.additions { color: #22C55E; }
.deletions { color: #EF4444; }
</style>
