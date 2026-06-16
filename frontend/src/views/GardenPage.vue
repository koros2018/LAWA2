<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { getGarden, getGardenReport, getHealthInsights } from '@/api/habit'
import type { GardenData, GardenReportData, HealthInsightsData } from '@/api/habit'

const garden = ref<GardenData | null>(null)
const report = ref<GardenReportData | null>(null)
const health = ref<HealthInsightsData | null>(null)
const loading = ref(true)

const stageOrder = ['seed', 'sprout', 'seedling', 'bloom', 'fruit']
const stageMeta: Record<string, { label: string; icon: string; color: string }> = {
  seed:     { label: '种子', icon: '🌰', color: '#8B6C42' },
  sprout:   { label: '发芽', icon: '🌱', color: '#7BC67E' },
  seedling: { label: '幼苗', icon: '🌿', color: '#4CAF50' },
  bloom:    { label: '开花', icon: '🌸', color: '#E8796E' },
  fruit:    { label: '结果', icon: '🍎', color: '#F44336' },
}

const g = computed(() => garden.value?.garden)
const totalWords = computed(() => g.value?.total_vocab ?? 0)
const bloomWords = computed(() => {
  const byStage = g.value?.by_stage ?? {}
  return (byStage['bloom'] ?? 0) + (byStage['fruit'] ?? 0)
})

// ── 词簇粒子系统 ──
interface VocabParticle {
  id: number
  word: string
  x: number
  y: number
  vx: number
  vy: number
  size: number
  opacity: number
  hue: number
  clusterGroup: number
}

const particles = ref<VocabParticle[]>([])
let animFrame = 0

const clusterWords = [
  { word: '破防了', clusterGroup: 0 }, { word: '绝绝子', clusterGroup: 0 }, { word: 'YYDS', clusterGroup: 0 },
  { word: '鸳鸯锅', clusterGroup: 1 }, { word: '打包', clusterGroup: 1 }, { word: '美团', clusterGroup: 1 },
  { word: '+1', clusterGroup: 2 }, { word: 'wdym', clusterGroup: 2 }, { word: 'omg fr', clusterGroup: 2 },
  { word: '格局小了', clusterGroup: 3 }, { word: '显眼包', clusterGroup: 3 }, { word: '尊嘟假嘟', clusterGroup: 3 },
]

function initParticles() {
  const w = window.innerWidth
  const h = window.innerHeight
  const clusterCenters = [[180, 280], [w - 280, 180], [220, h - 200], [w - 300, h - 220]]
  const clusterColors = [260, 180, 30, 340]
  particles.value = clusterWords.map((cw, i) => {
    const ci = cw.clusterGroup
    const cc = clusterCenters[ci]
    return {
      id: i,
      word: cw.word,
      x: cc[0] + (Math.random() - 0.5) * 120,
      y: cc[1] + (Math.random() - 0.5) * 120,
      vx: (Math.random() - 0.5) * 0.25,
      vy: (Math.random() - 0.5) * 0.25,
      size: 10 + Math.random() * 6,
      opacity: 0.5 + Math.random() * 0.4,
      hue: clusterColors[ci] + (Math.random() - 0.5) * 30,
      clusterGroup: ci,
    }
  })
}

function animateParticles() {
  const w = window.innerWidth
  const h = window.innerHeight
  const clusterCenters = [[180, 280], [w - 280, 180], [220, h - 200], [w - 300, h - 220]]
  for (const p of particles.value) {
    p.x += p.vx
    p.y += p.vy
    if (p.x < 30 || p.x > w - 30) p.vx *= -1
    if (p.y < 30 || p.y > h - 30) p.vy *= -1
    const cc = clusterCenters[p.clusterGroup]
    p.vx += (cc[0] - p.x) * 0.00005
    p.vy += (cc[1] - p.y) * 0.00005
  }
  animFrame = requestAnimationFrame(animateParticles)
}

const healthLabel = computed(() => {
  if (!health.value) return '—'
  const s = health.value.health_score
  if (s >= 85) return '🌿 欣欣向荣'
  if (s >= 60) return '🌱 稳步成长'
  if (s >= 30) return '💧 需要浇灌'
  return '🌰 刚刚播种'
})

