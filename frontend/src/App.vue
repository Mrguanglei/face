<template>
  <div class="facefusion-app">
    <header class="app-header">
      <h1>FaceFusion</h1>
      <span class="version">v3.6.1</span>
    </header>


    <div class="main-layout" style="display: flex; flex-direction: row;">
      <!-- 左侧：处理器选项 -->
      <div class="left-sidebar">
        <section class="section processor-section">
          <div class="processor-header" @click="showProcessorOptions = !showProcessorOptions">
            <h2>处理器选项</h2>
            <span class="toggle-icon">{{ showProcessorOptions ? '▼' : '▶' }}</span>
          </div>
          <div v-if="showProcessorOptions" class="processor-body">
        <!-- 处理器复选框 -->
        <div class="processor-chips">
          <label class="chip" :class="{ active: selectedProcessors.includes('face_swapper') }">
            <input type="checkbox" v-model="selectedProcessors" value="face_swapper" />
            换脸
          </label>
          <label class="chip" :class="{ active: selectedProcessors.includes('face_enhancer') }">
            <input type="checkbox" v-model="selectedProcessors" value="face_enhancer" />
            面部增强
          </label>
          <label class="chip" :class="{ active: selectedProcessors.includes('frame_enhancer') }">
            <input type="checkbox" v-model="selectedProcessors" value="frame_enhancer" />
            帧增强
          </label>
        </div>

        <!-- face_swapper 选项 -->
        <div v-if="selectedProcessors.includes('face_swapper')" class="processor-card">
          <h4>换脸模型</h4>
          <select v-model="processorConfigs.face_swapper.model" class="select-box">
            <option value="blendswap_256">BlendSwap 256</option>
            <option value="ghost_1_256">Ghost 1 256</option>
            <option value="ghost_2_256">Ghost 2 256</option>
            <option value="ghost_3_256">Ghost 3 256</option>
            <option value="hififace_unofficial_256">HifiFace 256</option>
            <option value="hyperswap_1a_256">HyperSwap 1A 256</option>
            <option value="hyperswap_1b_256">HyperSwap 1B 256</option>
            <option value="hyperswap_1c_256">HyperSwap 1C 256</option>
            <option value="inswapper_128">InSwapper 128</option>
            <option value="inswapper_128_fp16">InSwapper 128 FP16</option>
            <option value="simswap_256">SimSwap 256</option>
            <option value="simswap_unofficial_512">SimSwap 512</option>
            <option value="uniface_256">UniFace 256</option>
          </select>
          <h4 style="margin-top: 10px;">分辨率增强</h4>
          <select v-model="processorConfigs.face_swapper.pixel_boost" class="select-box">
            <option value="128x128">128x128</option>
            <option value="256x256">256x256</option>
            <option value="384x384">384x384</option>
            <option value="512x512">512x512</option>
            <option value="768x768">768x768</option>
            <option value="1024x1024">1024x1024</option>
          </select>
          <h4 style="margin-top: 10px;">强度: {{ processorConfigs.face_swapper.weight }}</h4>
          <input
            type="range"
            v-model.number="processorConfigs.face_swapper.weight"
            min="0"
            max="1"
            step="0.05"
            class="slider"
          />
        </div>

        <!-- face_enhancer 选项 -->
        <div v-if="selectedProcessors.includes('face_enhancer')" class="processor-card">
          <h4>面部增强模型</h4>
          <select v-model="processorConfigs.face_enhancer.model" class="select-box">
            <option value="codeformer">CodeFormer</option>
            <option value="gfpgan_1.2">GFPGAN 1.2</option>
            <option value="gfpgan_1.3">GFPGAN 1.3</option>
            <option value="gfpgan_1.4">GFPGAN 1.4</option>
            <option value="gpen_bfr_256">GPEN BFR 256</option>
            <option value="gpen_bfr_512">GPEN BFR 512</option>
            <option value="gpen_bfr_1024">GPEN BFR 1024</option>
            <option value="gpen_bfr_2048">GPEN BFR 2048</option>
            <option value="restoreformer_plus_plus">RestoreFormer++</option>
          </select>
          <h4 style="margin-top: 10px;">强度: {{ processorConfigs.face_enhancer.weight }}</h4>
          <input
            type="range"
            v-model.number="processorConfigs.face_enhancer.weight"
            min="0"
            max="1"
            step="0.05"
            class="slider"
          />
        </div>

        <!-- frame_enhancer 选项 -->
        <div v-if="selectedProcessors.includes('frame_enhancer')" class="processor-card">
          <h4>帧增强模型</h4>
          <select v-model="processorConfigs.frame_enhancer.model" class="select-box">
            <option value="clear_reality_x4">Clear Reality x4</option>
            <option value="face_dat_x4">Face DAT x4</option>
            <option value="lsdir_x4">LSDIR x4</option>
            <option value="real_esrgan_x2">Real-ESRGAN x2</option>
            <option value="real_esrgan_x4">Real-ESRGAN x4</option>
            <option value="real_hatgan_x4">Real-HatGAN x4</option>
            <option value="span_kendata_x4">Span Kendata x4</option>
            <option value="swin2_sr_x4">Swin2SR x4</option>
            <option value="ultra_sharp_x4">Ultra Sharp x4</option>
            <option value="ultra_sharp_2_x4">Ultra Sharp 2 x4</option>
          </select>
        </div>

        <!-- 并发线程数 -->
        <div class="processor-card">
          <h4>并发线程数: {{ executionThreadCount }}</h4>
          <input
            type="range"
            v-model.number="executionThreadCount"
            min="1"
            max="16"
            step="1"
            class="slider"
          />
          <p class="hint">内存 32GB 建议 8 线程，内存小请调低避免崩溃</p>
        </div>
      </div>
    </section>

      </div>

      <!-- 右侧：人脸列表 + 操作 -->
      <div class="right-content">
            <!-- 目标文件上传 -->
            <section class="section">
              <h2>上传目标视频</h2>
              <div
                class="upload-area"
                :class="{ 'has-preview': targetPreviewUrl }"
                @click="!targetPreviewUrl && triggerTargetUpload()"
                @dragover.prevent
                @drop.prevent="handleTargetDrop"
              >
                <input
                  ref="targetInput"
                  type="file"
                  accept="video/*,image/*"
                  style="display: none"
                  @change="handleTargetChange"
                />
                <!-- 未上传时显示提示 -->
                <template v-if="!targetPreviewUrl">
                  <el-icon :size="40" color="#888"><video-play /></el-icon>
                  <p>拖拽文件到此处 或 <em>点击上传</em></p>
                  <p class="hint">支持 MP4 | MOV | AVI | WEBM (≤ 300MB)</p>
                </template>
                <!-- 已上传时显示预览 -->
                <template v-else>
                  <video
                    v-if="targetIsVideo"
                    :src="targetPreviewUrl"
                    controls
                    class="preview-media"
                    @click.stop
                  />
                  <img
                    v-else
                    :src="targetPreviewUrl"
                    class="preview-media"
                    @click.stop
                  />
                </template>
              </div>
              <div v-if="targetFileName" class="file-name">已选择: {{ targetFileName }}</div>
            </section>
            <!-- 检测按钮 -->
            <button class="detect-btn" :disabled="detecting || !targetFileName" @click="handleDetect">
              <el-icon v-if="detecting" class="spin"><loading /></el-icon>
              <span v-else>☺</span>
              {{ detecting ? '检测中...' : '检测目标人脸' }}
            </button>
        <!-- 人脸列表 -->
        <section v-if="faces.length > 0" class="section face-section">
      <h2>上传人脸照片</h2>
      <div class="face-grid">
        <div v-for="face in faces" :key="face.index" class="face-card">
          <div class="face-item">
            <img :src="face.thumbnail_url" class="face-img" />
            <span class="delete-btn" @click="deleteFace(face.index)">×</span>
          </div>
          <div class="arrow">➜</div>
          <div class="source-item" @click="triggerSourceUpload(face.index)">
            <input
              :ref="el => { if (el) sourceInputs[face.index] = el }"
              type="file"
              accept="image/*"
              style="display: none"
              @change="e => handleSourceChange(face.index, e)"
            />
            <img v-if="sourcePreviews[face.index]" :src="sourcePreviews[face.index]" class="face-img" />
            <div v-else class="placeholder">
              <el-icon :size="24"><camera /></el-icon>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 开始换脸 -->
    <button
      v-if="faces.length > 0"
      class="swap-btn"
      :disabled="swapping || Object.keys(sourceMap).length === 0"
      @click="handleSwap"
    >
      {{ swapping ? '换脸中...' : '立即换脸' }}
    </button>

    <!-- 进度 -->
    <div v-if="swapping || processing" class="progress-bar">
      <div class="progress-fill indeterminate"></div>
      <span class="progress-text">{{ processing ? '后端处理中，请稍候...' : '准备中...' }}</span>
    </div>

        <!-- 结果 -->
        <div v-if="resultUrl" class="result-section">
          <h2>换脸完成</h2>
          <a :href="resultUrl" download class="download-link">点击下载结果</a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { VideoPlay, Loading, Camera } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { uploadTarget, uploadSource, detectFaces, setSourceMap, startSwap } from './api'

