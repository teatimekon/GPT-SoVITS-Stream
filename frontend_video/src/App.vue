<template>
  <el-container class="app-container">
    <el-header class="app-header">
      <h1>数字人直播</h1>
    </el-header>

    <el-container class="main-container">
      <el-aside width="500px" class="fixed-aside">
        <goods-form @content-generated="handleContentGenerated" />
      </el-aside>

      <el-main class="fixed-main">
        <el-card class="content-card">
          <template #header>
            <div class="card-header">
              <span>生成的口播文本</span>
              <el-button v-if="generatedContent && !audioChunks.length" type="primary" @click="generateVideo"
                :loading="isLoading" class="generate-btn">
                生成视频
              </el-button>
            </div>
          </template>

          <div class="content" v-if="generatedContent">
            <div class="content-text">
              <div v-for="(chunk, index) in generatedContent" :key="index"
                :class="['content-chunk', { 'active': currentAudioIndex === index }]">
                {{ chunk.content }}
              </div>
            </div>
            <div v-if="audioChunks.length" class="audio-section">
              <audio-player ref="audioPlayerRef" :playlist="audioChunks" :loading="isLoading"
                :should-play-next="shouldPlayNext" v-model="currentAudioIndex" @play="handlePlay" @pause="handlePause"
                @chunkEnd="handleChunkEnd" @chunkStart="handleChunkStart" @update-playlist="updatePlaylist"/>
            </div>
          </div>
          <el-empty v-else description="暂无内容" />
        </el-card>

        <!-- <el-card class="stream-card">
          <template #header>
            <div class="card-header">
              <span>实时音频流</span>
            </div>
          </template>
          <streaming-audio ref="streamingAudioRef" :continuity-sentences="audioChunksWithSentences"
            :checkCanPlay="checkCanPlay" @stream-start="handleStreamStart" @stream-end="handleStreamEnd" />
        </el-card> -->

        <!-- <el-card class="video-card">
          <template #header>
            <div class="card-header">
              <span>生成视频</span>
            </div>
          </template>
          <el-button type="primary" @click="generateVideo" :loading="isLoading" class="generate-btn">
            生成视频
          </el-button>
          <video v-if="videoUrl" :src="videoUrl" controls></video>

        </el-card>  -->

        <el-card class="live-card">
          <template #header>
            <div class="card-header">
              <span>直播控制</span>
            </div>
          </template>
          <el-button type="success" @click="startLive" :disabled="jobId !== ''">开始获取弹幕</el-button>
          <el-button type="danger" @click="stopLive" :disabled="jobId == ''">停止获取弹幕</el-button>
        </el-card>

        <el-card class="live-data-card">
          <template #header>
            <div class="card-header">
              <span>直播数据</span>
            </div>
          </template>
          <h4>回答</h4>
          <p>{{ answers }}</p>

          <h4>挑选弹幕</h4>
          <p>{{ chooseComments }}</p>

          <h4>所有弹幕</h4>
          <p>{{ comments }}</p>

          <h4>脚本id</h4>
          <p>{{ jobId }}</p>
        </el-card>
        <el-card class="config-card">
          <template #header>
            <div class="card-header">
              <span>直播配置</span>
            </div>
          </template>
          <el-form label-width="100px">
            <el-form-item label="商品信息">
              <el-input v-model="goodsInfo"></el-input>
            </el-form-item>
            <el-form-item label="弹幕选择数量">
              <el-input-number v-model="chooseNum" :min="1"></el-input-number>
            </el-form-item>
            <el-form-item label="脚本间隔 (秒)">
              <el-input-number v-model="interval" :min="1"></el-input-number>
            </el-form-item>
            <el-form-item label="获取弹幕间隔 (毫秒)">
              <el-input-number v-model="fetchDataInterval" :min="1000"></el-input-number>
            </el-form-item>
            <el-form-item label="直播房间id">
              <el-input v-model="roomId"></el-input>
            </el-form-item>
            <el-form-item label="回答风格">
              <el-select v-model="style" placeholder="请选择回答风格">
                <el-option label="正常风格" value="1"></el-option>
                <el-option label="董宇辉" value="2"></el-option>
                <el-option label="李佳琦" value="3"></el-option>
              </el-select>
            </el-form-item>
          </el-form>
        </el-card>
      </el-main>
    </el-container>

    <!-- 上传图片部分 -->
    <el-card class="upload-card">
      <template #header>
        <div class="card-header">
          <span>上传图片</span>
        </div>
      </template>
      <input type="file" @change="handleImageFileChange" accept=".jpg,.jpeg,.png">
      <el-button type="primary" @click="uploadImageManually">上传图片</el-button>
    </el-card>

    <!-- 上传音频部分 -->
    <el-card class="upload-card">
      <template #header>
        <div class="card-header">
          <span>上传音频</span>
        </div>
      </template>
      <input type="file" @change="handleAudioFileChange" accept=".mp3,.wav">
      <el-button type="primary" @click="uploadAudioManually">上传音频</el-button>
    </el-card>
  </el-container>
