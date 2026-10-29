"""Figure 1 (the mine in three dimensions) and Figure 2 (plan view with the quadrant zones)."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from mpl_toolkits.mplot3d.art3d import Line3DCollection,Poly3DCollection
from matplotlib.colors import Normalize
from matplotlib.patches import Rectangle
ROOT=Path(__file__).resolve().parents[1];P=Path(__file__).resolve().parent;F=P/'figures'
D=json.loads((ROOT/'实验_07_分区预警与固定路线_全分区分析'/'design.json').read_text())
XYZ={k:np.array(v,float) for k,v in D['nodes'].items()};EDGES=[(a,b,L) for a,b,L in D['arcs'] if a<b]
SHAFT='#b22222';EXAG=60.
ZC=np.array([(XYZ[a][2]+XYZ[b][2])/2 for a,b,L in EDGES]);NORM=Normalize(ZC.min(),ZC.max())
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'pdf.fonttype':42})

def three_d():
 """Thin tunnel lines in an ordinary 3D axis box with a strong vertical exaggeration, so that tunnels at
 different heights separate; a light shadow on the box floor and the four shafts as red columns."""
 zf,zt=10.,125.;az,el=-65,28
 fig=plt.figure(figsize=(9.4,6.6));ax=fig.add_axes([0,0,1,1],projection='3d')
 segs=[np.array([XYZ[a],XYZ[b]])*[1/1000,1/1000,1] for a,b,L in EDGES]
 ax.add_collection3d(Line3DCollection([[[s[0,0],s[0,1],zf],[s[1,0],s[1,1],zf]] for s in segs],colors='#d6d6d6',linewidths=.6))
 ax.add_collection3d(Line3DCollection(segs,colors='#1f3a5a',linewidths=1.25))
 for e in D['exits']:
  p=XYZ[e];ax.plot([p[0]/1000]*2,[p[1]/1000]*2,[p[2],zt],c=SHAFT,lw=3.2,solid_capstyle='butt')
 ax.set_xlim(0,10);ax.set_ylim(0,10);ax.set_zlim(zf,zt);ax.set_box_aspect([10,10,(zt-zf)*EXAG/1000],zoom=.9);ax.view_init(el,az)
 ax.set_xlabel('x (km)',labelpad=2);ax.set_ylabel('y (km)',labelpad=2);ax.set_zlabel('floor elevation (m, relative)',labelpad=6)
 ax.tick_params(labelsize=8.5,pad=1)
 for axis in [ax.xaxis,ax.yaxis,ax.zaxis]:axis.pane.set_facecolor((.97,.97,.97,1));axis._axinfo['grid'].update(color='#e2e2e2',linewidth=.6)
 # Labels in screen space, each tied to a real point by a leader line.
 from mpl_toolkits.mplot3d import proj3d
 fig.canvas.draw();M=ax.get_proj()
 def label(pt,text,off,**kw):
  x,y,_=proj3d.proj_transform(pt[0]/1000,pt[1]/1000,pt[2],M)
  ax.annotate(text,(x,y),xytext=off,textcoords='offset points',fontsize=10,arrowprops=dict(arrowstyle='-',lw=.7,color=kw.get('color','#444')),**kw)
 sh=XYZ['P0986'];hi=max(XYZ.values(),key=lambda v:v[2]);ne=max(XYZ.values(),key=lambda v:v[0]+v[1])
 road=min(XYZ.values(),key=lambda v:(v[0]-7400)**2+(v[1]-6900)**2)
 label((sh[0],sh[1],zt-6),'4 shafts (to the surface;\nheight not to scale)',(55,18),color=SHAFT)
 label(hi,'longwall panels,\nhighest in the west',(-70,40))
 label(road,'main roadway',(-20,75))
 label(ne,'lowest point\n(far northeast)',(-95,-85))
 # Crop to the drawn content: a tight bounding box would include the empty part of the 3D axes.
 import io
 from PIL import Image,ImageOps
 from matplotlib.transforms import Bbox
 buf=io.BytesIO();dpi=100;fig.savefig(buf,format='png',dpi=dpi);buf.seek(0);im=Image.open(buf).convert('L')
 x0,y0,x1,y1=ImageOps.invert(im).point(lambda v:255 if v>8 else 0).getbbox();W,H=fig.get_size_inches();pad=.08
 box=Bbox([[x0/dpi-pad,H-y1/dpi-pad],[x1/dpi+pad,H-y0/dpi+pad]])
 fig.savefig(F/'geometry3d.pdf',bbox_inches=box);fig.savefig(F/'geometry3d.png',dpi=170,bbox_inches=box);plt.close(fig)

def plan():
 """Plan view with the quadrant zones; an inset enlarges the shaft area."""
 fig,bx=plt.subplots(figsize=(6.2,5.6));segs=[[XYZ[a][:2]/1000,XYZ[b][:2]/1000] for a,b,L in EDGES]
 bx.add_collection(LineCollection(segs,colors='#3d5670',linewidths=1.1))
 mx,my=np.array(D['median_xy'])/1000;bx.axvline(mx,c='#555',ls='--',lw=.8);bx.axhline(my,c='#555',ls='--',lw=.8)
 for name,x,y in [('NW',.6,8.9),('NE',8.7,8.9),('SW',.6,3.0),('SE',8.7,.6)]:bx.text(x,y,name,fontsize=12,color='#444',fontweight='bold')
 ex=np.array([XYZ[e][:2]/1000 for e in D['exits']]);bx.scatter(ex[:,0],ex[:,1],marker='s',s=28,c=SHAFT,zorder=5)
 bx.annotate('main roadway',(7.6,7.0),xytext=(8.3,5.8),fontsize=9.5,arrowprops=dict(arrowstyle='-',lw=.6,color='#555'),ha='center')
 bx.annotate('longwall panels',(2.0,4.6),xytext=(1.0,7.5),fontsize=9.5,arrowprops=dict(arrowstyle='-',lw=.6,color='#555'))
 bx.set_xlim(.3,9.8);bx.set_ylim(.3,9.6);bx.set_aspect('equal');bx.set_xlabel('x (km)');bx.set_ylabel('y (km)')
 for s in ['top','right']:bx.spines[s].set_visible(False)
 ins=bx.inset_axes([.0,.0,.24,.2]);w=.55;cx,cy=4.55,3.70
 ins.add_collection(LineCollection(segs,colors='#3d5670',linewidths=1.0));ins.scatter(ex[:,0],ex[:,1],marker='s',s=30,c=SHAFT,zorder=5)
 ins.axvline(mx,c='#555',ls='--',lw=.8);ins.axhline(my,c='#555',ls='--',lw=.8)
 ins.set_xlim(cx-w,cx+w);ins.set_ylim(cy-w*.8,cy+w*.8);ins.set_xticks([]);ins.set_yticks([]);ins.set_title('shaft area (1.1 km)',fontsize=8.5,pad=2)
 bx.add_patch(Rectangle((cx-w,cy-w*.8),2*w,1.6*w,fill=False,lw=.7,ec='#333'))
 fig.savefig(F/'plan.pdf',bbox_inches='tight');fig.savefig(F/'plan.png',dpi=170,bbox_inches='tight');plt.close(fig)

if __name__=='__main__':
 F.mkdir(exist_ok=True);three_d();plan()
