<template>
  <div v-if="dashboard" class="dashboard-page">
    <div class="header-row">
      <div>
        <h1 class="page-title">项目仪表盘</h1>
        <div class="page-desc">数据更新时间：{{ projectStore.currentProject?.updated_at }}</div>
      </div>
      <div class="header-actions">
        <el-button @click="goCareer">成员画像</el-button>
        <el-button @click="refreshContribution">刷新贡献分</el-button>
        <el-button type="primary" @click="scanRisk">扫描风险</el-button>
      </div>
    </div>

    <section class="grid-4">
      <StatCard theme="dark" title="任务完成率" :value="`${dashboard.stats.completion_rate}%`" :footer="`已完成 ${dashboard.stats.completed_count} / ${dashboard.stats.task_total}`" :icon="PieChart" bg="linear-gradient(135deg, #F472B6 0%, #DB2777 100%)" />
      <StatCard theme="dark" title="进行中任务" :value="dashboard.stats.in_progress_count" :footer="'较上周 ↓ 2'" :icon="DocumentChecked" bg="linear-gradient(135deg, #A78BFA 0%, #7C3AED 100%)" />
      <StatCard theme="dark" title="延期任务" :value="dashboard.stats.delayed_count" :footer="'较上周 ↑ 1'" :icon="Clock" bg="linear-gradient(135deg, #22D3EE 0%, #0891B2 100%)" />
      <StatCard theme="dark" title="项目成员" :value="dashboard.stats.member_count" :footer="'活跃成员 7'" :icon="UserFilled" bg="linear-gradient(135deg, #818CF8 0%, #4F46E5 100%)" />
      <StatCard theme="dark" title="协作文档" :value="dashboard.stats.document_count" :footer="'较上周 ↑ 3'" :icon="Files" bg="linear-gradient(135deg, #34D399 0%, #059669 100%)" />
      <StatCard theme="dark" title="协作事件" :value="dashboard.stats.event_count" :footer="'较上周 ↑ 18'" :icon="Connection" bg="linear-gradient(135deg, #FB923C 0%, #EA580C 100%)" />
      <StatCard theme="dark" title="待处理邀请" :value="dashboard.stats.pending_invitation_count" :footer="'成员加入待确认'" :icon="Bell" bg="linear-gradient(135deg, #FBBF24 0%, #D97706 100%)" />
      <StatCard theme="dark" title="未读提醒" :value="dashboard.stats.unread_count" :footer="'点击右上角快速查看'" :icon="Message" bg="linear-gradient(135deg, #FB7185 0%, #E11D48 100%)" />
    </section>

    <section class="dashboard-grid">
      <div class="teamflow-card panel">
        <div class="panel-header">
          <div class="section-title">项目心电图（协作活跃度趋势）</div>
          <el-select model-value="近 30 天" style="width: 120px">
            <el-option label="近 30 天" value="近 30 天" />
          </el-select>
        </div>
        <LineChart :series="dashboard.activity_series" />
      </div>

      <div class="teamflow-card panel">
        <div class="panel-header">
          <div class="section-title">最新协作事件</div>
          <router-link class="action-link" :to="`/projects/${projectId}/graph`">查看全部</router-link>
        </div>
        <div class="timeline-list">
          <div v-for="item in dashboard.recent_events" :key="item.id" class="timeline-item">
            <img :src="item.actor?.avatar" alt="avatar" />
            <div>
              <div class="timeline-title">{{ item.title }}</div>
              <div class="tiny-muted">{{ item.content }}</div>
            </div>
            <span class="tiny-muted">{{ item.created_at?.slice(11, 16) }}</span>
          </div>
        </div>
      </div>

      <div class="teamflow-card panel">
        <div class="panel-header">
          <div class="section-title">风险预警</div>
          <router-link class="action-link" :to="`/projects/${projectId}/risk`">查看全部</router-link>
        </div>
        <div class="risk-list">
          <div v-for="risk in dashboard.risk_alerts" :key="risk.id" class="risk-item">
            <div>
              <div class="timeline-title">{{ risk.title }}</div>
              <div class="tiny-muted">{{ risk.reason }}</div>
            </div>
            <span :class="['status-tag', risk.level === '高' ? 'red' : risk.level === '中' ? 'orange' : 'green']">{{ risk.level }}风险</span>
          </div>
        </div>
      </div>

      <div class="teamflow-card panel">
        <div class="panel-header">
          <div class="section-title">成员贡献排名（近 30 天）</div>
          <router-link class="action-link" :to="`/projects/${projectId}/contribution`">查看全部</router-link>
        </div>
        <div class="ranking-list">
          <div v-for="(item, index) in dashboard.contribution_rank" :key="item.id" class="ranking-row">
            <span class="rank-index">{{ Number(index) + 1 }}</span>
            <img :src="item.user.avatar" alt="avatar" />
            <span class="ranking-name">{{ item.user.name }}</span>
            <el-progress :percentage="Math.min(item.total_score, 100)" :show-text="false" />
            <span>{{ item.total_score }}</span>
          </div>
        </div>
      </div>

      <div class="teamflow-card panel">
        <div class="panel-header">
          <div class="section-title">项目健康度雷达图</div>
        </div>
        <RadarChart :items="dashboard.health_radar" />
      </div>

      <div class="teamflow-card panel">
        <div class="panel-header">
          <div class="section-title">过程审计概览</div>
          <router-link class="action-link" :to="`/projects/${projectId}/audit`">查看全部</router-link>
        </div>
        <div class="audit-list">
          <div v-for="item in dashboard.process_audit" :key="item.name" class="audit-row">
            <span>{{ item.name }}</span>
            <span class="tiny-muted">本期 {{ item.count }} 条</span>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { Bell, Clock, Connection, DocumentChecked, Files, Message, PieChart, UserFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { projectApi } from '@/api'
import LineChart from '@/components/common/LineChart.vue'
import RadarChart from '@/components/common/RadarChart.vue'
import StatCard from '@/components/common/StatCard.vue'
import { useProjectStore } from '@/stores/project'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()
const projectId = computed(() => route.params.id as string)
const dashboard = computed(() => projectStore.dashboard)

const load = () => projectStore.fetchDashboard(projectId.value)
const scanRisk = async () => {
  await projectApi.scanRisk(projectId.value)
  ElMessage.success('风险扫描完成')
  await load()
}
const refreshContribution = async () => {
  await projectApi.recalculateContribution(projectId.value)
  ElMessage.success('贡献分已刷新')
  await load()
}
const goCareer = async () => {
  await router.push(`/projects/${projectId.value}/career`)
}

onMounted(load)
</script>

<style scoped>
.dashboard-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.header-row,
.panel-header,
.timeline-item,
.risk-item,
.ranking-row,
.audit-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.dashboard-grid {
  display: grid;
  gap: 18px;
  grid-template-columns: minmax(0, 1.45fr) minmax(0, 1fr) minmax(0, 1fr);
}

.panel {
  padding: 18px 20px;
}

.dashboard-grid > :nth-child(1) {
  grid-column: span 1;
}

.timeline-list,
.risk-list,
.ranking-list,
.audit-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-top: 18px;
}

.timeline-item {
  gap: 12px;
  justify-content: flex-start;
}

.timeline-item img,
.ranking-row img {
  width: 36px;
  height: 36px;
  border-radius: 50%;
}

.timeline-title {
  font-weight: 700;
}

.risk-item {
  gap: 12px;
  padding: 16px;
  border: 1px solid #eef2ff;
  border-radius: 14px;
}

.ranking-row {
  display: grid;
  align-items: center;
  gap: 12px;
  grid-template-columns: 24px 38px 110px 1fr 48px;
}

.rank-index {
  font-weight: 700;
  color: #f59e0b;
}

.audit-row {
  padding: 14px 16px;
  border: 1px solid #eef2ff;
  border-radius: 14px;
}

@media (max-width: 1200px) {
  .dashboard-grid {
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  }
}

@media (max-width: 768px) {
  .header-row {
    align-items: flex-start;
    gap: 12px;
    flex-direction: column;
  }

  .header-actions {
    width: 100%;
    flex-wrap: wrap;
  }

  .dashboard-grid {
    grid-template-columns: 1fr;
  }

  .ranking-row {
    grid-template-columns: 24px 38px 1fr;
  }

  .ranking-row :deep(.el-progress) {
    grid-column: 1 / -1;
  }
}
</style>
