import { defineStore } from 'pinia'

export interface ToastNotice {
  id: number
  message: string
  tone: 'info' | 'success' | 'error'
}

export const useUiStore = defineStore('ui', {
  state: () => ({
    notices: [] as ToastNotice[],
    noticeSeed: 1,
  }),
  actions: {
    notify(message: string, tone: ToastNotice['tone'] = 'info') {
      const notice: ToastNotice = {
        id: this.noticeSeed,
        message,
        tone,
      }

      this.noticeSeed += 1
      this.notices.push(notice)

      window.setTimeout(() => {
        this.dismiss(notice.id)
      }, 3600)
    },
    dismiss(id: number) {
      this.notices = this.notices.filter((item) => item.id !== id)
    },
  },
})
