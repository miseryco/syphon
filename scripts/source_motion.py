"""Render the local amber currents and the Audio File capsules' air bubbles."""
from math import cos, sin, tau
from pathlib import Path

import bpy
from bpy.app.handlers import persistent
from mathutils import Vector


def object_attribute(nodes, name):
    node = nodes.new('ShaderNodeAttribute')
    node.attribute_type = 'OBJECT'
    node.attribute_name = name
    return node


def set_up_liquid(amber, swept):
    nodes = amber.node_tree.nodes
    links = amber.node_tree.links
    old_flow = nodes['Seamless liquid circulation']
    for axis in range(3):
        old_flow.inputs[1].driver_remove('default_value', axis)
    nodes.remove(old_flow)

    # Both charts put the bore around (.5, .5) and its length along Z.
    # A swept chart follows the actual glass around every bend of the cable.
    if swept:
        chart = nodes.new('ShaderNodeAttribute')
        chart.attribute_name = 'bore_coordinates'
        coordinates = chart.outputs['Vector']
        depth = nodes.new('ShaderNodeSeparateXYZ')
        links.new(coordinates, depth.inputs[0])
    else:
        coordinates = nodes['Texture Coordinate'].outputs['Generated']
        depth = nodes['Separate XYZ.001']
    angle = object_attribute(nodes, 'swirl_angle')
    twist = nodes.new('ShaderNodeMath')
    twist.operation = 'MULTIPLY_ADD'
    links.new(depth.outputs['Z'], twist.inputs[0])
    twist.inputs[1].default_value = 2.7
    links.new(angle.outputs['Factor'], twist.inputs[2])
    rotate = nodes.new('ShaderNodeVectorRotate')
    rotate.rotation_type = 'Z_AXIS'
    rotate.inputs['Center'].default_value = (0.5, 0.5, 0.5)
    links.new(coordinates, rotate.inputs['Vector'])
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


def new_bubble(liquid, air, name):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12)
    bubble = bpy.context.object
    bubble.name = name
    bubble.parent = liquid
    bubble.data.materials.append(air)
    for polygon in bubble.data.polygons:
        polygon.use_smooth = True
    return bubble


def loop_frames(scene, phase):
    period = scene.frame_end - scene.frame_start + 1
    for offset in range(period + 1):
        t = offset / period + phase
        life = min((t % 1) / (0.70 + 0.14 * phase), 1.0)
        edge = min(1.0, life / 0.20, (1 - life) / 0.26)
        yield scene.frame_start + offset, tau * t, life, edge**2 * (3 - 2 * edge)


def animate_spin(scene, liquid, phase, direction):
    for frame, turn, _, _ in loop_frames(scene, phase):
        liquid['swirl_angle'] = direction * (turn + 0.33 * sin(turn))
        liquid.keyframe_insert(data_path='["swirl_angle"]', frame=frame)


def key_bubble(bubble, frame, location, size):
    bubble.location = location
    # Express the radius in studio units, independent of the fill's scale.
    bubble.scale = tuple(size / axis for axis in bubble.parent.matrix_world.to_scale())
    bubble.keyframe_insert(data_path='scale', frame=frame)
    bubble.keyframe_insert(data_path='location', frame=frame)


def animate_capsule(scene, liquid, ring, air, phase, direction):
    (left, front, bottom), (right, back, surface) = liquid.bound_box[0], liquid.bound_box[6]
    radius = (right - left) / 2
    cx, cy = (left + right) / 2, (front + back) / 2
    height = surface - bottom
    for part in (liquid, ring):
        part['swirl_scale'] = (1.0, 1.0, max(1.0, height / (3 * radius)))
    ring['swirl_angle'] = tau * phase
    animate_spin(scene, liquid, phase, direction)
    bubble = new_bubble(liquid, air, liquid.name.replace('amber fill', 'rising bubble'))

    # Start above the rounded floor and dissolve below the meniscus. The bubble
    # vanishes before it can repeat, even in the two shortest end capsules.
    bubble_radius = radius * (0.16 + 0.045 * phase)
    low = bottom + radius + bubble_radius
    high = surface - 2 * bubble_radius
    rise = min(2.35 * radius, high - low)
    start = low + (high - low - rise) * phase
    for frame, turn, life, envelope in loop_frames(scene, phase):
        location = (cx + 0.32 * radius * sin(direction * turn),
                    cy - radius * (0.42 + 0.15 * cos(turn)), start + rise * life)
        key_bubble(bubble, frame, location, bubble_radius * envelope)


