import axios from 'axios'

const BASE_URL = 'http://localhost:5006'

export const api = {
  async generateContent(formData) {
    const response = await axios.post('http://183.131.7.9:8003/api/application/68b32f0e-64e2-11ef-977b-26cf8447a8c9/content_generate', formData)
    return response.data.data
  },

  async getTTS(text, requestId) {
    try {
      const response = await axios.post(`${BASE_URL}/tts`, {
        text,
        request_id: requestId
      })
      const audioPath = response.data
      return `${BASE_URL}/audio/${audioPath}`
    } catch (error) {
      console.error('TTS请求失败:', error)
      throw error
    }
  },

  async chatStream(question, requestId) {
    try {
      const response = await fetch(`${BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question,
          request_id: requestId
        })
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      return response
    } catch (error) {
      console.error('音频流请求失败:', error)
      throw error
    }
  },

  async killRequest(requestId) {
    try {
      await axios.get(`${BASE_URL}/kill`, {
        params: { request_id: requestId }
      })
    } catch (error) {
      console.error('终止请求失败:', error)
      throw error
    }
  }
} 