const targetInput = ref<HTMLInputElement>()
const sourceInputs = reactive<Record<number, any>>({})
const targetFileName = ref('')
const targetPreviewUrl = ref('')
const targetIsVideo = ref(false)
const detecting = ref(false)
const swapping = ref(false)
const progress = ref(0)
const faces = ref<any[]>([])
const sourceMap = reactive<Record<number, string>>({})
const sourcePreviews = reactive<Record<number, string>>({})
const resultUrl = ref('')
const processing = ref(false)
const ws = ref<WebSocket | null>(null)
// processor options are built dynamically in handleSwap
const executionThreadCount = ref(8)
const selectedProcessors = ref<string[]>(['face_swapper'])
const processorConfigs = reactive<Record<string, any>>({
  face_swapper: { model: 'hyperswap_1a_256', pixel_boost: '512x512', weight: 0.5 },
  face_enhancer: { model: 'gfpgan_1.4', weight: 0.5 },
  frame_enhancer: { model: 'span_kendata_x4' }
})
const showProcessorOptions = ref(true)

function triggerTargetUpload() {
  targetInput.value?.click()
}

async function handleTargetChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  targetFileName.value = file.name
  targetPreviewUrl.value = URL.createObjectURL(file)
  targetIsVideo.value = file.type.startsWith('video/')
  // 清空旧状态
  faces.value = []
  Object.keys(sourceMap).forEach(k => delete sourceMap[+k])
  Object.keys(sourcePreviews).forEach(k => delete sourcePreviews[+k])
  try {
    const res = await uploadTarget(file)
    if (res.success) ElMessage.success('目标文件上传成功')
  } catch (err) {
    ElMessage.error('上传失败')
  }
}

