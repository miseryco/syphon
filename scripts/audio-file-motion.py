"""Light the amber in the Audio File loop while keeping the liquid surfaces still."""
import bpy
from bpy.app.handlers import persistent


@persistent
def prepare_audio_file(_filepath):
    for number in range(1, 8):
        capsule = f'Capsule {number}'
        liquid = bpy.data.objects[f'{capsule} | amber fill']
        ring = bpy.data.objects[f'{capsule} | liquid meniscus']
        tilt = liquid.data.shape_keys.key_blocks['Gentle liquid surface tilt']
        tilt.driver_remove('value')
        tilt.value = 0
        ring.driver_remove('rotation_euler', 1)
        ring.rotation_euler.y = 0

    # Match the light pockets in Plugin and MIDI Device. The scene's shorter
    # circulation path lets the highlights drift gently inside the capsules.
    amber = bpy.data.materials['Amber liquid | transmissive core']
    pockets = amber.node_tree.nodes['Uneven golden light pockets'].color_ramp
    for stop, strength in zip(pockets.elements, (0.12, 0.65, 4.5), strict=True):
        stop.color = (strength, strength, strength, 1)


bpy.app.handlers.load_post.append(prepare_audio_file)
