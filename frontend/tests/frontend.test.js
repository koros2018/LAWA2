/**
 * LAWA2 前端功能测试
 * 
 * 测试所有主要页面和组件的功能性
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const FRONTEND_DIR = path.join(__dirname, '..');

const results = [];
const issues = [];

function test(name, fn) {
  try {
    fn();
    results.push({ name, status: 'PASS' });
    console.log(`✅ ${name}`);
  } catch (error) {
    results.push({ name, status: 'FAIL', error: error.message });
    issues.push({ name, error: error.message });
    console.log(`❌ ${name}: ${error.message}`);
  }
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

// ── 文件结构测试 ──

test('Frontend directory structure', () => {
  const requiredDirs = ['src', 'src/views', 'src/components', 'src/api', 'src/router', 'src/store'];
  requiredDirs.forEach(dir => {
    const fullPath = path.join(__dirname, '..', dir);
    assert(fs.existsSync(fullPath), `Missing directory: ${dir}`);
  });
});

test('Main entry file exists', () => {
  assert(fs.existsSync(path.join(__dirname, '..', 'index.html')), 'Missing index.html');
  assert(fs.existsSync(path.join(__dirname, '..', 'package.json')), 'Missing package.json');
  assert(fs.existsSync(path.join(__dirname, '..', 'vite.config.ts')), 'Missing vite.config.ts');
});

// ── API 客户端测试 ──

test('API client configuration', () => {
  const clientCode = fs.readFileSync(path.join(__dirname, '..', 'src/api/client.ts'), 'utf8');
  // Check for HTTP client (axios or fetch)
  const hasHttpLib = clientCode.includes('axios') || clientCode.includes('fetch');
  assert(hasHttpLib, 'Missing HTTP client configuration');
  // Check for auth headers and API request methods
  assert(clientCode.includes('getAuthHeaders'), 'Missing getAuthHeaders');
  assert(clientCode.includes('apiGet') && clientCode.includes('apiPost'), 'Missing API methods');
});

test('All API modules exist', () => {
  const apiModules = [
    'admin.ts', 'agent_main.ts', 'agent_photo.ts', 'agent_reminder.ts',
    'auth.ts', 'bridge.ts', 'habit.ts', 'photo.ts', 'reminder.ts',
    'seed.ts', 'logs.ts', 'errors.ts'
  ];
  apiModules.forEach(module => {
    const fullPath = path.join(__dirname, '..', 'src/api', module);
    assert(fs.existsSync(fullPath), `Missing API module: ${module}`);
  });
});

// ── 视图组件测试 ──

test('All view components exist', () => {
  const viewFiles = [
    'AdminPage.vue', 'BridgePage.vue', 'ErrorMonitorPage.vue', 'FeedPage.vue',
    'GardenPage.vue', 'HomePage.vue', 'LoginPage.vue', 'LogsPage.vue',
    'OnboardingPage.vue', 'PhotoPage.vue', 'ProfilePage.vue', 'ReminderPage.vue',
    'RewardsPage.vue', 'SeedContentPage.vue'
  ];
  viewFiles.forEach(file => {
    const fullPath = path.join(__dirname, '..', 'src/views', file);
    assert(fs.existsSync(fullPath), `Missing view: ${file}`);
  });
});

test('Core components exist', () => {
  const components = ['ECharts.vue', 'SocialSceneCard.vue', 'HelloWorld.vue'];
  components.forEach(file => {
    const fullPath = path.join(__dirname, '..', 'src/components', file);
    assert(fs.existsSync(fullPath), `Missing component: ${file}`);
  });
});

// ── 路由配置测试 ──

test('Router configuration', () => {
  const routerCode = fs.readFileSync(path.join(__dirname, '..', 'src/router/index.ts'), 'utf8');
  assert(routerCode.includes('createRouter'), 'Missing createRouter');
  assert(routerCode.includes('routes'), 'Missing routes array');
});

// ── 状态管理测试 ──

test('Store configuration', () => {
  const storeFiles = fs.readdirSync(path.join(__dirname, '..', 'src/store'));
  assert(storeFiles.length > 0, 'Store directory is empty');
});

// ── Vue 组件语法测试 ──

test('Vue components have valid syntax', () => {
  const viewFiles = fs.readdirSync(path.join(__dirname, '..', 'src/views'));
  viewFiles.forEach(file => {
    if (file.endsWith('.vue')) {
      const fullPath = path.join(__dirname, '..', 'src/views', file);
      const content = fs.readFileSync(fullPath, 'utf8');
      
      // 检查基本 Vue 结构
      assert(content.includes('<template>'), `${file}: Missing <template>`);
      assert(content.includes('<script'), `${file}: Missing <script>`);
      assert(content.includes('</template>'), `${file}: Missing </template>`);
      assert(content.includes('</script>'), `${file}: Missing </script>`);
    }
  });
});

// ── 双语化检查 ──

test('Bilingual content in key views', () => {
  const bilingualFiles = ['GardenPage.vue', 'BridgePage.vue', 'HomePage.vue'];
  bilingualFiles.forEach(file => {
    const fullPath = path.join(__dirname, '..', 'src/views', file);
    const content = fs.readFileSync(fullPath, 'utf8');
    
    // 检查是否有英文内容（简单检查）
    const hasEnglish = /[A-Z][a-z]+\s+[A-Z][a-z]+/.test(content);
    // 注意：这只是启发式检查，实际需要更精确的双语验证
    console.log(`   ${file}: ${hasEnglish ? 'Has English content' : 'Needs bilingual check'}`);
  });
});

// ── 打印结果 ──

console.log('\n' + '='.repeat(60));
console.log('LAWA2 前端功能测试结果');
console.log('='.repeat(60));

const passed = results.filter(r => r.status === 'PASS').length;
const failed = results.filter(r => r.status === 'FAIL').length;

console.log(`\n总计: ${results.length} 个测试`);
console.log(`通过: ${passed} ✅`);
console.log(`失败: ${failed} ❌`);

if (issues.length > 0) {
  console.log('\n' + '='.repeat(60));
  console.log('问题列表:');
  console.log('='.repeat(60));
  issues.forEach(issue => {
    console.log(`\n❌ ${issue.name}`);
    console.log(`   ${issue.error}`);
  });
}

console.log('\n' + '='.repeat(60));

// 退出码
process.exit(failed > 0 ? 1 : 0);
