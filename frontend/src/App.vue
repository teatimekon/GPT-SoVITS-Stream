<template>
  <el-container class="app-container">
    <el-header class="app-header">
      <h1>商品口播生成系统</h1>
    </el-header>
    
    <el-container>
      <el-aside width="500px">
        <goods-form @content-generated="handleContentGenerated"/>
      </el-aside>
      
      <el-main>
        <el-card class="content-card">
          <template #header>
            <div class="card-header">
              <span>生成的口播文本</span>
              <div class="audio-controls" v-if="generatedContent">
                <el-button 
                  type="primary"
                  @click="generateAudio"
                  :loading="isLoading"
                  :disabled="!!audioUrl"
                >
                  生成语音
                </el-button>
                <audio-player 
                  v-if="audioUrl"
                  :audio-src="audioUrl"
                  :loading="isLoading"
                  @play="handlePlay"
                  @pause="handlePause"
                  @ended="handleEnded"
                />
              </div>
            </div>
          </template>
          <div class="content" v-if="generatedContent">{{ generatedContent }}</div>
          <el-empty v-else description="暂无内容" />
        </el-card>
        
        <el-card class="stream-card">
          <template #header>
            <div class="card-header">
              <span>实时音频流</span>
            </div>
          </template>
          <streaming-audio ref="streamingAudioRef" />
        </el-card>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref } from 'vue'
import { v4 as uuidv4 } from 'uuid'
import { ElMessage } from 'element-plus'
import GoodsForm from './components/GoodsForm.vue'
import StreamingAudio from './components/StreamingAudio.vue'
import AudioPlayer from './components/AudioPlayer.vue'
import { api } from './services/api'

const generatedContent = ref('')
const audioUrl = ref('')
const isPlaying = ref(false)
const isLoading = ref(false)
const currentRequestId = ref('')
const streamingAudioRef = ref(null)

const handleContentGenerated = (content) => {
  console.log('handleContentGenerated', content)
  generatedContent.value = content
  audioUrl.value = ''
}

const generateAudio = async () => {
  try {
    isLoading.value = true
    currentRequestId.value = uuidv4()
    audioUrl.value = await api.getTTS(generatedContent.value, currentRequestId.value)
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

const handleEnded = () => {
  isPlaying.value = false
  currentRequestId.value = ''
}
</script>

<style>
.app-container {
  min-height: 100vh;
}

.app-header {
  background-color: #409EFF;
  color: white;
  display: flex;
  align-items: center;
  padding: 0 20px;
}

.app-header h1 {
  margin: 0;
  font-size: 20px;
}

.content-card,
.stream-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.content {
  white-space: pre-wrap;
  line-height: 1.6;
}

.el-main {
  padding: 20px;
  background: #f5f7fa;
}

.el-aside {
  background: #f5f7fa;
  padding: 20px;
}

.chat-container {
  padding: 20px;
}

.chat-container .el-input {
  margin-bottom: 15px;
}

.status-area {
  margin-top: 15px;
}

.status-text {
  display: block;
  text-align: center;
  color: #909399;
  margin-top: 10px;
}

.audio-controls {
  display: flex;
  gap: 10px;
  align-items: center;
}
</style>