async function handleTargetDrop(e: DragEvent) {
  const file = e.dataTransfer?.files[0]
  if (!file) return
  targetFileName.value = file.name
  targetPreviewUrl.value = URL.createObjectURL(file)
  targetIsVideo.value = file.type.startsWith('video/')
  // 清空旧状态
  faces.value = []
  Object.keys(sourceMap).forEach(k => delete sourceMap[+k])
  Object.keys(sourcePreviews).forEach(k => delete sourcePreviews[+k])
  try {
    const res = await uploadTarget(file)
    if (res.success) ElMessage.success('目标文件上传成功')
  } catch (err) {
    ElMessage.error('上传失败')
  }
}

async function handleDetect() {
  detecting.value = true
  faces.value = []
  Object.keys(sourceMap).forEach(k => delete sourceMap[+k])
  Object.keys(sourcePreviews).forEach(k => delete sourcePreviews[+k])

  try {
    const res = await detectFaces()
    if (res.success) {
      faces.value = res.faces
      ElMessage.success(`检测到 ${res.face_count} 张人脸`)
    } else {
      ElMessage.warning(res.message || '未检测到人脸')
    }
  } catch (err) {
    ElMessage.error('检测失败')
  } finally {
    detecting.value = false
  }
}

function triggerSourceUpload(index: number) {
  sourceInputs[index]?.click()
}

