const BASE = '/api'

async function request(path, options = {}) {
  const isGet = !options.method || options.method === 'GET'
  const url = isGet ? BASE + path + (path.includes('?') ? '&' : '?') + 't=' + Date.now() : BASE + path
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    cache: 'no-store',
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    let msg = err.detail || err.error || 'Request failed'
    if (typeof msg === 'object') msg = JSON.stringify(msg)
    throw new Error(msg)
  }
  return res.json()
}

export const getChatLogs = (limit = 10) => request(`/chat/?limit=${limit}`)
export const egoAutoTeam = (teamId, egoHeroId) => request('/heroes/team/ego_auto', { method: 'POST', body: JSON.stringify({ team_id: teamId, ego_hero_id: egoHeroId }) })

// Base
export const getBase = () => request('/base/')
export const restHeroes = () => request('/base/rest', { method: 'POST' })
export const runDailyDungeon = (type) => request(`/base/daily_dungeon/${type}`, { method: 'POST' })
export const getBaseFloors = () => request('/base/floors')
export const assignBaseFloor = (heroId, floor) => request('/base/floors/assign', { method: 'POST', body: JSON.stringify({ hero_id: heroId, floor }) })

export const getFacilities = () => request('/base/facilities')
export const buildFacility = (type) => request('/base/facilities/build', { method: 'POST', body: JSON.stringify({ facility_type: type }) })
export const assignFacility = (facId, heroId) => request('/base/facilities/assign', { method: 'POST', body: JSON.stringify({ facility_id: facId, hero_id: heroId }) })
export const removeFacility = (heroId) => request('/base/facilities/remove', { method: 'POST', body: JSON.stringify({ hero_id: heroId }) })
export const upgradeFacility = (facilityId) => request('/base/facilities/upgrade', { method: 'POST', body: JSON.stringify({ facility_id: facilityId }) })
export const configTraining = (facilityId, heroId, role, targetSkillId, targetHeroId) => request('/base/facilities/training-config', { method: 'POST', body: JSON.stringify({ facility_id: facilityId, hero_id: heroId, role, target_skill_id: targetSkillId, target_hero_id: targetHeroId }) })
export const getMageTowerUpgrades = () => request('/base/facilities/mage-tower/upgrades')
export const buyResearchUpgrade = (upgradeId) => request('/base/facilities/mage-tower/buy', { method: 'POST', body: JSON.stringify({ upgrade_id: upgradeId }) })

export const listUpgrades = () => request('/base/upgrades')
export const purchaseUpgrade = (facilityId) => request('/base/upgrades/purchase', { method: 'POST', body: JSON.stringify({ upgrade_id: facilityId }) })
export const getInventory = () => request('/base/inventory')

// Heroes
export const listHeroes = (aliveOnly = false) => request(`/heroes/?alive_only=${aliveOnly}`)
export const getHero = (id) => request(`/heroes/${id}`)
export const setTeam = (teamId, heroIds) => request('/heroes/team/set', { method: 'POST', body: JSON.stringify({ team_id: teamId, hero_ids: heroIds }) })
export const getTeam = (teamId = 1) => request(`/heroes/team/${teamId}`)
export const getAllTeams = () => request('/heroes/teams/all')
export const dismissHero = (id) => request(`/heroes/${id}`, { method: 'DELETE' })
export const dismissHeroesBulk = (heroIds) => request('/heroes/dismiss-bulk', { method: 'POST', body: JSON.stringify({ hero_ids: heroIds }) })
export const synthesizeHero = (targetId, sacrificeId) => request('/heroes/synthesize', { method: 'POST', body: JSON.stringify({ target_id: targetId, sacrifice_id: sacrificeId }) })
export const ascendHero = (heroId) => request(`/heroes/${heroId}/ascend`, { method: 'POST' })
export const promoteHero = (heroId) => request(`/heroes/${heroId}/promote`, { method: 'POST' })
export const evolveHero = (heroId, targetClass) => request(`/heroes/${heroId}/evolve`, { method: 'POST', body: JSON.stringify({ target_class: targetClass }) })
export const getClassEvolutions = () => request('/heroes/classes/evolutions')
export const getLegacies = () => request('/heroes/legacies')
export const regenerateProfile = (heroId) => request(`/heroes/${heroId}/regenerate-profile`, { method: 'POST' })
export const getHeroAptitudes = (heroId) => request(`/heroes/${heroId}/aptitudes`)
export const getBonds = () => request('/heroes/bonds')

// Equipment
export const listEquipment = () => request('/equipment/')
export const craftEquipment = (crafterId) => request('/equipment/craft', { method: 'POST', body: JSON.stringify({ crafter_id: crafterId }) })
export const equipItem = (equipmentId, heroId) => request('/equipment/equip', { method: 'POST', body: JSON.stringify({ equipment_id: equipmentId, hero_id: heroId }) })
export const unequipItem = (equipmentId) => request('/equipment/unequip', { method: 'POST', body: JSON.stringify({ equipment_id: equipmentId }) })

// Gacha
export const pullHeroes = (count = 1, usePortrait = false) => request('/gacha/pull', { method: 'POST', body: JSON.stringify({ count, use_portrait: usePortrait }) })
export const getOdds = () => request('/gacha/odds')
export const getPityInfo = () => request('/gacha/pity-info')
export const redeemSpark = () => request('/gacha/spark-redeem', { method: 'POST' })

// Tower / Runs
export const enterFloor = (floorNumber, teamId) => request('/tower/floor/enter', { method: 'POST', body: JSON.stringify({ floor_number: floorNumber, team_id: teamId }) })
export const resolveEvent = (floorNumber, teamId, templateId, choiceId, theme) => request('/tower/floor/event/resolve', { method: 'POST', body: JSON.stringify({ floor_number: floorNumber, team_id: teamId, template_id: templateId, choice_id: choiceId, theme: theme }) })
export const listRuns = () => request('/runs/')
export const getEventLog = (runId = null, limit = 50) => request(`/runs/log?${runId ? `run_id=${runId}&` : ''}limit=${limit}`)

// Profiles
export const listProfiles = () => request('/profiles/')
export const switchProfile = (name) => request('/profiles/switch', { method: 'POST', body: JSON.stringify({ name }) })
export const renameProfile = (oldName, newName) => request('/profiles/rename', { method: 'POST', body: JSON.stringify({ old_name: oldName, new_name: newName }) })
export const deleteProfile = (name) => request('/profiles/delete', { method: 'POST', body: JSON.stringify({ name }) })

// Portrait Cache
export const regeneratePortraits = () => request('/portrait-cache/regenerate', { method: 'POST' })
export const cleanupPortraits = () => request('/portrait-cache/cleanup', { method: 'POST' })
export const getCacheStatus = () => request('/portrait-cache/status')

export const craftMaterialEquipment = (heroId, slot) => request('/base/forge/craft', { method: 'POST', body: JSON.stringify({ hero_id: heroId, slot }) })