const trendIcon = computed(() => {
  if (!health.value) return '➖'
  const t = health.value.trend
  if (t === 'up') return '📈'
  if (t === 'down') return '📉'
  return '➡️'
})

onMounted(async () => {
  try {
    const [g, r, h] = await Promise.all([
      getGarden(),
      getGardenReport(),
      getHealthInsights(),
    ])
    garden.value = g
    report.value = r
    health.value = h
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
  initParticles()
  animateParticles()
})

onUnmounted(() => {
  if (animFrame) cancelAnimationFrame(animFrame)
})
</script>

<template>
  <div class="page garden-page">
    <div class="particle-overlay">
      <div v-for="p in particles" :key="p.id" class="vocab-particle"
        :style="{
          left: p.x + 'px', top: p.y + 'px', fontSize: p.size + 'px',
          opacity: p.opacity,
          color: `hsl(${p.hue}, 70%, 65%)`,
          textShadow: `0 0 ${p.size}px hsla(${p.hue}, 70%, 60%, 0.3)`,
        }">
        {{ p.word }}
      </div>
    </div>

    <div class="garden-scroll">

      <section class="hero-section garden-hero">
        <div class="bg-glow bg-glow-2"></div>
        <h1 class="hero-title garden-title">🌱 语言花园</h1>
        <p class="hero-subtitle" v-if="!loading">
          你种下了 <strong>{{ totalWords }}</strong> 个词，<strong>{{ bloomWords }}</strong> 个已开花结果
        </p>
      </section>

      <div v-if="report && !loading" class="card report-card">
        <div class="report-header">
          <span class="report-icon">📋</span>
          <h3 class="report-title">花园周报</h3>
          <span class="report-badge" :class="{ watered: report.watered_today }">
            {{ report.can_water ? '💧 可浇水' : '☀️ 已浇灌' }}
          </span>
        </div>
        <div class="report-body" v-html="report.report.replace(/\n\n/g, '<br><br>')"></div>
        <div class="report-metrics">
          <div class="rm-item">
            <span class="rm-value">{{ report.week_actions }}</span>
            <span class="rm-label">微行为</span>
          </div>
          <div class="rm-item">
            <span class="rm-value">+{{ report.week_vocab }}</span>
            <span class="rm-label">新词</span>
          </div>
          <div class="rm-item">
            <span class="rm-value">🔥 {{ report.streak }}</span>
            <span class="rm-label">连续天</span>
          </div>
          <div class="rm-item">
            <span class="rm-value">{{ report.level }}</span>
            <span class="rm-label">等级</span>
          </div>
        </div>
      </div>

      <div v-if="health && !loading" class="card health-card">
        <div class="health-header">
          <span class="health-title">🫀 习惯健康度</span>
          <span class="health-score">{{ health.health_score }}/100</span>
        </div>
        <div class="health-bar-wrapper">
          <div class="health-bar" :style="{
            width: health.health_score + '%',
            background: health.health_score >= 60
              ? 'linear-gradient(90deg, #7BC67E, #4CAF50)'
              : 'linear-gradient(90deg, #E8796E, #FF9800)',
          }"></div>
        </div>
        <div class="health-label">{{ healthLabel }} {{ trendIcon }}</div>

        <div class="health-dims">
          <div class="hd-row" v-for="d in [
            { key: 'consistency' as const, label: '持续度', color: '#7BC67E' },
            { key: 'depth' as const, label: '深入度', color: '#4FC3F7' },
            { key: 'breadth' as const, label: '广度', color: '#BA68C8' },
            { key: 'recovery' as const, label: '恢复力', color: '#FFB74D' },
          ]" :key="d.key">
            <span class="hd-label">{{ d.label }}</span>
            <div class="hd-bar-bg">
              <div class="hd-bar" :style="{
                width: Math.min(100, health.dimensions[d.key]) + '%',
                background: d.color,
              }"></div>
            </div>
            <span class="hd-value">{{ health.dimensions[d.key] }}</span>
          </div>
        </div>
        <div class="health-recommend">{{ health.recommendation }}</div>
      </div>

      <div v-if="g" class="garden-overview card">
        <div class="overview-row">
          <div v-for="item in [
            { value: g.total_vocab, label: '词汇量' },
            { value: g.habit_level, label: '等级' },
            { value: g.total_milestones, label: '里程碑' },
            { value: g.total_xp, label: '总 XP' },
          ]" :key="item.label" class="overview-item">
            <span class="ov-value">{{ item.value }}</span>
            <span class="ov-label">{{ item.label }}</span>
          </div>
        </div>
      </div>

      <div v-if="loading" class="garden-stages">
        <div v-for="i in 3" :key="i" class="card skeleton" style="height: 60px;"></div>
      </div>
      <div v-else class="garden-stages">
        <div v-for="stage in stageOrder" :key="stage" class="stage-section">
          <div class="stage-header">
            <span class="stage-icon">{{ stageMeta[stage]?.icon }}</span>
            <h3 class="stage-name">{{ stageMeta[stage]?.label }}</h3>
            <span class="stage-count">{{ g?.by_stage?.[stage] ?? 0 }}</span>
          </div>
          <div class="stage-progress">
            <div class="stage-bar" :style="{
              width: Math.min(100, ((g?.by_stage?.[stage] ?? 0) / Math.max(totalWords, 1)) * 100) + '%',
              background: stageMeta[stage]?.color,
            }"></div>
          </div>
        </div>
      </div>

      <section v-if="garden?.new_milestones?.length" class="new-milestones">
        <h2 class="section-title">🎉 新里程碑</h2>
        <div class="divider"></div>
        <div v-for="m in garden.new_milestones" :key="m.code" class="card milestone-card">
          <span class="ms-icon">🏆</span>
          <div><h4 class="ms-name">{{ m.name }}</h4><p class="ms-desc">{{ m.description }}</p></div>
        </div>
      </section>

      <div v-if="!totalWords && !loading" class="empty-state">
        <p class="empty-icon">🌱</p>
        <p>开始阅读信息流，词汇会自动生长</p>
        <router-link to="/feed" class="btn btn-primary">去信息流</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.garden-page { position: relative; min-height: 100dvh; }
