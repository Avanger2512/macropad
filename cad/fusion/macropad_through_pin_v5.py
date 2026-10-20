"""Replace blind V4 retention with an X-direction through pin clear of contacts.

V5 preserves the tested seating depth and guide positions. A reinforced positive-Y
land keeps the pin outside the central MX post opening. Existing V4 archives are
preserved; native body names identify lineage rather than current revision.
"""
import importlib.util
import json
from pathlib import Path
import adsk.core
import adsk.fusion

HERE=Path('/Users/denisbabiichuk/3dPrint/macropad/cad/fusion')
EXPORT=HERE/'exports'


def load_helpers():
    spec=importlib.util.spec_from_file_location('v4_carrier',HERE/'macropad_carrier_compact_v4.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module,module.helpers()


def design():
    app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct)
    if d is None or app.activeDocument.name!='macropad':raise RuntimeError('Activate macropad')
    return app,d,d.rootComponent


def healthy(d):
    errors=[t.name for t in d.timeline if not getattr(t.entity,'isSuppressed',False)
            and t.healthState!=adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState]
    if errors:raise RuntimeError('Unhealthy features '+str(errors))


def initialize(context):
    app,d,r=design();m,h=load_helpers()
    if d.userParameters.itemByName('throughPinV5Y'):raise RuntimeError('V5 already initialized')
    backup=EXPORT/'macropad_before_through_pin_v5.f3d'
    if not d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(str(backup))):raise RuntimeError('Backup failed')
    baseline={b.name:b.volume*1000 for b in r.bRepBodies}
    (EXPORT/'through-pin-v5-baseline.json').write_text(json.dumps(baseline,indent=2)+'\n')
    for name,expr in [('throughPinV5Y','2.8 mm'),('throughPinV5Z','1.6 mm'),
                      ('throughPinV5Bore','1.2 mm'),('throughPinV5Diameter','1 mm'),('throughPinV5Length','20 mm')]:
        d.userParameters.add(name,h.value(expr),'mm','V5 transverse through retaining pin')
    names=['Compact V4 single pin receiver bore','Compact V4 single pin hotswap bore','Compact V4 single pin reference']
    names += [f'SW{i} V4 single retaining pin' for i in range(1,7)]
    for name in reversed(names):
        feature=r.features.extrudeFeatures.itemByName(name)
        if feature is None:raise RuntimeError('Missing '+name)
        feature.isSuppressed=True
    hotswap=r.bRepBodies.itemByName('HotswapCompact_Pin_V4');hotswap.isVisible=True
    plane=h.offset(r,r.constructionPlanes.itemByName('Exterior face datum'),'Carrier V4 V5 reinforcement datum','-carrierV4BottomDepth+0.2 mm')
    sketch=h.rectangle(d,r,plane,'V5 hotswap reinforcement','compactV4TrialX-5.2 mm','keyRowOne+2.7 mm','10.4 mm','1.5 mm')
    h.extrude(r,sketch,'V5 hotswap reinforced pin land','2.8 mm',adsk.fusion.FeatureOperations.JoinFeatureOperation,True,hotswap)
    d.computeAll();healthy(d)
    print(json.dumps({'stage':'V5 initialized','reinforcement_y_mm':[2.7,4.2],'pin_axis_y_z_mm':[2.8,1.6]}))


def cut_position(label,cx,cy,body_names):
    app,d,r=design();m,h=load_helpers()
    if r.features.extrudeFeatures.itemByName(label+' V5 through pin bore'):raise RuntimeError(label+' already updated')
    plane=h.offset(r,r.yZConstructionPlane,label+' V5 pin entry datum',f'({cx})-10 mm')
    sketch=m.channel_circle(h,d,r,plane,label+' V5 through pin',cx,cy,-10,
                            h.evaluate(d,'throughPinV5Y')*10,h.evaluate(d,'throughPinV5Z')*10,'throughPinV5Bore')
    for index,name in enumerate(body_names):
        body=r.bRepBodies.itemByName(name);body.isVisible=True
        suffix='' if index==0 else ' holder'
        h.extrude(r,sketch,label+' V5 through pin bore'+suffix,'20 mm',adsk.fusion.FeatureOperations.CutFeatureOperation,True,body)
    if label=='Compact':
        pin_sketch=m.channel_circle(h,d,r,plane,'V5 reference pin',cx,cy,-10,
                                    h.evaluate(d,'throughPinV5Y')*10,h.evaluate(d,'throughPinV5Z')*10,'throughPinV5Diameter')
        pin=h.extrude(r,pin_sketch,'V5 through pin reference','throughPinV5Length',adsk.fusion.FeatureOperations.NewBodyFeatureOperation,True).bodies.item(0)
        pin.name='MechanicalPin_Through_V5_REFERENCE'
    d.computeAll();healthy(d)
    print(json.dumps({'stage':'V5 through bore','position':label}))


def run(context):
    initialize(context)
    cut_position('Compact','compactV4TrialX','keyRowOne',['SwitchFitCoupon_Compact_V4','HotswapCompact_Pin_V4'])
    m,_=load_helpers()
    for label,cx,cy in m.locations():cut_position(label,cx,cy,['MiddleCarrier_Draft'])
