import { useState, useEffect, useCallback } from 'react'

interface KeyboardNavOptions {
  items: string[]  // IDs of items to navigate
  onSelect?: (id: string) => void
  onAction?: (id: string, key: string) => void
  enabled?: boolean
}

export function useKeyboardNav({ items, onSelect, onAction, enabled = true }: KeyboardNavOptions) {
  const [selectedIndex, setSelectedIndex] = useState(0)

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (!enabled || items.length === 0) return

    switch (e.key) {
      case 'j':
      case 'ArrowDown':
        e.preventDefault()
        setSelectedIndex(prev => Math.min(prev + 1, items.length - 1))
        break
      case 'k':
      case 'ArrowUp':
        e.preventDefault()
        setSelectedIndex(prev => Math.max(prev - 1, 0))
        break
      case 'Enter':
        e.preventDefault()
        onSelect?.(items[selectedIndex])
        break
      case 'a':
        if (!e.ctrlKey && !e.metaKey) {
          e.preventDefault()
          onAction?.(items[selectedIndex], 'approve')
        }
        break
      case 'r':
        if (!e.ctrlKey && !e.metaKey) {
          e.preventDefault()
          onAction?.(items[selectedIndex], 'request_changes')
        }
        break
      case 'Escape':
        e.preventDefault()
        onAction?.(items[selectedIndex], 'escape')
        break
    }
  }, [enabled, items, selectedIndex, onSelect, onAction])

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [handleKeyDown])

  return { selectedIndex, setSelectedIndex }
}
