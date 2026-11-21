"""Run in Blender before the light-edition recipe opens the Audio File scene."""
import bpy
from bpy.app.handlers import persistent


@persistent
def animate_fill_levels(_filepath):
    drop_fraction = 0.72
    for index in range(7):
        capsule = f'Capsule {index + 1}'
        liquid = bpy.data.objects[f'{capsule} | amber fill']
        ring = bpy.data.objects[f'{capsule} | liquid meniscus']
        vertices = liquid.data.shape_keys.reference_key.data
        radius = (max(v.co.x for v in vertices) - min(v.co.x for v in vertices)) / 2
        shoulder = min(v.co.z for v in vertices) + radius
        top = max(v.co.z for v in vertices)
        ring_height = ring.location.z

        # Leave the rounded base intact. Lower the flat liquid surface and its
        # meniscus together inside the straight section of the stationary glass.
        lowered = liquid.shape_key_add(name='Lower liquid level', from_mix=False)
        for vertex, target in zip(vertices, lowered.data):
            target.co.z -= drop_fraction * max(0, vertex.co.z - shoulder)
        travel = drop_fraction * (top - shoulder)

        # Each pulse lasts one second and starts four frames after its neighbour.
        # Frames 1 and 49 both match the approved still; only 1–48 are exported.
        start = 1 + 4 * index
        for frame, amount in ((start, 0), (start + 12, 1), (start + 24, 0)):
            lowered.value = amount
            lowered.keyframe_insert(data_path='value', frame=frame)
            ring.location.z = ring_height - travel * amount
            ring.keyframe_insert(data_path='location', index=2, frame=frame)
    bpy.context.scene.frame_set(1)


bpy.app.handlers.load_post.append(animate_fill_levels)
