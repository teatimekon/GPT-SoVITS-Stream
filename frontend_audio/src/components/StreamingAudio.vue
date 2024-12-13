<template>
  <div class="streaming-audio">
    <div v-if="dialogHistory.length" class="dialog-history">
      <div v-for="(dialog, index) in dialogHistory" :key="index" class="dialog-item">
        <div class="question-container">
          <div class="question-label">问题：</div>
          <div class="question-content">{{ dialog.question }}</div>
        </div>
        <div class="answer-container">
          <div class="answer-title">AI回答：</div>
          <div class="answer-content">
            <div class="paragraph">
              <span
                v-for="chunk in dialog.answer" 
                :key="chunk.index"
                :class="['text-chunk', { 
                  'active': currentDialogIndex === index && currentChunkIndex === chunk.index 
                }]"
              >{{ chunk.text }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="input-section">
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
        <el-button 
          type="danger" 
          @click="clearHistory"
          :disabled="isPlaying || !dialogHistory.length"
        >
          清空历史
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../services/api'


const statusText = ref('')
const requestId = ref(`${Date.now().toString()}-${Math.random().toString(36).substring(2, 15)}`)
const isLoading = ref(false)
const isPlaying = ref(false)
const question = ref('')
const audioContext = ref(null)
const currentSource = ref(null)
let isFirstChunk = true
const pendingBuffer = ref(new Uint8Array(0))
const textChunks = ref([])
const currentChunkIndex = ref(null)
const answerContentRef = ref(null)
const dialogHistory = ref([])
const currentDialogIndex = ref(null)

// 添加重置状态的函数
const resetState = () => {
  isPlaying.value = false
  isLoading.value = false
  isFirstChunk = true
  currentChunkIndex.value = null
  pendingBuffer.value = new Uint8Array(0)
}

// 定义 props
const props = defineProps({
  checkCanPlay: {
    type: Function,
    default: async () => true
  },
  continuitySentences: {
    type: Array,
    default: () => []
  },
  goodsInfo: {
    type: Object,
    default: () => {}
  }
})

// 初始化AudioContext
onMounted(() => {
  try {
    audioContext.value = new (window.AudioContext || window.webkitAudioContext)({
      sampleRate: 32000  // 设置采样率
    })
    console.log('AudioContext initialized:', audioContext.value)
  } catch (error) {
    console.error('初始化AudioContext失败:', error)
    ElMessage.error('初始化音频播放器失败')
  }
})

// 处理播放按钮点击
const handlePlay = async () => {
  if (!question.value.trim()) {
    ElMessage.warning('请输入问题')
    return
  }
  
  isLoading.value = true
  try {
    // 拼接历史对话和当前问题
    let fullQuestion = '之前用户的问题与你的回答如下所示：\n=============================\n'
    emit('streamStart') 
    if (dialogHistory.value.length > 0) {
      // 添加历史对话
      dialogHistory.value.forEach(dialog => {
        const answer = dialog.answer.map(chunk => chunk.text).join('')
        if (answer) {
          fullQuestion += `用户问：${dialog.question}\n AI回答：${answer}\n`
          fullQuestion += `=============================\n`
        }
      })
    }
    // 添加当前问题
    fullQuestion += ` \n最后，请你回答用户的问题：${question.value}`
    console.log('Full question:', fullQuestion)
    // 创建新的对话记录
    const newDialog = {
      question: question.value,
      answer: []
    }
    dialogHistory.value.push(newDialog)
    currentDialogIndex.value = dialogHistory.value.length - 1
    
    // 使用完整的问题文本调用startStream
    await startStream(fullQuestion)
  } catch (error) {
    console.error('开始播放失败:', error)
    ElMessage.error('播放失败')
  } finally {
    isLoading.value = false
  }
}

// 播放单个音频块
const playAudioChunk = async (audioData) => {
  if (!audioContext.value) {
    console.error('AudioContext not initialized')
    return
  }
  
  try {
    console.log('Playing audio chunk, size:', audioData.length)
    
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
    
    // 每个字节组合成一个 Int16 值
    for (let i = 0; i < processableData.length; i += 2) {
      const low = processableData[i]
      const high = processableData[i + 1]
      int16Array[i / 2] = (high << 8) | low
    }
    
    // 如果没有可处理的完整数据，直接返回
    if (int16Array.length === 0) {
      console.log('No complete audio data to process')
      return
    }
    
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
    console.log('Started playing audio chunk')
    
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
    // 不再重置文本chunks，而是添加到当前对话
    currentChunkIndex.value = null
    
    console.log('props.goodsInfo', props.goodsInfo)
    const response = await api.chatStream(text, requestId.value, props.goodsInfo)
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) {
        emit('streamEnd')
        resetState()
        break
      }

      // 将新的数据添加到buffer
      buffer += decoder.decode(value, { stream: true })
      
      // 按换行符分割并处理完整的JSON
      const lines = buffer.split('\n')
      buffer = lines.pop() // 保留最后一个不完整的行
      await props.checkCanPlay()

      for (const line of lines) {
        if (!line.trim()) continue
        
        try {
          const chunk = JSON.parse(line)
          console.log('Received chunk:', chunk)
          
          // 添加到当前对话的回答中
          if (currentDialogIndex.value !== null) {
            dialogHistory.value[currentDialogIndex.value].answer.push({
              text: chunk.text,
              index: chunk.index
            })
          }
          
          // 更新当前chunk索引
          currentChunkIndex.value = chunk.index
          
          // 自动滚动到最新内容
          await nextTick()
          const lastDialog = document.querySelector('.dialog-item:last-child')
          if (lastDialog) {
            lastDialog.scrollIntoView({ behavior: 'smooth', block: 'end' })
          }
          
          // 发送文本给父组件
          emit('chunkText', {
            text: chunk.text,
            index: chunk.index
          })
          
          // 将base64音频数据转回Uint8Array
          const audioData = new Uint8Array(
            atob(chunk.audio)
              .split('')
              .map(char => char.charCodeAt(0))
          )
          
          console.log('Decoded audio data size:', audioData.length)
          
          // 播放音频
          
          await playAudioChunk(audioData)
          
          if (isFirstChunk) {
            isFirstChunk = false
            isPlaying.value = true
          }
        } catch (error) {
          console.error('处理数据chunk失败:', error, 'Line:', line)
        }
      }
    }
    
  } catch (error) {
    console.error('处理音频流失败:', error)
    resetState()
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
      resetState()
      emit('streamEnd')
    } catch (error) {
      console.error('停止播放失败:', error)
      resetState()
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

// 定义事件
const emit = defineEmits([
  'streamStart',
  'streamEnd',
  'beforeStreamStart',
  'beforePlayNextChunk',
  'chunkText'  // 新增事件用于传递文本
])

// 新增清空历史功能
const clearHistory = () => {
  dialogHistory.value = []
  currentDialogIndex.value = null
  currentChunkIndex.value = null
  question.value = ''
}
</script>

<style scoped>
.streaming-audio {
  display: flex;
  flex-direction: column;
  gap: 20px;
  height: 100%;
}

.dialog-history {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 16px;
}

.dialog-item {
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  padding: 16px;
}

.question-container {
  display: flex;
  gap: 8px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
}

.question-label {
  font-weight: 500;
  color: #606266;
}

.question-content {
  color: #303133;
  flex: 1;
}

.input-section {
  position: sticky;
  bottom: 0;
  background: #fff;
  padding: 16px;
  border-top: 1px solid #e4e7ed;
  z-index: 1;
}

.answer-container {
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
}

.answer-title {
  padding: 12px 16px;
  font-size: 14px;
  font-weight: 500;
  color: #606266;
  background: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
}

.answer-content {
  padding: 16px;
}

.paragraph {
  line-height: 1.8;
  text-align: justify;
  color: #303133;
  font-size: 14px;
}

.text-chunk {
  display: inline;
  transition: all 0.3s ease;
  padding: 2px 0;
  margin: 0;
  border-radius: 2px;
}

.text-chunk.active {
  background-color: #ecf5ff;
  box-shadow: 0 0 0 2px #ecf5ff;
}

.controls {
  display: flex;
  gap: 12px;
  margin-top: 12px;
}

.dialog-history::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.dialog-history::-webkit-scrollbar-thumb {
  border-radius: 3px;
  background: #c0c4cc;
}

.dialog-history::-webkit-scrollbar-track {
  border-radius: 3px;
  background: #f5f7fa;
}

.dialog-item {
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
