from pathlib import Path
import pypdfium2 as pdfium
from pypdf import PdfReader
from PIL import Image,ImageOps,ImageDraw
P=Path(__file__).resolve().parent;out=P/'audit'/'revision-2026-10-26';out.mkdir(parents=True,exist_ok=True)
pdf=pdfium.PdfDocument(str(P/'build/regional_alarm.pdf'));reader=PdfReader(P/'build/regional_alarm.pdf')
for stale in out.glob('page-*.png'):
 if int(stale.stem.split('-')[-1])>len(pdf):stale.unlink()
texts=[];thumbs=[]
for i in range(len(pdf)):
 page=pdf[i];im=page.render(scale=1.35).to_pil().convert('RGB');im.save(out/f'page-{i+1:02}.png');texts.append(reader.pages[i].extract_text())
 thumb=im.copy();thumb.thumbnail((345,485));canvas=Image.new('RGB',(365,515),'#dedede');canvas.paste(thumb,((365-thumb.width)//2,20));ImageDraw.Draw(canvas).text((12,497),f'Page {i+1}',fill='black');thumbs.append(canvas)
for start in range(0,len(thumbs),6):
 group=thumbs[start:start+6];sheet=Image.new('RGB',(365*3,515*2),'white')
 for j,im in enumerate(group):sheet.paste(im,((j%3)*365,(j//3)*515))
 sheet.save(out/f'contact-{start//6+1}.png')
(out/'text.txt').write_text('\n\n'.join(texts));print('Rendered',len(pdf),'pages',out)
