"""Read-only, sampled vertical carrier removal check using temporary BRep bodies."""
import adsk.core,adsk.fusion,json
def run(_context: str):
 d=adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct);r=d.rootComponent
 m=adsk.fusion.TemporaryBRepManager.get()
 carrier=r.bRepBodies.itemByName("MiddleCarrier_Draft")
 result=[]
 for drop in (0,0.25,0.5,1,2,3,4,5,6,8,10,15,20,25,30,35):
  for name in ("UpperShell_Draft","Diffuser_Draft"):
   moving=m.copy(carrier);matrix=adsk.core.Matrix3D.create();matrix.translation=adsk.core.Vector3D.create(0,0,-drop/10)
   if not m.transform(moving,matrix):raise RuntimeError("Temporary translation failed")
   other=m.copy(r.bRepBodies.itemByName(name))
   ok=m.booleanOperation(moving,other,adsk.fusion.BooleanTypes.IntersectionBooleanType)
   if not ok:raise RuntimeError("Temporary intersection failed")
   if moving.volume*1000 > 1e-6:raise RuntimeError(f"Carrier removal collision at {drop} mm against {name}")
   result.append({"drop_mm":drop,"other":name,"valid":moving.isValid,"faces":moving.faces.count,"volume_mm3":moving.volume*1000})
 print(json.dumps({"vertical_removal_samples":result}))
