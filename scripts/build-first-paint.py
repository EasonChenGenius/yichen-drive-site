"""Refresh the committed static shell and shared CSS after editing their source files."""
from pathlib import Path
import re,sys,json
root=Path(__file__).resolve().parents[1]/'dist'
p=root/'index.html';s=p.read_text()
names=['regional','tour','brand','home','service','business']
css='\n'.join('/* '+name+'.css */\n'+(root/(name+'.css')).read_text() for name in names)
updated=re.sub(r'<!-- BEGIN GENERATED FIRST PAINT CSS -->.*?<!-- END GENERATED FIRST PAINT CSS -->',lambda _: '<!-- BEGIN GENERATED FIRST PAINT CSS -->\n<style>\n'+css+'\n.page{animation:none}\n</style>\n<!-- END GENERATED FIRST PAINT CSS -->',s,flags=re.S)
updated=re.sub(r'<div id="app" data-first-paint>.*?</main>\s*</div>',lambda _: '<div id="app" data-first-paint>'+ (root/'home-shell.html').read_text()+'</div>',updated,flags=re.S)
updated=re.sub(r'<template id="enquiry-first-paint">.*?</template>',lambda _: '<template id="enquiry-first-paint">'+(root/'enquiry-shell.html').read_text()+'</template>',updated,flags=re.S)
if '--check' in sys.argv:
 if updated!=s:raise SystemExit('Run python scripts/build-first-paint.py to refresh published sources')
else:p.write_text(updated)

sources=json.loads((root.parent/'scripts/first-paint-sources.json').read_text())
bundle='/* Generated from scripts/first-paint-sources.json. Edit source files, then rebuild. */\n'+'\n;\n'.join('/* '+src+' */\n'+(root/src.split('?')[0].removeprefix('./')).read_text() for src in sources)+'\n'
bundle=bundle.rstrip()+'\n'
output=root/'application-v56.js'
if '--check' in sys.argv:
 if not output.exists() or output.read_text()!=bundle:raise SystemExit('Refresh application bundle')
else:output.write_text(bundle)
