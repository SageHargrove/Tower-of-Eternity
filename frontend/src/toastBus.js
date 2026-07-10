// Tiny module-level event bus so the API client (a plain module, not a React
// component) can fire reward toasts without needing hook/context access.
const listeners = new Set()

export function subscribeToast(fn) {
  listeners.add(fn)
  return () => listeners.delete(fn)
}

// Two call shapes are supported:
//   emitToast({ title, lines:[{label,value,color}], borderColor })  ← reward toasts
//   emitToast("some message", "success"|"error"|"info")             ← simple notices
// The string form is normalized here so ToastContainer only ever sees objects.
export function emitToast(toast, severity) {
  let normalized = toast
  if (typeof toast === 'string') {
    const borderColor = severity === 'error' ? '#ff6b6b' : severity === 'success' ? '#8fbf9f' : 'var(--gold)'
    normalized = { message: toast, borderColor, severity }
  }
  listeners.forEach(fn => fn(normalized))
}