</template>

<script setup>
import { ref, watch, onBeforeUnmount, onMounted } from 'vue'
import { v4 as uuidv4 } from 'uuid'
import { ElMessage } from 'element-plus'
import GoodsForm from './components/GoodsForm.vue'
import StreamingAudio from './components/StreamingAudio.vue'
import AudioPlayer from './components/AudioPlayer.vue'
import { api } from './services/api'

const generatedContent = ref('')
const audioChunks = ref([])
const audioChunksWithSentences = ref([])

const isPlaying = ref(false)
const isLoading = ref(false)

const currentContentRequestId = ref('')
const audioPlayerRef = ref(null)
const streamingAudioRef = ref(null)
const shouldPlayNext = ref(true)
const canStreamPlay = ref(true)
const currentAudioIndex = ref(0)
const videoUrl = ref('');
const imageUrl = ref('');
const audioUrl = ref('');
const imageFile = ref(null);
const audioFile = ref(null);
const jobId = ref('');
const answers = ref('');
const chooseComments = ref('');
const comments = ref('');
const goodsInfo = ref('女士拖鞋舒适鞋日常步行');
const chooseNum = ref(1);
const interval = ref(10);
const fetchDataInterval = ref(20000); // 默认10秒
const pgJobId = ref('');
const roomId = ref('1752664819');
const style = ref("1");
const timeoutId = ref(null);
let fetchLiveDataInterval = ref(null);


const handleContentGenerated = (content) => {
  generatedContent.value = content.content
  audioChunks.value = []
}


