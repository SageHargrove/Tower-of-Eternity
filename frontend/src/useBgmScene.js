import { useEffect } from 'react'
import { setBgmScene } from './audio'

// Mount a screen/panel and route BGM to `scene` while it's open; on unmount,
// revert to `revertTo` (default the Base hub). Same-scene calls are no-ops in
// the manager, and App.jsx re-asserts the tab scene on navigation, so this is
// safe to sprinkle on any dedicated-music panel.
export function useBgmScene(scene, revertTo = 'hub') {
  useEffect(() => {
    setBgmScene(scene)
    return () => setBgmScene(revertTo)
  }, [scene, revertTo])
}