def prepare_audio_file(scene):
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
        animate_capsule(scene, liquid, ring, air, phase, direction)


def write_chart(mesh, coordinates):
    attribute = mesh.attributes.new('bore_coordinates', 'FLOAT_VECTOR', 'POINT')
    attribute.data.foreach_set('vector', coordinates)


def animate_tube(scene, liquid, phase, direction):
    # The original swept meshes have one ring of vertices per station and an
    # n-gon at each end. Opposite vertices give the centre even at crossings.
    mesh = liquid.data
    sides = mesh.polygons[-1].loop_total
    if sides < 8 or sides % 2 or len(mesh.vertices) % sides:
        raise ValueError(f'{liquid.name} has no circular end cap')
    points = mesh.vertices
    centres = [(points[i].co + points[i + sides // 2].co) * 0.5
               for i in range(0, len(points), sides)]
    radius = (points[0].co - centres[0]).length
    distances = [0.0]
    for a, b in zip(centres, centres[1:]):
        distances.append(distances[-1] + (b - a).length)
    circle = [(0.5 + 0.5 * cos(tau * j / sides), 0.5 + 0.5 * sin(tau * j / sides))
              for j in range(sides)]
    write_chart(mesh, [component for distance in distances for x, y in circle
                       for component in (x, y, distance / distances[-1])])
    liquid['swirl_scale'] = (1., 1., max(1., distances[-1] / (3 * radius)))
    animate_spin(scene, liquid, phase, direction)


def animate_pocket(scene, liquid, phase, direction):
    # The knob inset and the collar are small, compact reservoirs. Their own
    # mesh bounds supply a chart in the same units as a tube cross-section.
    low = Vector(liquid.bound_box[0])
    high = Vector(liquid.bound_box[6])
    span = high - low
    write_chart(liquid.data, [(v.co[i] - low[i]) / span[i]
                              for v in liquid.data.vertices for i in range(3)])
    liquid['swirl_scale'] = (1., 1., 1.)
    animate_spin(scene, liquid, phase, direction)


@persistent
def prepare_source(_filepath):
    kind = Path(bpy.data.filepath).stem.removesuffix('-Loop')
    if kind not in ('Plugin', 'MIDI-Device', 'Audio-File'):
        return
    scene = bpy.context.scene
    set_up_liquid(bpy.data.materials['Amber liquid | transmissive core'], swept=kind != 'Audio-File')
    if kind == 'Audio-File':
        prepare_audio_file(scene)
    elif kind == 'Plugin':
        lower = scene.objects['Horizontal tube 1.08 | amber liquid']
        upper = scene.objects['Horizontal tube 1.92 | amber liquid']
        lens = scene.objects['Knob amber inset']
        lower.pass_index, upper.pass_index, lens.pass_index = 2, 4, 7
        animate_tube(scene, lower, 0.64, -1)
        animate_tube(scene, upper, 0.13, 1)
        animate_pocket(scene, lens, 0.43, -1)
    else:
        cable = scene.objects['Cable | separate amber core']
        collar = scene.objects['Rear collar liquid']
        cable.pass_index, collar.pass_index = 3, 6
        animate_tube(scene, cable, 0.33, -1)
        animate_pocket(scene, collar, 0.83, 1)
    scene.frame_set(scene.frame_start)


bpy.app.handlers.load_post.append(prepare_source)
