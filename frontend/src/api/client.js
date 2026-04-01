const BASE = '/api'

async function request(path, options = {}) {
  const res = await fetch(BASE + path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Request failed')
  }
  return res.json()
}

// Base
export const getBase = () => request('/base/')
export const restHeroes = () => request('/base/rest', { method: 'POST' })

// Heroes
export const listHeroes = (aliveOnly = false) =>
  request(`/heroes/?alive_only=${aliveOnly}`)
export const getHero = (id) => request(`/heroes/${id}`)
export const setTeam = (heroIds) =>
  request('/heroes/team/set', { method: 'POST', body: JSON.stringify({ hero_ids: heroIds }) })
export const getTeam = () => request('/heroes/team/current')
export const dismissHero = (id) => request(`/heroes/${id}`, { method: 'DELETE' })

// Gacha
export const pullHeroes = (count = 1, usePortrait = false) =>
  request('/gacha/pull', {
    method: 'POST',
    body: JSON.stringify({ count, use_portrait: usePortrait }),
  })
export const getOdds = () => request('/gacha/odds')

// Tower
export const startRun = () => request('/tower/run/start', { method: 'POST' })
export const getActiveRun = () => request('/tower/run/active')
export const advanceFloor = () => request('/tower/run/floor/advance', { method: 'POST' })
export const abandonRun = () => request('/tower/run/abandon', { method: 'POST' })

// Runs / Log
export const listRuns = () => request('/runs/')
export const getEventLog = (runId = null, limit = 50) =>
  request(`/runs/log?${runId ? `run_id=${runId}&` : ''}limit=${limit}`)
