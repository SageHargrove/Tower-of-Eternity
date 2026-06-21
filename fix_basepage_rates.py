import re

with open('frontend/src/pages/BasePage.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Add getGenRate helper
gen_helper = """
  const getGenRate = (fac) => {
    if (fac.type !== 'The Market' && fac.type !== 'The Farm') return null;
    let base_amt = 50 * fac.level;
    let multiplier = 1.0 + ((fac.heroes || []).length * 0.10);
    let amt = Math.floor(base_amt * multiplier);
    let resName = fac.type === 'The Market' ? 'Gold' : 'Supplies';
    return `Generating: ${amt} ${resName} / 5 mins`;
  };

  return (
"""
content = content.replace("  return (\n", gen_helper)

# Add the generation rate text below the title
old_title_div = """<h3 style={{ fontFamily: 'Cinzel, serif', color: 'var(--gold)', margin: 0 }}>{fac.type} \n(Lv.{fac.level})</h3>\n                      <span title={FACILITY_TOOLTIPS[fac.type] || "Base facility."} style={{ fontSize: '0.8rem', \ncolor: 'var(--gold)', cursor: 'help' }}>[?]</span>\n                    </div>\n                    {fac.level < fac.max_level && ("""
# The formatting of the output string makes it easier to replace using regex.
pattern = r"<div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>\s*<h3.*?</h3>\s*<span.*?</span>\s*</div>"
replacement = """<div style={{ display: 'flex', flexDirection: 'column' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <h3 style={{ fontFamily: 'Cinzel, serif', color: 'var(--gold)', margin: 0 }}>{fac.type} (Lv.{fac.level})</h3>
                        <span title={FACILITY_TOOLTIPS[fac.type] || "Base facility."} style={{ fontSize: '0.8rem', color: 'var(--gold)', cursor: 'help' }}>[?]</span>
                      </div>
                      {getGenRate(fac) && (
                        <div style={{ fontSize: '0.9rem', color: 'var(--star2)', marginTop: '0.2rem', fontFamily: 'Cinzel, serif' }}>
                          {getGenRate(fac)}
                        </div>
                      )}
                    </div>"""

content = re.sub(pattern, replacement, content)

with open('frontend/src/pages/BasePage.jsx', 'w', encoding='utf-8') as f:
    f.write(content)
