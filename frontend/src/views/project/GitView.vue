<template>
  <div class="git-page" v-if="payload">
    <div class="header-row">
      <div>
        <h1 class="page-title">代码提交与冲突风险</h1>
        <div class="page-desc">追踪代码提交证据、分支关系、修改热点与合并风险预警</div>
      </div>
      <el-button type="primary" size="large" @click="showBindDialog = true" v-if="!isRepoBound">
        <el-icon style="margin-right:6px"><Link/></el-icon> 绑定 GitHub 仓库
      </el-button>
      <div v-else class="status-tag green" style="padding: 6px 12px; font-size: 14px;">已绑定: facebook/react</div>
    </div>
    <section class="grid-4">
      <StatCard theme="dark" title="今日提交数" :value="payload.overview.today_commits" footer="较昨日 ↑ 5" :icon="Connection" bg="linear-gradient(135deg, #F472B6 0%, #DB2777 100%)" />
      <StatCard theme="dark" title="活跃分支" :value="payload.overview.active_branches" footer="较上周 ↑ 2" :icon="Share" bg="linear-gradient(135deg, #A78BFA 0%, #7C3AED 100%)" />
      <StatCard theme="dark" title="冲突风险文件" :value="payload.overview.conflict_files" footer="较昨日 ↑ 3" :icon="Warning" bg="linear-gradient(135deg, #22D3EE 0%, #0891B2 100%)" />
      <StatCard theme="dark" title="待处理合并请求" :value="payload.overview.pending_prs" footer="较昨日 ↓ 1" :icon="Tickets" bg="linear-gradient(135deg, #818CF8 0%, #4F46E5 100%)" />
    </section>
    <div class="git-grid">
      <div class="teamflow-card panel">
        <div class="section-title">最近提交</div>
        <div class="commit-list">
          <div v-for="item in payload.recent_commits" :key="item.id" class="commit-item">
            <img :src="item.author.avatar" alt="avatar" />
            <div>
              <div>{{ item.author.name }} · {{ item.commit_hash }}</div>
              <div class="tiny-muted">{{ item.message }} · {{ item.branch_name }}</div>
            </div>
            <span class="status-tag green score-tag">质量分 {{ formatScore(item.quality_score) }}</span>
          </div>
        </div>
      </div>
      <div class="teamflow-card panel">
        <div class="section-title">分支图谱</div>
        <div class="branch-list">
          <div v-for="(item, index) in payload.branch_graph" :key="item.commit" class="branch-timeline-item">
            <div class="branch-track">
              <div class="branch-dot" :class="item.branch === 'main' ? 'primary' : 'secondary'"></div>
              <div class="branch-line" v-if="index !== payload.branch_graph.length - 1"></div>
            </div>
            <div class="branch-content">
              <div class="branch-info">
                <span class="status-tag" :class="item.branch === 'main' ? 'blue' : 'purple'" style="display:flex;align-items:center;padding:2px 8px;">
                  <el-icon style="margin-right:4px;"><Share /></el-icon>{{ item.branch }}
                </span>
                <span class="commit-hash">{{ item.commit }}</span>
              </div>
              <div class="branch-meta">
                <div class="author-info">
                  <img :src="`https://api.dicebear.com/7.x/notionists/svg?seed=${item.author}`" alt="avatar" class="mini-avatar" />
                  <span>{{ item.author }}</span>
                </div>
                <span class="tiny-muted">最近更新</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="teamflow-card panel">
        <div class="section-title">冲突风险预警</div>
        <div class="conflict-list">
          <div v-for="item in payload.conflict_files" :key="item.path" class="conflict-item">
            <div>
              <div>{{ item.path }}</div>
              <div class="tiny-muted">{{ item.suggestion }}</div>
            </div>
            <span :class="['status-tag', item.level === '高' ? 'red' : item.level === '中' ? 'orange' : 'green']">{{ item.level }}</span>
          </div>
        </div>
      </div>
    </div>
    <div class="git-explorer" v-if="isRepoBound" style="margin-top: 18px; margin-bottom: 18px;">
      <div class="teamflow-card panel explorer-layout">
        <div class="explorer-sidebar">
          <div class="explorer-header">
            <el-icon><Folder /></el-icon>
            <strong>react-core</strong>
          </div>
          <div class="tree-item" v-for="node in mockFileTree" :key="node.name" @click="selectFile(node)">
            <el-icon v-if="node.type === 'folder'"><Folder /></el-icon>
            <el-icon v-else><Document /></el-icon>
            <span :style="{ fontWeight: selectedFile?.name === node.name ? 600 : 400, color: selectedFile?.name === node.name ? 'var(--primary)' : 'inherit' }">{{ node.name }}</span>
          </div>
        </div>
        <div class="explorer-content">
          <div class="explorer-toolbar">
            <div style="display:flex; align-items:center; gap:8px;">
              <el-icon><Document /></el-icon>
              <strong>{{ selectedFile?.name || 'README.md' }}</strong>
            </div>
            <div class="explorer-actions">
              <el-button size="small" plain @click="startAiAnalysis"><el-icon style="margin-right:4px;"><Cpu/></el-icon> AI 分析</el-button>
              <el-button size="small" type="primary" @click="startCodeReview">发起 Code Review</el-button>
            </div>
          </div>
          <div class="code-preview app-scroll">
            <pre><code>{{ selectedFile?.content || mockFileTree[5].content }}</code></pre>
          </div>
        </div>
      </div>
    </div>
    <div class="git-bottom">
      <div class="teamflow-card panel">
        <div class="section-title">修改热点热力表（近 7 天）</div>
        <el-table :data="payload.hotspots">
          <el-table-column label="文件路径" prop="path" min-width="220" />
          <el-table-column label="修改次数" prop="changes" width="100" />
          <el-table-column label="增删行数" prop="lines" width="140" />
          <el-table-column label="参与人数" prop="participants" width="100" />
          <el-table-column label="热点指数" width="180">
            <template #default="{ row }">
              <div class="heat-cell">
                <div class="heat-bar">
                  <div class="heat-fill" :style="{ width: `${row.heat}%`, background: heatGradient(row.heat) }"></div>
                </div>
                <strong :style="{ color: heatTextColor(row.heat) }">{{ row.heat }}</strong>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <div class="teamflow-card panel">
        <div class="section-title">仓库绑定信息</div>
        <div class="repo-item"><label>仓库</label><span>{{ payload.repository.name }}</span></div>
        <div class="repo-item"><label>远程地址</label><span>{{ payload.repository.url }}</span></div>
        <div class="repo-item"><label>默认分支</label><span>{{ payload.repository.default_branch }}</span></div>
        <div class="repo-item"><label>同步状态</label><span>{{ payload.repository.sync_status }}</span></div>
        <div class="repo-item"><label>最近同步</label><span>{{ payload.repository.last_synced_at }}</span></div>
      </div>
    </div>

    <el-dialog v-model="showBindDialog" title="绑定 GitHub 仓库" width="min(500px, 90vw)">
      <div v-if="!isParsing">
        <el-form label-position="top">
          <el-form-item label="仓库 URL">
            <el-input v-model="repoUrl" placeholder="https://github.com/..." />
          </el-form-item>
        </el-form>
      </div>
      <div v-else class="parsing-state">
        <el-progress type="dashboard" :percentage="parseProgress" :color="progressColor"></el-progress>
        <div style="margin-top: 16px; font-weight: 600;">{{ parseStatus }}</div>
      </div>
      <template #footer v-if="!isParsing">
        <el-button @click="showBindDialog = false">取消</el-button>
        <el-button type="primary" @click="startParse" :disabled="!repoUrl">开始解析</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { Connection, Share, Tickets, Warning, Folder, Document, Link, Cpu } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import { projectApi } from '@/api'