const generateVideo = async () => {
  try {
    isLoading.value = true
    currentContentRequestId.value = uuidv4()

    // 获取音频结果
    const audioPromises = generatedContent.value.map(async chunk => {
      // 获取主要内容的音频
      const contentAudio = await api.getVideo(
        chunk.content,
        currentContentRequestId.value + 'content',
        chunk.rank
      )

      // 获取连续性话语的音频
      const continuityAudio = await api.getVideo(
        chunk.continuity_sentences,
        currentContentRequestId.value + 'continuity',
        chunk.rank
      )
      canStreamPlay.value = false
      return {
        content: contentAudio,
        continuity_sentences: continuityAudio,
        rank: chunk.rank
      }
    })

    const results = await Promise.all(audioPromises)
    audioChunks.value = results.sort((a, b) => a.rank - b.rank)
    console.log('audioChunks', audioChunks.value)
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

const handleQAStart = () => {
  if (audioPlayerRef.value) {
    console.log('开始回答弹幕问题', audioPlayerRef.value)
    shouldPlayNext.value = false
  }
}

const handleQAEnd = () => {
  console.log('回答弹幕问题结束,handleQAEnd', audioPlayerRef.value)

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

// 处理图片上传成功
const handleImageUploadSuccess = async (response) => {
  imageUrl.value = response.image_path
}

// 验证图片上传
const beforeImageUpload = (file) => {
  const isImage = file.type === 'image/jpeg' || file.type === 'image/png'
  if (!isImage) {
    ElMessage.error('只能上传JPEG或PNG格式的图片文件!')
  }
  return isImage
}

// 手动上传图片
const uploadImageManually = async () => {
  if (!imageFile.value) {
    ElMessage.error('请选择一个图片文件')
    return
  }

  const formData = new FormData()
  formData.append('image', imageFile.value)

  try {
    const response = await api.uploadImage(formData)
    handleImageUploadSuccess(response)
  } catch (error) {
    ElMessage.error('上传图片失败')
  }
}

// 处理音频上传成功
const handleAudioUploadSuccess = (response) => {
  audioUrl.value = response.audio_path
}

// 验证音频上传
const beforeAudioUpload = (file) => {
  const isAudio = file.type === 'audio/mpeg' || file.type === 'audio/wav'
  if (!isAudio) {
    ElMessage.error('只能上传MP3或WAV格式的音频文件!')
  }
  return isAudio
}

// 手动上传音频
const uploadAudioManually = async () => {
  if (!audioFile.value) {
    ElMessage.error('请选择一个音频文件')
    return
  }

  const formData = new FormData()
  formData.append('audio', audioFile.value)

  try {
    const response = await api.uploadAudio(formData)
    handleAudioUploadSuccess(response)
  } catch (error) {
    ElMessage.error('上传音频失败')
  }
}

// 处理图片文件变化
const handleImageFileChange = (event) => {
  const file = event.target.files[0]
  if (beforeImageUpload(file)) {
    imageFile.value = file
  }
}

// 处理音频文件变化
const handleAudioFileChange = (event) => {
  const file = event.target.files[0]
  if (beforeAudioUpload(file)) {
    audioFile.value = file
  }
}

const updatePlaylist = (index,newValue) => {
  console.log('调用了updatePlaylist', index,newValue)
  audioChunks.value = [
    ...audioChunks.value.slice(0, index),
    newValue,
    ...audioChunks.value.slice(index + 1)
  ]
}

const fetchLiveData = async () => {
  try {
    const formData = new FormData();
    formData.append('job_id', pgJobId.value);
    const response = await api.getResultById(formData);
    
    if (response.status === "empty") {
      ElMessage.info('队列中暂无数据');
      return;
    }

    // 如果有新的回答音频
    if (response.video_url ) {
       console.log('有新的回答音频')
        handleQAStart()  //将 shouldPlayNext 设置为 false
        await checkCanPlay()
        console.log('现在能播放了 response.video_url', response.video_url)
        await audioPlayerRef.value.playQA(response.video_url)
        handleQAEnd()  //将 shouldPlayNext 设置为 true
    }

    answers.value = response.answers;
    chooseComments.value = response.choose_comments;
    comments.value = response.comments;
  } catch (error) {
    console.error('获取直播数据失败:', error);
  }
};
const startLive = async () => {
  if (!goodsInfo.value || !chooseNum.value || !interval.value) {
    ElMessage.error('请填写所有配置项');
    return;
  }

  const formData = new FormData();
  formData.append('goods_info', goodsInfo.value);
  formData.append('choose_num', chooseNum.value);
  formData.append('interval', interval.value);
  formData.append('room_id', roomId.value)
  formData.append('style', style.value)
  
  const response = await api.startPeriodicTask(formData);
  jobId.value = response.job_id;
  pgJobId.value = response.pg_job_id;
  ElMessage.success('直播已开始');

  // 清除可能存在的旧定时器
  if (timeoutId.value) {
    clearTimeout(timeoutId.value);
  }

  // 定义并启动递归的轮询函数
  const scheduleFetch = async () => {
    try {
      await fetchLiveData();
      // 只有当 jobId 还存在(即直播未停止)时才继续轮询
      if (jobId.value) {
        timeoutId.value = setTimeout(scheduleFetch, fetchDataInterval.value);
      }
    } catch (error) {
      console.error('轮询出错:', error);
      // 出错时也继续轮询
      if (jobId.value) {
        timeoutId.value = setTimeout(scheduleFetch, fetchDataInterval.value);
      }
    }
  };

  // 启动轮询
  scheduleFetch();
};
const stopLive = async () => {
  if (!jobId.value) {
    ElMessage.error('没有正在运行的直播任务');
    return;
  }

  const formData = new FormData();
  formData.append('job_id', jobId.value);
  await api.stopPeriodicTask(formData);

  // 清除定时器
  if (timeoutId.value) {
    clearTimeout(timeoutId.value);
    timeoutId.value = null;
  }

  jobId.value = '';
  pgJobId.value = '';
  answers.value = '';
  chooseComments.value = '';
  comments.value = '';
  roomId.value = '1752664819';
  ElMessage.success('直播已停止');
};

// 添加 beforeunload 处理函数
const handleBeforeUnload = async () => {
  if (jobId.value) {
    await stopLive()
  }
}

// 添加生命周期钩子
onMounted(() => {
  window.addEventListener('beforeunload', handleBeforeUnload)
})

onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', handleBeforeUnload)
  if (jobId.value) {
    stopLive()
  }
})

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
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
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
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.2);
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
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
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

.video-card video {
  width: 100%;
  max-width: 100%;
  height: auto;
}

.content-chunk {
  padding: 12px;
  margin: 8px 0;
  border-radius: 8px;
  background-color: #f5f7fa;
  transition: all 0.3s ease;
}

.content-chunk.active {
  background-color: #ecf5ff;
  border-left: 4px solid #409EFF;
  transform: translateX(4px);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}
</style>