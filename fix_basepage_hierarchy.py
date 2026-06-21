with open('frontend/src/pages/BasePage.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace Unassigned Heroes grid minmax
content = content.replace("gridTemplateColumns: 'repeat(auto-fill, minmax(60px, 1fr))'", "gridTemplateColumns: 'repeat(auto-fill, minmax(100px, 1fr))'")

# Replace image sizes from 60 to 100 in unassigned and assigned heroes
content = content.replace("width: 60, height: 60", "width: 100, height: 100")

# Render name and class under Unassigned heroes
old_unassigned_img = """<img src={`http://localhost:8000/${h.portrait_path}`} alt={h.name} style={{ width: 100, height: 100, borderRadius: '50%', objectFit: 'cover', border: '1px solid var(--border)' }} title={`${h.name} (Lv ${h.level} ${h.hero_class})`} />"""
new_unassigned_img = """<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                      <img src={`http://localhost:8000/${h.portrait_path}`} alt={h.name} style={{ width: 100, height: 100, borderRadius: '50%', objectFit: 'cover', border: '1px solid var(--border)' }} title={`${h.name} (Lv ${h.level} ${h.hero_class})`} />
                      <div className="text-hi" style={{ fontSize: '0.8rem', marginTop: '0.3rem', textAlign: 'center' }}>{h.name}</div>
                      <div className="text-dim" style={{ fontSize: '0.7rem', textAlign: 'center' }}>{h.hero_class}</div>
                    </div>"""
content = content.replace(old_unassigned_img, new_unassigned_img)

# Render name and class under Assigned heroes
old_assigned_img = """<img src={`http://localhost:8000/${h.portrait_path}`} alt={h.name} style={{ width: 100, height: 100, borderRadius: '50%', objectFit: 'cover', border: '1px solid var(--border)' }} />"""
new_assigned_img = """<div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                            <img src={`http://localhost:8000/${h.portrait_path}`} alt={h.name} style={{ width: 100, height: 100, borderRadius: '50%', objectFit: 'cover', border: '1px solid var(--border)' }} />
                            <div className="text-hi" style={{ fontSize: '0.8rem', marginTop: '0.3rem', textAlign: 'center' }}>{h.name}</div>
                          </div>"""
content = content.replace(old_assigned_img, new_assigned_img)

with open('frontend/src/pages/BasePage.jsx', 'w', encoding='utf-8') as f:
    f.write(content)
