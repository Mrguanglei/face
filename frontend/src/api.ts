import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 0  // 不超时，处理大视频可能要好几分钟
})

export async function uploadTarget(file: File) {
  const form = new FormData()
  form.append('file', file)
  const res = await api.post('/upload/target', form, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return res.data
}

export async function uploadSource(file: File) {
  const form = new FormData()
  form.append('file', file)
  const res = await api.post('/upload/source', form, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return res.data
}

export async function detectFaces() {
  const res = await api.post('/detect-faces')
  return res.data
}

export async function setSourceMap(map: Record<number, string>) {
  const res = await api.post('/set-source-map', { map })
  return res.data
}

export async function getProcessorOptions() {
  const res = await api.get('/processor-options')
  return res.data
}

export async function startSwap(processors: string[], processorOptions: Record<string, any>) {
  const res = await api.post('/start-swap', { processors, processor_options: processorOptions })
  return res.data
}
