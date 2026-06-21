import { createServer } from 'vite'
import React from 'react'
import ReactDOMServer from 'react-dom/server'

async function run() {
  const server = await createServer({
    server: { middlewareMode: true },
    appType: 'custom'
  })
  
  try {
    const InventoryPageMod = await server.ssrLoadModule('/src/pages/InventoryPage.jsx')
    const InventoryPage = InventoryPageMod.default
    const html = ReactDOMServer.renderToString(React.createElement(InventoryPage))
    console.log("INVENTORY SUCCESS")
  } catch (e) {
    console.error("INVENTORY ERROR:", e)
  }

  try {
    const HeroesPageMod = await server.ssrLoadModule('/src/pages/HeroesPage.jsx')
    const HeroesPage = HeroesPageMod.default
    const html2 = ReactDOMServer.renderToString(React.createElement(HeroesPage))
    console.log("HEROES SUCCESS")
  } catch (e) {
    console.error("HEROES ERROR:", e)
  }

  await server.close()
}

run()
