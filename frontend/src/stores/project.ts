import { defineStore } from 'pinia'
import { ref } from 'vue'
import { projectApi } from '@/api'

export const useProjectStore = defineStore('project', () => {
  const projects = ref<any[]>([])
  const current = ref<any | null>(null)
  const dashboard = ref<any | null>(null)
  const members = ref<any[]>([])

  async function fetchProjects() {
    const res: any = await projectApi.list()
    projects.value = res
    return res
  }

  async function fetchDashboard(id: number) {
    const res: any = await projectApi.dashboard(id)
    dashboard.value = res
    current.value = res.project
    return res
  }

  async function fetchMembers(id: number) {
    const res: any = await projectApi.members(id)
    members.value = res
    return res
  }

  function setCurrentProject(project: any) {
    current.value = project
  }

  return { projects, current, dashboard, members, fetchProjects, fetchDashboard, fetchMembers, setCurrentProject }
})
