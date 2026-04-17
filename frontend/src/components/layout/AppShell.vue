<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'

const route = useRoute()

const navigationItems = computed(() => [
  { label: '概览', to: '/' },
  { label: '日报', to: '/reports' },
  { label: '数据源', to: '/sources' },
])

function isRouteActive(targetPath: string) {
  if (targetPath === '/') {
    return route.path === '/'
  }
  return route.path === targetPath || route.path.startsWith(`${targetPath}/`)
}
</script>

<template>
  <div class="shell">
    <aside class="shell-sidebar">
      <div class="brand-block">
        <p class="brand-kicker">Forum Intelligence</p>
        <h1 class="brand-title">情报日报中枢</h1>
        <p class="brand-description">
          每日采集论坛与资讯源，英文内容自动翻译，分门别类沉淀成可读日报，并支持飞书推送。
        </p>
      </div>

      <nav class="shell-nav" aria-label="主导航">
        <RouterLink
          v-for="item in navigationItems"
          :key="item.to"
          :to="item.to"
          class="nav-link"
          :class="{ 'nav-link-active': isRouteActive(item.to) }"
        >
          {{ item.label }}
        </RouterLink>
      </nav>
    </aside>

    <main class="shell-main">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.shell {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  min-height: 100vh;
}

.shell-sidebar {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 2rem;
  padding: 2rem;
  border-right: 1px solid rgba(255, 255, 255, 0.12);
  background:
    radial-gradient(circle at top, rgba(255, 180, 90, 0.32), transparent 40%),
    linear-gradient(180deg, rgba(10, 26, 45, 0.96), rgba(7, 18, 31, 0.96));
}

.brand-block {
  display: grid;
  gap: 1rem;
}

.brand-kicker {
  margin: 0;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--color-accent);
  font-size: 0.75rem;
}

.brand-title {
  margin: 0;
  font-size: clamp(2rem, 4vw, 3rem);
  line-height: 1;
}

.brand-description {
  margin: 0;
  color: var(--color-muted);
  line-height: 1.7;
}

.shell-nav {
  display: grid;
  gap: 0.75rem;
}

.nav-link {
  padding: 0.95rem 1rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.06);
  color: var(--color-text);
  text-decoration: none;
  transition: transform 180ms ease, background 180ms ease;
}

.nav-link:hover {
  transform: translateX(4px);
  background: rgba(255, 255, 255, 0.12);
}

.nav-link-active {
  background: linear-gradient(135deg, rgba(255, 159, 67, 0.9), rgba(65, 218, 255, 0.82));
  color: #06223d;
  font-weight: 700;
}

.shell-main {
  padding: 2rem;
}

@media (max-width: 960px) {
  .shell {
    grid-template-columns: 1fr;
  }

  .shell-sidebar {
    border-right: none;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }
}
</style>

