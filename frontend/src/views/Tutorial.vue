<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const currentStep = ref(0)

const steps = [
  {
    title: '选择数据集',
    description: '在首页选择一个要标注的数据集，点击"开始标注"按钮进入标注界面。',
    tips: [
      '可以查看每个数据集的标注进度',
      '进度条显示已完成的百分比'
    ]
  },
  {
    title: '选择标注类别',
    description: '在左侧面板中选择要标注的目标类别。如果数据集只有一个类别，会自动选中。',
    tips: [
      '每个类别都有对应的颜色',
      '可以通过快捷键快速切换类别',
      '当前选中的类别会高亮显示'
    ]
  },
  {
    title: '绘制标注框',
    description: '在图片上按住鼠标左键拖动来绘制边界框。松开鼠标完成绘制。',
    tips: [
      '框要尽量贴合目标边缘',
      '可以选中已有的框进行调整',
      '双击框可以删除它',
      '按 Delete 键删除选中的框'
    ]
  },
  {
    title: '调整和保存',
    description: '绘制完成后，可以调整框的大小和位置。确认无误后点击"保存"按钮。',
    tips: [
      '拖动框的角和边可以调整大小',
      '支持撤销 (Ctrl+Z) 和重做 (Ctrl+Shift+Z)',
      '如果图片中没有目标，按 N 键跳过'
    ]
  },
  {
    title: '快捷键操作',
    description: '熟练使用快捷键可以大大提高标注效率。',
    tips: [
      'Ctrl+S: 保存当前标注',
      'N: 跳过当前图片（无目标）',
      'Ctrl+Z: 撤销',
      'Ctrl+Shift+Z: 重做',
      '滚轮: 缩放画布',
      '空格+拖动: 平移画布',
      '数字键/字母键: 切换类别',
      '?: 显示帮助面板'
    ]
  }
]

function nextStep() {
  if (currentStep.value < steps.length - 1) {
    currentStep.value++
  }
}

function prevStep() {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

function goToAnnotation() {
  router.push('/')
}
</script>

<template>
  <div class="tutorial-container">
    <header class="header">
      <div class="logo">
        <h1>Torch-Markup 使用教程</h1>
      </div>
      <el-button @click="router.push('/')" type="primary" link>
        返回首页
      </el-button>
    </header>

    <main class="main">
      <div class="steps-nav">
        <div
          v-for="(step, index) in steps"
          :key="index"
          class="step-dot"
          :class="{ active: index === currentStep, completed: index < currentStep }"
          @click="currentStep = index"
        >
          <span class="number">{{ index + 1 }}</span>
          <span class="title">{{ step.title }}</span>
        </div>
      </div>

      <div class="step-content">
        <div class="step-header">
          <span class="step-number">步骤 {{ currentStep + 1 }}</span>
          <h2>{{ steps[currentStep].title }}</h2>
        </div>

        <p class="description">{{ steps[currentStep].description }}</p>

        <div class="tips-card">
          <h3>提示</h3>
          <ul>
            <li v-for="(tip, index) in steps[currentStep].tips" :key="index">
              {{ tip }}
            </li>
          </ul>
        </div>

        <div class="demo-area">
          <!-- 步骤1: 数据集选择示意 -->
          <div v-if="currentStep === 0" class="demo-datasets">
            <div class="demo-card">
              <div class="card-header">示例数据集</div>
              <div class="card-body">
                <div class="progress-bar">
                  <div class="fill" style="width: 65%"></div>
                </div>
                <span>65% 完成</span>
              </div>
            </div>
          </div>

          <!-- 步骤2: 类别选择示意 -->
          <div v-if="currentStep === 1" class="demo-categories">
            <div class="category-item active">
              <span class="dot" style="background: #FF0000"></span>
              <span>行人</span>
              <kbd>1</kbd>
            </div>
            <div class="category-item">
              <span class="dot" style="background: #00FF00"></span>
              <span>车辆</span>
              <kbd>2</kbd>
            </div>
            <div class="category-item">
              <span class="dot" style="background: #0000FF"></span>
              <span>自行车</span>
              <kbd>3</kbd>
            </div>
          </div>

          <!-- 步骤3: 绘制框示意 -->
          <div v-if="currentStep === 2" class="demo-drawing">
            <div class="demo-image">
              <div class="bbox"></div>
              <div class="cursor"></div>
            </div>
            <p class="demo-hint">按住拖动绘制框</p>
          </div>

          <!-- 步骤4: 调整框示意 -->
          <div v-if="currentStep === 3" class="demo-adjusting">
            <div class="demo-image">
              <div class="bbox selected">
                <span class="handle tl"></span>
                <span class="handle tr"></span>
                <span class="handle bl"></span>
                <span class="handle br"></span>
              </div>
            </div>
            <p class="demo-hint">拖动角点调整大小</p>
          </div>

          <!-- 步骤5: 快捷键示意 -->
          <div v-if="currentStep === 4" class="demo-shortcuts">
            <div class="shortcut-grid">
              <div class="shortcut-item">
                <kbd>Ctrl</kbd> + <kbd>S</kbd>
                <span>保存</span>
              </div>
              <div class="shortcut-item">
                <kbd>N</kbd>
                <span>跳过</span>
              </div>
              <div class="shortcut-item">
                <kbd>Ctrl</kbd> + <kbd>Z</kbd>
                <span>撤销</span>
              </div>
              <div class="shortcut-item">
                <kbd>滚轮</kbd>
                <span>缩放</span>
              </div>
            </div>
          </div>
        </div>

        <div class="nav-buttons">
          <el-button @click="prevStep" :disabled="currentStep === 0">
            上一步
          </el-button>
          <el-button
            v-if="currentStep < steps.length - 1"
            type="primary"
            @click="nextStep"
          >
            下一步
          </el-button>
          <el-button
            v-else
            type="success"
            @click="goToAnnotation"
          >
            开始标注
          </el-button>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.tutorial-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 40px;
}

