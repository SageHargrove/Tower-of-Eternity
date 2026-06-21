import pathlib
p = pathlib.Path('services/portrait_cache.py')
t = p.read_text('utf-8')

t = t.replace(', (Solo Leveling manhwa art style:1.2), dark fantasy anime, highly detailed facial shading, rich saturated colors, sharp dramatic rim lighting, intense contrast, clean sharp lineart, intricate details, masterpiece, best quality, same universe aesthetic', '')
t = t.replace('centered face, head and shoulders portrait, face focused, close up, portrait, fully clothed, wearing detailed outfit', 'upper body')
t = t.replace('gritty realistic', '')
p.write_text(t, 'utf-8')
print('Tags fixed in portrait_cache.py')
