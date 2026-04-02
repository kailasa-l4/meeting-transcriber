import { useEffect } from 'react'

interface ToastProps {
  message: string
  type: 'success' | 'error' | 'info'
  duration?: number
  onClose: () => void
}

export function Toast({ message, type, duration = 3000, onClose }: ToastProps) {
  useEffect(() => {
    const timer = setTimeout(onClose, duration)
    return () => clearTimeout(timer)
  }, [duration, onClose])

  const colors = {
    success: { bg: '#f0fdf4', border: '#86efac', text: '#166534' },
    error: { bg: '#fef2f2', border: '#fca5a5', text: '#991b1b' },
    info: { bg: '#eff6ff', border: '#93c5fd', text: '#1e40af' },
  }
  const c = colors[type]

  return (
    <div style={{
      position: 'fixed', top: 16, right: 16, zIndex: 1000,
      padding: '12px 20px', borderRadius: 8,
      backgroundColor: c.bg, border: `1px solid ${c.border}`, color: c.text,
      boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
      animation: 'slideIn 0.3s ease-out',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span>{message}</span>
        <button onClick={onClose} style={{
          background: 'none', border: 'none', cursor: 'pointer',
          color: c.text, fontSize: 18, lineHeight: 1,
        }}>×</button>
      </div>
    </div>
  )
}
