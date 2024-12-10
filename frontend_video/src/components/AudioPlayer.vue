<template>
  <div class="video-player">
    <div class="loading-state" v-if="loading">
      <el-button :loading="true">生成中...</el-button>
    </div>
    <div v-else>
      <video 
        ref="audioRef"
        :src="currentAudio?.url"
        @ended="handleEnded"
        @pause="handlePause"
        @play="handlePlay"
        controls
        controlsList="nodownload"
        class="video-element"
      />
      <div class="player-controls">
        <div class="time-info" v-if="duration">
          {{ formatTime(currentTime) }} / {{ formatTime(duration) }}
        </div>
        <div class="playlist-controls">
          <span class="playlist-info" v-if="playlist.length">
            {{ currentIndex + 1 }}/{{ playlist.length }}
          </span>
          <el-switch
            v-model="autoPlayNext"
            active-text="自动播放下一个"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  playlist: {
    type: Array,
    default: () => []
  },
  loading: Boolean,
  shouldPlayNext: {
    type: Boolean,
    default: true
  },
  modelValue: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['play', 'pause', 'ended', 'chunkStart', 'chunkEnd', 'update:modelValue'])

// 播放器状态
const audioRef = ref(null)
const currentIndex = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})
const currentKey = ref('content')
const currentTime = ref(0)
const duration = ref(0)
const isPlaying = ref(false)
const autoPlayNext = ref(true)
const autoPlayEnabled = ref(true)

// 计算当前播放的音频
const currentAudio = computed(() => props.playlist[currentIndex.value]?.[currentKey.value] || null)

// 播放控制相关方法
const playAudio = async () => {
  if (!audioRef.value || !autoPlayEnabled.value) return
  
  try {
    await audioRef.value.play()
  } catch (error) {
    if (error.name === 'AbortError') {
      console.log('视频加载被打断，正在切换到新视频')
    } else {
      console.error('播放出错:', error)
    }
  }
}

const playNext = async () => {
  if (!autoPlayEnabled.value) return
  let haveStreamPlayed = false
  console.log('shouldPlayNext', props.shouldPlayNext)
  while (!props.shouldPlayNext) {
    await new Promise(r => setTimeout(r, 100))
    console.log('刚刚流式播放啦')
    haveStreamPlayed = true
  }
  if (!haveStreamPlayed) {
    currentKey.value = 'content'
    currentIndex.value = (currentIndex.value + 1) % props.playlist.length
  }
  else {
    currentKey.value = 'continuity_sentences'
  }
  emit('chunkStart', {
    index: currentIndex.value,
    audio: currentAudio.value
  })
  await playAudio()
}

// 事件处理器
const handleEnded = async () => {
  isPlaying.value = false
  emit('chunkEnd', {
    index: currentIndex.value,
    audio: currentAudio.value
  })
  
  if (autoPlayNext.value && autoPlayEnabled.value) {
    await playNext()
  }
}

const handlePause = () => {
  isPlaying.value = false
  emit('pause')
}

const handlePlay = () => {
  isPlaying.value = true
  emit('play')
}

// 时间更新处理
const updateTime = () => {
  if (audioRef.value) {
    currentTime.value = audioRef.value.currentTime
    duration.value = audioRef.value.duration
  }
}

// ��听播放列表变化
watch(() => props.playlist, (newPlaylist) => {
  if (newPlaylist.length > 0) {
    currentIndex.value = 0
    if (autoPlayNext.value) {
      audioRef.value?.load()
      playAudio()
    }
  }
}, { deep: true })

// 监听当前音频变化
watch(() => currentAudio.value, () => {
  if (audioRef.value) {
    audioRef.value.load()
    setTimeout(() => {
      if (autoPlayNext.value) {
        playAudio()
      }
    }, 500)
  }
})

// 生命周期钩子
onMounted(() => {
  audioRef.value?.addEventListener('timeupdate', updateTime)
})

onUnmounted(() => {
  audioRef.value?.removeEventListener('timeupdate', updateTime)
})

// 工具函数
const formatTime = (time) => {
  if (!time) return '00:00'
  const minutes = Math.floor(time / 60)
  const seconds = Math.floor(time % 60)
  return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
}

// 暂停自动播放
const pauseAutoPlay = () => {
  autoPlayEnabled.value = false
  // 确保当前播放也暂停
  audioRef.value?.pause()
}

// 恢复自动播放
const resumeAutoPlay = () => {
  autoPlayEnabled.value = true
  // 如果需要继续播放，可以在这里添加播放逻辑
  if (autoPlayNext.value && !isPlaying.value) {
    playAudio()
  }
}

// 对外暴露的方法
defineExpose({
  playNext,
  play: playAudio,
  pause: () => audioRef.value?.pause(),
  waitForCurrentChunk: () => {
    return new Promise((resolve) => {
      if (!audioRef.value || audioRef.value.ended || audioRef.value.paused) {
        resolve()
        return
      }
      
      const onEnd = () => {
        audioRef.value?.removeEventListener('ended', onEnd)
        resolve()
      }
      
      audioRef.value.addEventListener('ended', onEnd)
    })
  }
})
</script>

<style scoped>
.video-player {
  min-width: 300px;
  padding: 16px;
  background: #fafafa;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.video-element {
  width: 100%;
  height: auto;
  margin-bottom: 8px;
  border-radius: 8px;
  outline: none;
}

.player-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
  padding: 0 8px;
}

.time-info {
  font-size: 12px;
  color: #606266;
  font-family: 'Roboto Mono', monospace;
  background: #f5f7fa;
  padding: 4px 8px;
  border-radius: 4px;
}

.loading-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 54px;
  background: #f5f7fa;
  border-radius: 8px;
}
</style> 