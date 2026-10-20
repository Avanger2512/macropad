import adsk.core, adsk.fusion, json, math
from pathlib import Path

def run(context):
 app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);r=d.rootComponent
 m=adsk.fusion.TemporaryBRepManager.get()
 def shifted(body,y,z,x=0):
  b=m.copy(body);t=adsk.core.Matrix3D.create();t.translation=adsk.core.Vector3D.create(x/10,y/10,z/10)
  if not m.transform(b,t):raise RuntimeError('Transform failed')
  return b
 def overlap(a,b):
  out=m.copy(a)
  if not m.booleanOperation(out,m.copy(b),adsk.fusion.BooleanTypes.IntersectionBooleanType):raise RuntimeError('Boolean failed')
  return out.volume*1000
 carrier=r.bRepBodies.itemByName('MiddleCarrier_Draft');shell=r.bRepBodies.itemByName('UpperShell_Draft');diffuser=r.bRepBodies.itemByName('Diffuser_Draft')
 angle=d.unitsManager.evaluateExpression('caseTilt','rad');s,c=math.sin(angle),math.cos(angle)
 results={}
 drops=(0,.25,.5,1,2,2.5,3,4,5,6,8,10,15,20,25,30,35,40)
 for path in ('vertical','face_normal'):
  target_results={}
  for name,other in [('shell',shell),('diffuser',diffuser)]:
   first=None;peak=0;collisions=[]
   for drop in drops:
    moving=shifted(carrier,0 if path=='vertical' else s*drop,-drop if path=='vertical' else -c*drop)
    volume=overlap(moving,other);peak=max(peak,volume)
    if volume>1e-5:
     collisions.append(drop)
     if first is None:first={'drop_mm':drop,'volume_mm3':volume}
   target_results[name]={'first_collision':first,'maximum_sampled_overlap_mm3':peak,'colliding_samples_mm':collisions}
  results[path]=target_results
 # Diffuser moves toward the interior (negative face normal), with carrier removed.
 first=None
 for drop in drops:
  volume=overlap(shifted(diffuser,s*drop,-c*drop),shell)
  if volume>1e-5:
   first={'drop_mm':drop,'volume_mm3':volume};break
 results['diffuser_inward_without_carrier']={'first_collision':first}
 # Determine whether a small coupled lateral/vertical direction frees carrier.
 directions=[]
 for coefficient in (-.2,-.1,-.05,0,.05,.1,.2):
  first=None
  for drop in drops:
   volume=overlap(shifted(carrier,coefficient*drop,-drop),shell)
   if volume>1e-5:
    first={'drop_mm':drop,'volume_mm3':volume};break
  directions.append({'dy_per_downward_mm':coefficient,'shell_first_collision':first})
 results['carrier_with_diffuser_removed_direction_samples']=directions
 report={'revision':'V7 preprint native assembly audit','removal':results,'sampled_only':True,'hardware_removed_for_path_check':True}
 path=Path('/Users/denisbabiichuk/3dPrint/macropad/cad/fusion/exports/preprint-v7-assembly-audit.json');path.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
