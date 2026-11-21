"""Give each Audio File capsule its own slow current beneath a still surface."""
from math import cos, sin, tau

import bpy
from bpy.app.handlers import persistent


def object_attribute(nodes, name):
    node = nodes.new('ShaderNodeAttribute')
    node.attribute_type = 'OBJECT'
    node.attribute_name = name
    return node


def set_up_liquid(amber):
    nodes = amber.node_tree.nodes
    links = amber.node_tree.links
    old_flow = nodes['Seamless liquid circulation']
    for axis in range(3):
        old_flow.inputs[1].driver_remove('default_value', axis)
    nodes.remove(old_flow)

    # Generated coordinates start and end at each individual fill's bounds.
    # Twist the noise around that tube's centre, with a little shear by depth.
    angle = object_attribute(nodes, 'swirl_angle')
    twist = nodes.new('ShaderNodeMath')
    twist.operation = 'MULTIPLY_ADD'
    links.new(nodes['Separate XYZ.001'].outputs['Z'], twist.inputs[0])
    twist.inputs[1].default_value = 2.7
    links.new(angle.outputs['Factor'], twist.inputs[2])
    rotate = nodes.new('ShaderNodeVectorRotate')
    rotate.rotation_type = 'Z_AXIS'
    rotate.inputs['Center'].default_value = (0.5, 0.5, 0.5)
    links.new(nodes['Texture Coordinate'].outputs['Generated'], rotate.inputs['Vector'])
    links.new(twist.outputs[0], rotate.inputs['Angle'])

    aspect = object_attribute(nodes, 'swirl_scale')
    scale = nodes.new('ShaderNodeVectorMath')
    scale.operation = 'MULTIPLY'
    links.new(rotate.outputs['Vector'], scale.inputs[0])
    links.new(aspect.outputs['Vector'], scale.inputs[1])
    info = nodes.new('ShaderNodeObjectInfo')
    noise = nodes['Amber internal glow turbulence']
    noise.noise_dimensions = '4D'
    noise.inputs['Scale'].default_value = 1.5
    noise.inputs['Distortion'].default_value = 0.28
    links.new(scale.outputs['Vector'], noise.inputs['Vector'])
    links.new(info.outputs['Object Index'], noise.inputs['W'])

    pockets = nodes['Uneven golden light pockets'].color_ramp
    for stop, strength in zip(pockets.elements, (0.32, 0.88, 2.9), strict=True):
        stop.color = (strength, strength, strength, 1)


def air_material():
    material = bpy.data.materials.new('Air inside amber')
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.remove(nodes.get('Principled BSDF'))
    boundary = nodes.new('ShaderNodeBsdfGlass')
    # A submerged air pocket is less refractive than the surrounding liquid.
    boundary.inputs['IOR'].default_value = 1 / 1.333
    boundary.inputs['Roughness'].default_value = 0.065

    # Accentuate the upper-left studio reflection so the curved air boundary
    # survives downsampling to the small source key. The core stays transmissive.
    geometry = nodes.new('ShaderNodeNewGeometry')
    toward_light = nodes.new('ShaderNodeVectorMath')
    toward_light.operation = 'DOT_PRODUCT'
    links.new(geometry.outputs['Normal'], toward_light.inputs[0])
    toward_light.inputs[1].default_value = (-0.56, -0.36, 0.75)
    glint = nodes.new('ShaderNodeValToRGB')
    ramp = glint.color_ramp
    ramp.interpolation = 'EASE'
    ramp.elements[0].position = 0.52
    ramp.elements[0].color = (0, 0, 0, 1)
    ramp.elements[1].color = (1, 0.9, 0.72, 1)
    links.new(toward_light.outputs['Value'], glint.inputs['Fac'])
    reflection = nodes.new('ShaderNodeEmission')
    reflection.inputs['Strength'].default_value = 2.4
    links.new(glint.outputs['Color'], reflection.inputs['Color'])
    surface = nodes.new('ShaderNodeAddShader')
    links.new(boundary.outputs[0], surface.inputs[0])
    links.new(reflection.outputs[0], surface.inputs[1])
    links.new(surface.outputs[0], nodes['Material Output'].inputs['Surface'])
    return material


def animate_current(scene, liquid, ring, air, phase, direction):
    (left, front, bottom), (right, back, surface) = liquid.bound_box[0], liquid.bound_box[6]
    radius = (right - left) / 2
    cx, cy = (left + right) / 2, (front + back) / 2
    height = surface - bottom
    for part in (liquid, ring):
        part['swirl_scale'] = (1.0, 1.0, max(1.0, height / (3 * radius)))
    ring['swirl_angle'] = tau * phase

    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12)
    bubble = bpy.context.object
    bubble.name = liquid.name.replace('amber fill', 'rising bubble')
    bubble.parent = liquid
    bubble.data.materials.append(air)
    for polygon in bubble.data.polygons:
        polygon.use_smooth = True

    # Start above the rounded floor and dissolve below the meniscus. The bubble
    # vanishes before it can repeat, even in the two shortest end capsules.
    bubble_radius = radius * (0.16 + 0.045 * phase)
    low = bottom + radius + bubble_radius
    high = surface - 2 * bubble_radius
    rise = min(2.35 * radius, high - low)
    start = low + (high - low - rise) * phase
    period = scene.frame_end - scene.frame_start + 1
    for offset in range(period + 1):
        frame = scene.frame_start + offset
        turn = tau * (offset / period + phase)
        liquid['swirl_angle'] = direction * (turn + 0.33 * sin(turn))
        liquid.keyframe_insert(data_path='["swirl_angle"]', frame=frame)

        age = (offset / period + phase) % 1
        life = min(age / (0.70 + 0.14 * phase), 1.0)
        envelope = min(1.0, life / 0.20, (1 - life) / 0.26)
        size = bubble_radius * envelope**2 * (3 - 2 * envelope)
        bubble.scale = (size,) * 3
        bubble.location = (cx + 0.32 * radius * sin(direction * turn),
                           cy - radius * (0.42 + 0.15 * cos(turn)), start + rise * life)
        bubble.keyframe_insert(data_path='scale', frame=frame)
        bubble.keyframe_insert(data_path='location', frame=frame)


@persistent
def prepare_audio_file(_filepath):
    scene = bpy.context.scene
    set_up_liquid(bpy.data.materials['Amber liquid | transmissive core'])
    air = air_material()
    # Neighbours have different starting points and can circulate in opposite directions.
    currents = ((0.68, -1), (0.11, 1), (0.87, 1), (0.39, -1),
                (0.04, 1), (0.55, -1), (0.26, 1))
    for number, (phase, direction) in enumerate(currents, 1):
        capsule = f'Capsule {number}'
        liquid = bpy.data.objects[f'{capsule} | amber fill']
        ring = bpy.data.objects[f'{capsule} | liquid meniscus']
        tilt = liquid.data.shape_keys.key_blocks['Gentle liquid surface tilt']
        tilt.driver_remove('value')
        tilt.value = 0
        ring.driver_remove('rotation_euler', 1)
        ring.rotation_euler.y = 0
        liquid.pass_index = ring.pass_index = number
        animate_current(scene, liquid, ring, air, phase, direction)
    scene.frame_set(scene.frame_start)


bpy.app.handlers.load_post.append(prepare_audio_file)