.header h1 {
  color: white;
  margin: 0;
  font-size: 24px;
}

.main {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px 40px 60px;
}

.steps-nav {
  display: flex;
  justify-content: space-between;
  margin-bottom: 40px;
  position: relative;
}

.steps-nav::before {
  content: '';
  position: absolute;
  top: 20px;
  left: 40px;
  right: 40px;
  height: 2px;
  background: rgba(255, 255, 255, 0.3);
}

.step-dot {
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  z-index: 1;
}

.step-dot .number {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  margin-bottom: 8px;
  transition: all 0.3s;
}

.step-dot.active .number {
  background: white;
  color: #667eea;
  transform: scale(1.2);
}

.step-dot.completed .number {
  background: #67c23a;
}

.step-dot .title {
  color: rgba(255, 255, 255, 0.7);
  font-size: 12px;
  text-align: center;
}

.step-dot.active .title {
  color: white;
  font-weight: bold;
}

.step-content {
  background: white;
  border-radius: 16px;
  padding: 40px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

.step-header {
  margin-bottom: 20px;
}

.step-number {
  color: #667eea;
  font-size: 14px;
  font-weight: bold;
}

.step-header h2 {
  margin: 8px 0 0;
  color: #333;
}

.description {
  font-size: 16px;
  color: #666;
  line-height: 1.8;
  margin-bottom: 24px;
}

.tips-card {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 32px;
}

.tips-card h3 {
  margin: 0 0 12px;
  color: #333;
  font-size: 14px;
}

.tips-card ul {
  margin: 0;
  padding-left: 20px;
}

.tips-card li {
  color: #666;
  margin-bottom: 8px;
}

.demo-area {
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #1a1a2e;
  border-radius: 8px;
  padding: 32px;
  margin-bottom: 32px;
}

/* 演示样式 */
.demo-datasets .demo-card {
  width: 200px;
  background: white;
  border-radius: 8px;
  overflow: hidden;
}

.demo-datasets .card-header {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  padding: 12px 16px;
}

.demo-datasets .card-body {
  padding: 16px;
}

.demo-datasets .progress-bar {
  height: 8px;
  background: #eee;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 8px;
}

.demo-datasets .progress-bar .fill {
  height: 100%;
  background: #67c23a;
}

.demo-categories {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.demo-categories .category-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #0f3460;
  border-radius: 6px;
  color: white;
}

.demo-categories .category-item.active {
  background: #e94560;
}

.demo-categories .dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.demo-categories kbd {
  margin-left: auto;
  padding: 2px 8px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  font-size: 12px;
}

.demo-drawing,
.demo-adjusting {
  text-align: center;
}

.demo-image {
  width: 300px;
  height: 200px;
  background: #2d2d2d;
  border-radius: 4px;
  position: relative;
  margin: 0 auto 16px;
}

.demo-image .bbox {
  position: absolute;
  width: 100px;
  height: 80px;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  border: 2px solid #e94560;
  background: rgba(233, 69, 96, 0.2);
}

.demo-image .bbox.selected {
  border: 3px solid #e94560;
}

.demo-image .cursor {
  position: absolute;
  width: 20px;
  height: 20px;
  background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white"><path d="M4 4l16 8-8 4-4 8z"/></svg>');
  right: 60px;
  bottom: 40px;
  animation: drawAnim 2s infinite;
}

.handle {
  position: absolute;
  width: 8px;
  height: 8px;
  background: #e94560;
}

.handle.tl { top: -4px; left: -4px; cursor: nw-resize; }
.handle.tr { top: -4px; right: -4px; cursor: ne-resize; }
.handle.bl { bottom: -4px; left: -4px; cursor: sw-resize; }
.handle.br { bottom: -4px; right: -4px; cursor: se-resize; }

.demo-hint {
  color: #a0a0a0;
  font-size: 14px;
}

.demo-shortcuts .shortcut-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.shortcut-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px;
  background: #0f3460;
  border-radius: 8px;
}

.shortcut-item kbd {
  padding: 4px 10px;
  background: #1a4a7a;
  border: 1px solid #2a5a8a;
  border-radius: 4px;
  color: white;
  font-size: 14px;
}

.shortcut-item span {
  color: #a0a0a0;
  font-size: 13px;
}

.nav-buttons {
  display: flex;
  justify-content: center;
  gap: 16px;
}

@keyframes drawAnim {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(-60px, -40px); }
}
</style>
