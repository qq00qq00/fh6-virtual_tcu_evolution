import type { WsInbound, WsOutbound } from '@/types/ws'

export type MessageHandler = (msg: WsInbound) => void

export class TcuWsClient {
  private ws: WebSocket | null = null
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private handler: MessageHandler | null = null
  private url: string

  constructor(url?: string) {
    const proto = location.protocol === 'https:' ? 'wss' : 'ws'
    this.url = url ?? `${proto}://${location.host}/ws`
  }

  onMessage(handler: MessageHandler) {
    this.handler = handler
  }

  connect() {
    if (this.ws?.readyState === WebSocket.OPEN || this.ws?.readyState === WebSocket.CONNECTING)
      return

    this.ws = new WebSocket(this.url)
    this.ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data as string) as WsInbound
        this.handler?.(msg)
      }
      catch {
        /* ignore malformed */
      }
    }
    this.ws.onclose = () => this.scheduleReconnect()
    this.ws.onerror = () => this.ws?.close()
  }

  send(msg: WsOutbound) {
    if (this.ws?.readyState === WebSocket.OPEN)
      this.ws.send(JSON.stringify(msg))
  }

  get connected() {
    return this.ws?.readyState === WebSocket.OPEN
  }

  disconnect() {
    if (this.reconnectTimer)
      clearTimeout(this.reconnectTimer)
    this.reconnectTimer = null
    this.ws?.close()
    this.ws = null
  }

  private scheduleReconnect() {
    if (this.reconnectTimer)
      clearTimeout(this.reconnectTimer)
    this.reconnectTimer = setTimeout(() => this.connect(), 1500)
  }
}
