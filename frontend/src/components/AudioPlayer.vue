<template>
  <div class="audio-player">
    <div class="loading-state" v-if="loading">
      <el-button :loading="true">生成中...</el-button>
    </div>
    <div v-else>
      <audio 
        ref="audioRef"
        :src="audioSrc"
        @ended="handleEnded"
        @pause="handlePause"
        @play="handlePlay"
        controls
        loop
        controlsList="nodownload"
        class="audio-element"
      />
      <div class="player-controls">
        <div class="time-info" v-if="duration">
          {{ formatTime(currentTime) }} / {{ formatTime(duration) }}
        </div>
        <el-switch
          v-model="isLooping"
          active-text="循环播放"
          @change="handleLoopChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  audioSrc: String,
  loading: Boolean
})

const emit = defineEmits(['play', 'pause', 'ended'])

const audioRef = ref(null)
const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const isLooping = ref(true) // 默认开启循环播放

const formatTime = (time) => {
  const minutes = Math.floor(time / 60)
  const seconds = Math.floor(time % 60)
  return `${minutes}:${seconds.toString().padStart(2, '0')}`
}

const handleLoopChange = (val) => {
  if (audioRef.value) {
    audioRef.value.loop = val
  }
}

const togglePlay = async () => {
  if (props.loading || !audioRef.value) return
  
  if (isPlaying.value) {
    audioRef.value.pause()
  } else {
    emit('play')
    if (props.audioSrc) {
      await audioRef.value.play()
    }
  }
}

const handleEnded = () => {
  isPlaying.value = false
  emit('ended')
  // 如果开启了循环播放，自动重新开始
  if (isLooping.value && audioRef.value) {
    audioRef.value.play()
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

// 监听音频时间更新
const updateTime = () => {
  if (audioRef.value) {
    currentTime.value = audioRef.value.currentTime
    duration.value = audioRef.value.duration
  }
}

// 监听音频源变化
watch(() => props.audioSrc, (newSrc) => {
  if (newSrc && audioRef.value) {
    audioRef.value.load()
    audioRef.value.play()
  }
})

// 组件挂载后设置事件监听
onMounted(() => {
  if (audioRef.value) {
    audioRef.value.addEventListener('timeupdate', updateTime)
    audioRef.value.loop = isLooping.value // 设置初始循环状态
  }
})

// 组件卸载前移除事件监听
onUnmounted(() => {
  if (audioRef.value) {
    audioRef.value.removeEventListener('timeupdate', updateTime)
  }
})
</script>

<style scoped>
.audio-player {
  min-width: 300px;
  padding: 10px;
}

.audio-element {
  width: 100%;
  height: 54px;
  margin-bottom: 5px;
  border-radius: 4px;
  outline: none;
}

.player-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 5px;
}

.time-info {
  font-size: 12px;
  color: #909399;
}

.loading-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 54px;
}

/* 自定义音频控件样式 */
.audio-element::-webkit-media-controls-panel {
  background-color: #f5f7fa;
  border-radius: 4px;
}

.audio-element::-webkit-media-controls-play-button {
  background-color: #409EFF;
  border-radius: 50%;
}

.audio-element::-webkit-media-controls-current-time-display,
.audio-element::-webkit-media-controls-time-remaining-display {
  color: #606266;
  font-family: monospace;
}

.audio-element::-webkit-media-controls-timeline {
  background-color: #e4e7ed;
  border-radius: 2px;
  height: 4px;
}

.audio-element::-webkit-media-controls-volume-slider {
  background-color: #e4e7ed;
  border-radius: 2px;
  padding: 0 5px;
}

/* 移除多余的控件按钮 */
.audio-element::-webkit-media-controls-enclosure {
  border-radius: 4px;
}

.audio-element::-webkit-media-controls-mute-button {
  display: none;
}

.audio-element::-webkit-media-controls-volume-slider {
  display: none;
}
</style> 