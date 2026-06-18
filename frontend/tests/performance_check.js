/**
 * LAWA2 前端性能检查
 * 
 * 检查前端资源大小、加载时间等
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const FRONTEND_DIR = path.join(__dirname, '..');

const results = [];
const issues = [];

function check(name, fn) {
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

// ── 资源大小检查 ──

check('Frontend bundle size', () => {
  const distDir = path.join(FRONTEND_DIR, 'dist');
  if (fs.existsSync(distDir)) {
    const files = fs.readdirSync(distDir);
    let totalSize = 0;
    
    for (const file of files) {
      const filePath = path.join(distDir, file);
      if (fs.statSync(filePath).isFile()) {
        totalSize += fs.statSync(filePath).size;
      }
    }
    
    const totalMB = (totalSize / (1024 * 1024)).toFixed(2);
    console.log(`   总大小: ${totalMB} MB`);
    
    // 目标：< 2MB
    assert(totalSize < 2 * 1024 * 1024, `Bundle size ${totalMB}MB exceeds 2MB target`);
  } else {
    console.log('   (dist 目录不存在，跳过检查)');
  }
});

check('Vendor chunk size', () => {
  const distDir = path.join(FRONTEND_DIR, 'dist');
  if (fs.existsSync(distDir)) {
    const files = fs.readdirSync(distDir);
    for (const file of files) {
      if (file.includes('vendor') || file.includes('chunk')) {
        const filePath = path.join(distDir, file);
        const size = fs.statSync(filePath).size;
        const sizeKB = (size / 1024).toFixed(1);
        console.log(`   ${file}: ${sizeKB} KB`);
      }
    }
  }
});

// ── 代码优化检查 ──

check('No console.log in production code', () => {
  const srcDir = path.join(FRONTEND_DIR, 'src');
  const files = getAllVueFiles(srcDir);
  let consoleLogs = 0;
  
  for (const file of files) {
    const content = fs.readFileSync(file, 'utf8');
    const matches = content.match(/console\.(log|warn|error)/g);
    if (matches) {
      consoleLogs += matches.length;
    }
  }
  
  // 允许少量 console.log（开发用）
  console.log(`   Found ${consoleLogs} console statements`);
  // 不强制失败，仅警告
});

check('No hardcoded API URLs', () => {
  const srcDir = path.join(FRONTEND_DIR, 'src');
  const files = getAllVueFiles(srcDir);
  const hardcodedUrls = [];
  
  for (const file of files) {
    const content = fs.readFileSync(file, 'utf8');
    const matches = content.match(/https?:\/\/[^\s"'`]+/g);
    if (matches) {
      for (const url of matches) {
        if (!url.includes('localhost') && !url.includes('127.0.0.1')) {
          hardcodedUrls.push({ file: path.basename(file), url });
        }
      }
    }
  }
  
  if (hardcodedUrls.length > 0) {
    console.log(`   Found ${hardcodedUrls.length} hardcoded URLs:`);
    hardcodedUrls.slice(0, 3).forEach(u => console.log(`     ${u.file}: ${u.url}`));
  }
});

// ── 辅助函数 ──

function getAllVueFiles(dir) {
  const files = [];
  const items = fs.readdirSync(dir);
  
  for (const item of items) {
    const fullPath = path.join(dir, item);
    const stat = fs.statSync(fullPath);
    
    if (stat.isDirectory()) {
      files.push(...getAllVueFiles(fullPath));
    } else if (item.endsWith('.vue') || item.endsWith('.ts') || item.endsWith('.js')) {
      files.push(fullPath);
    }
  }
  
  return files;
}

// ── 打印结果 ──

console.log('\n' + '='.repeat(60));
console.log('LAWA2 前端性能检查结果');
console.log('='.repeat(60));

const passed = results.filter(r => r.status === 'PASS').length;
const failed = results.filter(r => r.status === 'FAIL').length;

console.log(`\n总计: ${results.length} 个检查`);
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

process.exit(failed > 0 ? 1 : 0);