import StatCard from '@/components/common/StatCard.vue'

const route = useRoute()
const projectId = computed(() => route.params.id as string)
const payload = ref<any>(null)

const showBindDialog = ref(false)
const repoUrl = ref('')
const isParsing = ref(false)
const parseProgress = ref(0)
const parseStatus = ref('')
const isRepoBound = ref(false)

const startParse = () => {
  isParsing.value = true
  parseProgress.value = 0
  parseStatus.value = '正在连接 GitHub API...'
  
  setTimeout(() => {
    parseProgress.value = 35
    parseStatus.value = '正在拉取分支拓扑结构...'
  }, 800)
  
  setTimeout(() => {
    parseProgress.value = 75
    parseStatus.value = '正在解析源码目录...'
  }, 1600)
  
  setTimeout(() => {
    parseProgress.value = 100
    parseStatus.value = '解析完成'
    setTimeout(() => {
      isRepoBound.value = true
      showBindDialog.value = false
      isParsing.value = false
    }, 600)
  }, 2400)
}

const progressColor = [
  { color: '#f56c6c', percentage: 20 },
  { color: '#e6a23c', percentage: 40 },
  { color: '#5cb87a', percentage: 60 },
  { color: '#1989fa', percentage: 80 },
  { color: '#6f7ad3', percentage: 100 },
]

const mockFileTree = [
  { name: 'packages', type: 'folder' },
  { name: 'scripts', type: 'folder' },
  { name: 'src', type: 'folder' },
  { name: '.gitignore', type: 'file' },
  { name: 'package.json', type: 'file', content: '{\n  "name": "react",\n  "version": "18.2.0",\n  "description": "React is a JavaScript library for building user interfaces."\n}' },
  { name: 'README.md', type: 'file', content: '# React\n\nReact is a library for building user interfaces.\n\n## Installation\n\n`npm install react`' },
]

const selectedFile = ref<any>(mockFileTree[5])

const selectFile = (node: any) => {
  if (node.type === 'file') {
    selectedFile.value = node
  }
}

