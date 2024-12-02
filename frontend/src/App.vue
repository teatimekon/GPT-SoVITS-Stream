<template>
  <el-container class="app-container">
    <el-header class="app-header">
      <h1>数字人直播</h1>
    </el-header>
    
    <el-container class="main-container">
      <el-aside width="500px" class="fixed-aside">
        <goods-form @content-generated="handleContentGenerated"/>
      </el-aside>
      
      <el-main class="fixed-main">
        <el-card class="content-card">
          <template #header>
            <div class="card-header">
              <span>生成的口播文本</span>
              <el-button 
                v-if="generatedContent && !audioChunks.length"
                type="primary"
                @click="generateAudio"
                :loading="isLoading"
                class="generate-btn"
              >
                生成语音
              </el-button>
            </div>
          </template>
          
          <div class="content" v-if="generatedContent">
            <div class="content-text">{{ generatedContent }}</div>
            <div v-if="audioChunks.length" class="audio-section">
              <audio-player 
                ref="audioPlayerRef"
                :playlist="audioChunks"
                :loading="isLoading"
                :should-play-next="shouldPlayNext"
                @play="handlePlay"
                @pause="handlePause"
                @chunkEnd="handleChunkEnd"
                @chunkStart="handleChunkStart"
              />
            </div>
          </div>
          <el-empty v-else description="暂无内容" />
        </el-card>
        
        <el-card class="stream-card">
          <template #header>
            <div class="card-header">
              <span>实时音频流</span>
            </div>
          </template>
          <streaming-audio 
            ref="streamingAudioRef" 
            :checkCanPlay="checkCanPlay"
            @stream-start="handleStreamStart" 
            @stream-end="handleStreamEnd"
          />
        </el-card>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, watch } from 'vue'
import { v4 as uuidv4 } from 'uuid'
import { ElMessage } from 'element-plus'
import GoodsForm from './components/GoodsForm.vue'
import StreamingAudio from './components/StreamingAudio.vue'
import AudioPlayer from './components/AudioPlayer.vue'
import { api } from './services/api'

const generatedContent = ref('')
const audioChunks = ref([])
const isPlaying = ref(false)
const isLoading = ref(false)
const currentRequestId = ref('')
const audioPlayerRef = ref(null)
const streamingAudioRef = ref(null)
const shouldPlayNext = ref(true)
const canStreamPlay = ref(false)

const handleContentGenerated = (content, chunks) => {
  console.log('handleContentGenerated', content, chunks)
  generatedContent.value = content
  audioChunks.value = []
}

const generateAudio = async () => {
  try {
    isLoading.value = true
    currentRequestId.value = uuidv4()
    
    const chunks = generatedContent.value
      .split('\n\n')
      .map((content, index) => ({
        content,
        rank: index + 1
      }))
    
    const audioPromises = chunks.map(chunk => 
      api.getTTS(chunk.content, currentRequestId.value, chunk.rank)
    )

    const results = await Promise.all(audioPromises)
    audioChunks.value = results.sort((a, b) => a.rank - b.rank)
    
  } catch (error) {
    console.error('获取音频失败:', error)
    ElMessage.error('获取音频失败')
  } finally {
    isLoading.value = false
  }
}

const handlePlay = () => {
  isPlaying.value = true
}

const handlePause = () => {
  isPlaying.value = false
}

const handleStreamStart = () => {
  if (audioPlayerRef.value) {
    console.log('流式处理开始,handleStreamStart', audioPlayerRef.value)
    shouldPlayNext.value = false
  }
}

const handleStreamEnd = () => {
  console.log('流式处理结束,handleStreamEnd', audioPlayerRef.value)
  canStreamPlay.value = false
  if (audioPlayerRef.value) {
    shouldPlayNext.value = true
  }
}

const handleChunkEnd = async ({ index, audio }) => {
  console.log(`音频块 ${index + 1}/${audioChunks.value.length} 播放完成`)
  canStreamPlay.value = true

  if (index === audioChunks.value.length - 1) {
    console.log('所有音频播放完成')
    
  }
}

const handleChunkStart = () => {
  console.log('handleChunkStart')
  canStreamPlay.value = false
}

const checkCanPlay = async () => {
  console.log('checkCanPlay', canStreamPlay.value)
  while (!canStreamPlay.value) {
    console.log('checkCanPlay waiting')
    await new Promise(r => setTimeout(r, 100))
  }
}
</script>

<style>
.app-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e7ed 100%);
}

.app-header {
  background: linear-gradient(90deg, #409EFF 0%, #36cfc9 100%);
  color: white;
  display: flex;
  align-items: center;
  padding: 0 20px;
  height: 60px;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1);
}

.app-header h1 {
  margin: 0;
  font-size: 22px;
  font-weight: 500;
}

.main-container {
  height: calc(100vh - 60px);
  overflow: hidden;
}

.fixed-aside {
  height: 100%;
  overflow-y: auto;
  background: transparent;
  padding: 24px;
  border-right: 1px solid #ebeef5;
}

.fixed-main {
  height: 100%;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.content-card,
.stream-card {
  margin-bottom: 0;
  flex-shrink: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #ebeef5;
  background: #fafafa;
  border-radius: 8px 8px 0 0;
}

.card-header span {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.content {
  white-space: pre-wrap;
  line-height: 1.8;
  padding: 24px;
  color: #303133;
  font-size: 14px;
  background: #fff;
  border-radius: 8px;
  position: relative;
}

.content-text {
  height: 200px;
  overflow-y: auto;
  padding-right: 10px;
}

.audio-section {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

.generate-btn {
  padding: 8px 20px;
  font-size: 14px;
  transition: all 0.3s ease;
}

.generate-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(64,158,255,0.2);
}

.el-main {
  padding: 24px;
}

.el-aside {
  background: transparent;
  padding: 24px;
  border-right: 1px solid #ebeef5;
}

.audio-controls {
  display: flex;
  gap: 12px;
  align-items: center;
}

/* 自定义 Element Plus 组件样式 */
:deep(.el-button) {
  border-radius: 6px;
  font-weight: 500;
}

:deep(.el-button--primary) {
  background: linear-gradient(90deg, #409EFF 0%, #36cfc9 100%);
  border: none;
}

:deep(.el-button--warning) {
  background: linear-gradient(90deg, #f56c6c 0%, #f39c12 100%);
  border: none;
}

:deep(.el-input__wrapper) {
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

:deep(.el-card) {
  border: none;
  overflow: visible;
}

/* 美化滚动条 */
.fixed-aside::-webkit-scrollbar,
.fixed-main::-webkit-scrollbar,
.content-text::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.fixed-aside::-webkit-scrollbar-thumb,
.fixed-main::-webkit-scrollbar-thumb,
.content-text::-webkit-scrollbar-thumb {
  border-radius: 3px;
  background: #c0c4cc;
}

.fixed-aside::-webkit-scrollbar-track,
.fixed-main::-webkit-scrollbar-track,
.content-text::-webkit-scrollbar-track {
  border-radius: 3px;
  background: #f5f7fa;
}

.playlist-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.playlist-info {
  font-size: 12px;
  color: #606266;
  background: #f5f7fa;
  padding: 4px 8px;
  border-radius: 4px;
  font-family: 'Roboto Mono', monospace;
}
</style>