async function handleSourceChange(index: number, e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  try {
    const res = await uploadSource(file)
    if (res.success) {
      sourceMap[index] = res.path
      sourcePreviews[index] = '/uploads/' + res.path.split('/').pop()
      await setSourceMap(sourceMap)
      ElMessage.success(`源图 #${index + 1} 上传成功`)
    }
  } catch (err) {
    ElMessage.error('源图上传失败')
  }
}

function deleteFace(index: number) {
  faces.value = faces.value.filter(f => f.index !== index)
  delete sourceMap[index]
  delete sourcePreviews[index]
  setSourceMap(sourceMap)
}

function connectProgressWs() {
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${location.host}/api/ws/progress`
  const socket = new WebSocket(wsUrl)
  socket.onmessage = (event) => {
    const data = JSON.parse(event.data)
    processing.value = data.processing
    if (!data.processing && swapping.value) {
      // 后端处理完了，但 HTTP 请求可能还没返回，保持状态
    }
  }
  socket.onerror = () => { processing.value = false }
  socket.onclose = () => { processing.value = false }
  ws.value = socket
}

function disconnectProgressWs() {
  ws.value?.close()
  ws.value = null
}

async function handleSwap() {
  swapping.value = true
  progress.value = 0
  resultUrl.value = ''
  connectProgressWs()

  try {
    // 构建处理器参数
    const processorOptions: Record<string, any> = {}
    if (selectedProcessors.value.includes('face_swapper')) {
      processorOptions.face_swapper_model = processorConfigs.face_swapper.model
      processorOptions.face_swapper_pixel_boost = processorConfigs.face_swapper.pixel_boost
      processorOptions.face_swapper_weight = processorConfigs.face_swapper.weight
    }
    if (selectedProcessors.value.includes('face_enhancer')) {
      processorOptions.face_enhancer_model = processorConfigs.face_enhancer.model
      processorOptions.face_enhancer_weight = processorConfigs.face_enhancer.weight
    }
    if (selectedProcessors.value.includes('frame_enhancer')) {
      processorOptions.frame_enhancer_model = processorConfigs.frame_enhancer.model
    }

    const res = await startSwap(selectedProcessors.value, processorOptions, executionThreadCount.value)
    if (res.success) {
      resultUrl.value = '/uploads/' + res.output_path.split('/').pop()
      ElMessage.success('换脸完成！')
    } else {
      ElMessage.error(res.message || '换脸失败')
    }
  } catch (err: any) {
    ElMessage.error('换脸出错: ' + (err.message || '未知错误'))
  } finally {
    swapping.value = false
    disconnectProgressWs()
  }
}
</script>

<style scoped>
.facefusion-app {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
  background: #1e1e2e;
  min-height: 100vh;
  color: #fff;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.main-layout {
  display: flex;
  flex-direction: row;
  gap: 24px;
  align-items: flex-start;
}

.left-sidebar {
  width: 320px;
  flex-shrink: 0;
  align-self: flex-start;
}

.right-content {
  flex: 1;
  min-width: 0;
}

.app-header {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 24px;
}

.app-header h1 {
  font-size: 28px;
  font-weight: 700;
  color: #e94560;
  margin: 0;
}

.version {
  color: #888;
  font-size: 14px;
}

.section {
  margin-bottom: 20px;
}

.section h2 {
  font-size: 16px;
  margin-bottom: 12px;
  color: #ccc;
}

.upload-area {
  border: 2px dashed #444;
  border-radius: 12px;
  padding: 32px;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.2s;
  min-height: 200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.upload-area:hover {
  border-color: #e94560;
}

.upload-area.has-preview {
  padding: 8px;
  min-height: auto;
}

.upload-area .preview-media {
  max-width: 100%;
  max-height: 320px;
  border-radius: 8px;
  cursor: default;
  display: block;
}

.upload-area p {
  margin-top: 12px;
  color: #aaa;
}

.upload-area em {
  color: #e94560;
  font-style: normal;
}

.hint {
  font-size: 12px;
  color: #666;
}

.file-name {
  margin-top: 8px;
  font-size: 13px;
  color: #888;
}

.preview-area {
  margin-top: 12px;
  border-radius: 12px;
  overflow: hidden;
  background: #252535;
  display: flex;
  justify-content: center;
  align-items: center;
  max-height: 400px;
}

.preview-media {
  max-width: 100%;
  max-height: 400px;
  border-radius: 12px;
  display: block;
}

.detect-btn {
  width: 100%;
  padding: 16px;
  border: none;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  font-size: 18px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
  margin-bottom: 20px;
}

.detect-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.detect-btn:hover:not(:disabled) {
  opacity: 0.9;
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.face-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.face-card {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #252535;
  padding: 12px;
  border-radius: 12px;
  position: relative;
}

.face-item, .source-item {
  position: relative;
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.face-img {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #444;
}

.delete-btn {
  position: absolute;
  top: -4px;
  right: -4px;
  width: 20px;
  height: 20px;
  background: #e94560;
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  cursor: pointer;
  z-index: 2;
}

.arrow {
  font-size: 20px;
  color: #888;
}

.placeholder {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  border: 2px dashed #555;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.placeholder:hover {
  border-color: #e94560;
}

.swap-btn {
  width: 100%;
  padding: 16px;
  border: none;
  border-radius: 12px;
  background: linear-gradient(135deg, #f6d365 0%, #fda085 100%);
  color: #333;
  font-size: 18px;
  font-weight: 700;
  cursor: pointer;
  margin-top: 16px;
}

.swap-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.progress-bar {
  margin-top: 16px;
  height: 8px;
  background: #333;
  border-radius: 4px;
  overflow: hidden;
  position: relative;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
  transition: width 0.3s;
}

.progress-fill.indeterminate {
  width: 40%;
  animation: indeterminate 1.5s ease-in-out infinite;
  background: linear-gradient(90deg, #667eea, #764ba2, #667eea);
}

@keyframes indeterminate {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(250%); }
}

.progress-text {
  position: absolute;
  top: 12px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 12px;
  color: #888;
}

.result-section {
  margin-top: 24px;
  padding: 16px;
  background: #252535;
  border-radius: 12px;
  text-align: center;
}

.download-link {
  display: inline-block;
  margin-top: 8px;
  padding: 10px 24px;
  background: #e94560;
  color: #fff;
  border-radius: 8px;
  text-decoration: none;
}

/* 处理器选项 */
.processor-section {
  background: #252535;
  border-radius: 12px;
  overflow: hidden;
}

.processor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  background: #2a2a40;
}

.processor-header h2 {
  margin: 0;
  font-size: 15px;
  color: #ccc;
}

.toggle-icon {
  color: #888;
  font-size: 12px;
}

.processor-body {
  padding: 16px;
}

.processor-chips {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.chip {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: 20px;
  background: #333;
  color: #aaa;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.chip input {
  display: none;
}

.chip.active {
  background: #e94560;
  color: #fff;
  border-color: #e94560;
}

.processor-card {
  background: #1e1e2e;
  border-radius: 10px;
  padding: 14px;
  margin-bottom: 12px;
}

.processor-card h4 {
  margin: 0 0 8px 0;
  font-size: 13px;
  color: #aaa;
  font-weight: 500;
}

.select-box {
  width: 100%;
  padding: 8px 12px;
  border-radius: 8px;
  border: 1px solid #444;
  background: #333;
  color: #fff;
  font-size: 13px;
  outline: none;
}

.select-box:focus {
  border-color: #e94560;
}

.slider {
  width: 100%;
  -webkit-appearance: none;
  appearance: none;
  height: 6px;
  border-radius: 3px;
  background: #444;
  outline: none;
}

.slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #e94560;
  cursor: pointer;
}

.slider::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #e94560;
  cursor: pointer;
  border: none;
}
</style>