.particle-overlay { position: fixed; inset: 0; pointer-events: none; z-index: 0; overflow: hidden; }
.vocab-particle { position: absolute; white-space: nowrap; font-weight: 600; font-family: 'SF Mono','Fira Code',monospace; letter-spacing: 0.02em; user-select: none; }
.garden-scroll { position: relative; z-index: 1; padding-bottom: calc(64px + var(--space-2xl)); }
.garden-hero { margin-bottom: var(--space-lg); }
.garden-title { font-size: var(--fs-title); }

.report-card { margin-bottom: var(--space-lg); border-color: rgba(74,222,128,0.25); }
.report-header { display: flex; align-items: center; gap: var(--space-sm); margin-bottom: var(--space-md); }
.report-icon { font-size: 1.25rem; flex-shrink: 0; }
.report-title { font-size: var(--fs-body); font-weight: var(--fw-semibold); flex: 1; }
.report-badge { font-size: var(--fs-caption); padding: 0.125rem 0.5rem; border-radius: 999px; background: rgba(74,222,128,0.15); color: #4ADE80; flex-shrink: 0; }
.report-badge.watered { background: rgba(250,204,21,0.15); color: #FACC15; }
.report-body { margin-bottom: var(--space-md); font-size: var(--fs-small); color: var(--text-secondary); line-height: 1.6; }
.report-metrics { display: grid; grid-template-columns: repeat(4,1fr); gap: var(--space-sm); text-align: center; padding: var(--space-sm) 0; border-top: 1px solid var(--border-color,rgba(255,255,255,0.06)); }
.rm-value { display: block; font-size: var(--fs-subtitle); font-weight: var(--fw-bold); color: var(--text-primary); line-height: 1.2; }
.rm-label { display: block; font-size: var(--fs-caption); color: var(--text-tertiary); margin-top: 2px; }

.health-card { margin-bottom: var(--space-lg); border-color: rgba(147,197,253,0.25); }
.health-header { display: flex; align-items: center; gap: var(--space-sm); margin-bottom: var(--space-sm); }
.health-title { font-size: var(--fs-body); font-weight: var(--fw-semibold); flex: 1; }
.health-score { font-size: var(--fs-subtitle); font-weight: var(--fw-bold); color: var(--accent); font-variant-numeric: tabular-nums; }
.health-bar-wrapper { height: 6px; background: var(--bg-primary); border-radius: 3px; overflow: hidden; margin-bottom: var(--space-sm); }
.health-bar { height: 100%; border-radius: 3px; transition: width var(--duration-slow) var(--ease-out); }
.health-label { font-size: var(--fs-small); color: var(--text-secondary); margin-bottom: var(--space-md); }

.health-dims { display: flex; flex-direction: column; gap: var(--space-sm); margin-bottom: var(--space-md); }
.hd-row { display: flex; align-items: center; gap: var(--space-sm); }
.hd-label { font-size: var(--fs-caption); color: var(--text-tertiary); width: 3.5em; flex-shrink: 0; }
.hd-bar-bg { flex: 1; height: 4px; background: var(--bg-primary); border-radius: 2px; overflow: hidden; }
.hd-bar { height: 100%; border-radius: 2px; transition: width var(--duration-slow) var(--ease-out); }
.hd-value { font-size: var(--fs-caption); color: var(--text-secondary); width: 2em; text-align: right; font-variant-numeric: tabular-nums; }
.health-recommend { font-size: var(--fs-caption); color: var(--text-tertiary); padding: var(--space-sm); background: var(--bg-primary); border-radius: var(--radius-sm); line-height: 1.5; }

.garden-overview { margin-bottom: var(--space-2xl); }
.overview-row { display: grid; grid-template-columns: repeat(4,1fr); gap: var(--space-md); text-align: center; }
.overview-item { display: flex; flex-direction: column; align-items: center; }
.ov-value { display: block; font-size: var(--fs-title); font-weight: var(--fw-bold); color: var(--text-primary); line-height: 1.1; }
.ov-label { display: block; font-size: var(--fs-small); color: var(--text-tertiary); margin-top: 2px; text-transform: uppercase; letter-spacing: 0.05em; }

.garden-stages { display: flex; flex-direction: column; gap: var(--space-lg); margin-bottom: var(--space-2xl); }
.stage-header { display: flex; align-items: center; gap: var(--space-sm); margin-bottom: var(--space-sm); }
.stage-icon { font-size: clamp(1rem,4vw,1.25rem); flex-shrink: 0; }
.stage-name { font-size: var(--fs-body); font-weight: var(--fw-semibold); color: var(--text-primary); flex: 1; }
.stage-count { font-size: var(--fs-small); color: var(--text-tertiary); background: var(--bg-card); padding: 0.125rem 0.5rem; border-radius: 999px; flex-shrink: 0; }
.stage-progress { height: 4px; background: var(--bg-primary); border-radius: 2px; overflow: hidden; }
.stage-bar { height: 100%; border-radius: 2px; transition: width var(--duration-slow) var(--ease-out); }

.new-milestones { margin-bottom: var(--space-2xl); }
.section-title { font-size: var(--fs-subtitle); font-weight: var(--fw-semibold); color: var(--text-primary); margin-bottom: var(--space-lg); }
.milestone-card { display: flex; align-items: flex-start; gap: var(--space-md); border-color: rgba(52,211,153,0.3); }
.ms-icon { font-size: 1.5rem; flex-shrink: 0; }
.ms-name { font-size: var(--fs-body); font-weight: var(--fw-medium); color: var(--text-primary); }
.ms-desc { font-size: var(--fs-caption); color: var(--text-secondary); margin-top: 2px; }

.empty-state { text-align: center; padding: var(--space-3xl) 0; display: flex; flex-direction: column; align-items: center; gap: var(--space-lg); color: var(--text-tertiary); }
.empty-icon { font-size: 3rem; }
</style>