const startAiAnalysis = () => {
  ElMessage.success('正在启动 AI 代码走查...')
}

const startCodeReview = () => {
  ElMessage.success('已自动创建 Code Review 任务卡片')
}

const load = async () => {
  const { data } = await projectApi.git(projectId.value)
  payload.value = data
}

const heatGradient = (heat: number) => {
  if (heat >= 80) return 'linear-gradient(90deg, #f97316 0%, #ef4444 100%)'
  if (heat >= 60) return 'linear-gradient(90deg, #f59e0b 0%, #f97316 100%)'
  if (heat >= 40) return 'linear-gradient(90deg, #14b8a6 0%, #0ea5e9 100%)'
  return 'linear-gradient(90deg, #8b5cf6 0%, #6366f1 100%)'
}

const heatTextColor = (heat: number) => {
  if (heat >= 80) return '#dc2626'
  if (heat >= 60) return '#ea580c'
  if (heat >= 40) return '#0f766e'
  return '#4f46e5'
}

const formatScore = (score: number | null | undefined) => {
  if (score === null || score === undefined || Number.isNaN(score)) return '—'
  return score.toFixed(1)
}

onMounted(load)
</script>

<style scoped>
.git-page,
.git-bottom {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.git-grid,
.git-bottom {
  display: grid;
  gap: 18px;
  grid-template-columns: 1fr 1fr 1fr;
}

.panel {
  padding: 18px;
}

.commit-list,
.branch-list,
.conflict-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-top: 16px;
}

.commit-item,
.conflict-item,
.repo-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

/* Branch Timeline Styles */
.branch-timeline-item {
  display: flex;
  gap: 16px;
  position: relative;
  padding-bottom: 6px;
}

.branch-track {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 24px;
}

.branch-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 3px solid #fff;
  box-shadow: 0 0 0 2px var(--primary);
  background: var(--primary);
  z-index: 1;
}

.branch-dot.secondary {
  box-shadow: 0 0 0 2px var(--purple);
  background: var(--purple);
}

.branch-line {
  flex: 1;
  width: 2px;
  background: #E2E8F0;
  margin-top: 4px;
}

.branch-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: #F8FAFC;
  padding: 14px 16px;
  border-radius: 12px;
  border: 1px solid rgba(15, 23, 42, 0.04);
  transition: all 0.2s;
}

.branch-content:hover {
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);
  border-color: rgba(99, 102, 241, 0.2);
}

.branch-info, .branch-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.commit-hash {
  font-family: monospace;
  color: var(--primary);
  background: rgba(99, 102, 241, 0.1);
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
}

.author-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text);
}

.mini-avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
}

.commit-item img {
  width: 34px;
  height: 34px;
  border-radius: 50%;
}

.score-tag {
  flex-shrink: 0;
  white-space: nowrap;
}

/* Explorer Styles */
.explorer-layout {
  display: flex;
  height: 480px;
  padding: 0;
  overflow: hidden;
}

.explorer-sidebar {
  width: 260px;
  background: #F8FAFC;
  border-right: 1px solid rgba(15, 23, 42, 0.06);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.explorer-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  margin-bottom: 8px;
  color: var(--primary);
  font-size: 15px;
}

.explorer-sidebar .tree-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
  color: #475569;
  font-size: 14px;
  transition: all 0.2s;
}

.explorer-sidebar .tree-item:hover {
  background: #E2E8F0;
}

.explorer-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: #FFFFFF;
}

.explorer-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  border-bottom: 1px solid rgba(15, 23, 42, 0.06);
}

.code-preview {
  flex: 1;
  padding: 20px;
  background: #F1F5F9;
  margin: 16px;
  border-radius: 12px;
  overflow: auto;
}

.code-preview pre {
  margin: 0;
  font-family: Consolas, monospace;
  font-size: 14px;
  line-height: 1.6;
  color: #334155;
}

.parsing-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 30px 0;
}

.repo-item {
  padding: 12px 0;
  border-bottom: 1px solid #f1f5f9;
}

.repo-item label {
  color: var(--text-muted);
}

.heat-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.heat-bar {
  position: relative;
  width: 100px;
  height: 10px;
  overflow: hidden;
  border-radius: 999px;
  background: linear-gradient(180deg, #edf4fa 0%, #e2ebf5 100%);
}

.heat-fill {
  height: 100%;
  border-radius: inherit;
  box-shadow: 0 6px 14px rgba(15, 23, 42, 0.14);
}

@media (max-width: 1200px) {
  .git-grid,
  .git-bottom {
    grid-template-columns: 1fr 1fr;
  }

  .git-grid > :first-child,
  .git-bottom > :first-child {
    grid-column: 1 / -1;
  }
}

@media (max-width: 768px) {
  .git-grid,
  .git-bottom {
    grid-template-columns: 1fr;
  }

  .commit-item,
  .branch-row,
  .conflict-item,
  .repo-item {
    align-items: flex-start;
    gap: 10px;
    flex-direction: column;
  }
}
</style>
