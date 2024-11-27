<template>
  <div class="streaming-audio">
    <el-input
      v-model="question"
      type="textarea"
      :rows="3"
      placeholder="请输入您的问题"
      :disabled="isPlaying"
    />
    
    <div class="controls">
      <el-button 
        type="primary" 
        @click="handlePlay"
        :loading="isLoading"
        :disabled="isPlaying || !question.trim()"
      >
        播放
      </el-button>
      <el-button 
        type="warning" 
        @click="stopStream"
        :disabled="!isPlaying"
      >
        停止
      </el-button>
    </div>
    
    <audio 
      ref="audioElement"
      controls
      @playing="handlePlaying"
      @pause="handlePause"
      @ended="handleEnded"
      @error="handleError"
    ></audio>
    <div class="status-text" v-if="statusText">{{ statusText }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../services/api'

const audioElement = ref(null)
const statusText = ref('')
const requestId = ref('')
const isLoading = ref(false)
const isPlaying = ref(false)
const question = ref('')
const audioContext = ref(null)
const currentSource = ref(null)
let isFirstChunk = true
const pendingBuffer = ref(new Uint8Array(0))

// 处理播放按钮点击
const handlePlay = async () => {
  if (!question.value.trim()) {
    ElMessage.warning('请输入问题')
    return
  }
  
  isLoading.value = true
  try {
    // 初始化AudioContext
    if (!audioContext.value) {
      audioContext.value = new (window.AudioContext || window.webkitAudioContext)({
        sampleRate: 32000
      })
    }
    isFirstChunk = true
    await startStream(question.value)
  } finally {
    isLoading.value = false
  }
}

// 播放单个音频块
const playAudioChunk = async (audioData) => {
  if (!audioContext.value) return
  
  try {
    // 合并之前未处理的数据和新数据
    const combinedBuffer = new Uint8Array(pendingBuffer.value.length + audioData.length)
    combinedBuffer.set(pendingBuffer.value)
    combinedBuffer.set(audioData, pendingBuffer.value.length)
    
    // 计算能够完整处理的字节数（必须是2的倍数）
    const processableLength = Math.floor(combinedBuffer.length / 2) * 2
    
    // 保存剩余的字节到pendingBuffer
    pendingBuffer.value = combinedBuffer.slice(processableLength)
    
    // 只处理完整的字节对
    const processableData = combinedBuffer.slice(0, processableLength)
    
    // 创建Int16Array来存储转换后的数据
    const int16Array = new Int16Array(processableData.length / 2)
    
    // 每两个字节组合成一个 Int16 值
    for (let i = 0; i < processableData.length; i += 2) {
      const low = processableData[i]
      const high = processableData[i + 1]
      int16Array[i / 2] = (high << 8) | low
    }
    
    // 如果没有可处理的完整数据，直接返回
    if (int16Array.length === 0) return
    
    // 创建音频buffer
    const audioBuffer = audioContext.value.createBuffer(1, int16Array.length, 32000)
    const channelData = audioBuffer.getChannelData(0)
    
    // 将 Int16Array 数据归一化到 [-1,1] 范围内
    for (let i = 0; i < int16Array.length; i++) {
      channelData[i] = int16Array[i] / 32768.0
    }
    
    // 如果有正在播放的源，等待其结束
    if (currentSource.value) {
      await new Promise(resolve => {
        currentSource.value.onended = resolve
      })
    }
    
    // 创建新的音频源
    const source = audioContext.value.createBufferSource()
    source.buffer = audioBuffer
    source.connect(audioContext.value.destination)
    currentSource.value = source
    
    // 播放音频
    const startTime = audioContext.value.currentTime
    source.start(startTime)
    
    // 等待播放完成
    await new Promise(resolve => {
      source.onended = () => {
        currentSource.value = null
        resolve()
      }
    })
  } catch (error) {
    console.error('播放音频块失败:', error)
  }
}

// 开始流式播放
const startStream = async (text) => {
  try {
    requestId.value = Date.now().toString()
    const response = await api.chatStream(text, requestId.value)
    
    const reader = response.body.getReader()
    let totalLength = 0
    // 开始读取流
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      totalLength += value.length
      console.log(totalLength)
      

      
      // 播放音频块
      await playAudioChunk(value)
      
      // 第一个块播放后更新状态
      if (isFirstChunk) {
        isFirstChunk = false
        isPlaying.value = true
      }
    }
    
  } catch (error) {
    console.error('处理音频流失败:', error)
    statusText.value = '音频播放出错'
    isPlaying.value = false
  }
}

// 停止播放
const stopStream = async () => {
  if (requestId.value) {
    try {
      await api.killRequest(requestId.value)
      if (currentSource.value) {
        currentSource.value.stop()
        currentSource.value = null
      }
      if (audioContext.value) {
        await audioContext.value.close()
        audioContext.value = null
      }
      // 清空缓冲区
      pendingBuffer.value = new Uint8Array(0)
      statusText.value = '已停止播放'
      isPlaying.value = false
    } catch (error) {
      console.error('停止播放失败:', error)
    }
  }
}

// 事件处理器
const handlePlaying = () => {
  statusText.value = '正在播放'
  isPlaying.value = true
}

const handlePause = () => {
  statusText.value = '已暂停'
  isPlaying.value = false
}

const handleEnded = () => {
  statusText.value = '播放结束'
  isPlaying.value = false
}

const handleError = (e) => {
  console.error('音频播放错误:', e)
  statusText.value = '音频播放出错'
  isPlaying.value = false
}

// 暴露方法给父组件
defineExpose({
  startStream,
  stopStream
})

onMounted(() => {
  statusText.value = '等待播放'
})
</script>

<style scoped>
.streaming-audio {
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  width: 100%;
  max-width: 600px;
  margin: 0 auto;
}

.el-input {
  width: 100%;
}

.controls {
  display: flex;
  gap: 10px;
  width: 100%;
  justify-content: center;
}

audio {
  width: 100%;
}

.status-text {
  color: #909399;
  font-size: 14px;
}
</style>
