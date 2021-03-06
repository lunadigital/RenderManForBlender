# ##### BEGIN MIT LICENSE BLOCK #####
#
# Copyright (c) 2015 - 2017 Pixar
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
#
# ##### END MIT LICENSE BLOCK #####

import bpy
import math
import blf
from bpy.types import Panel
from bl_ui.utils import PresetPanel
from .nodes import NODE_LAYOUT_SPLIT, is_renderman_nodetree, panel_node_draw

# global dictionaries
from bl_ui.properties_particle import ParticleButtonsPanel

# helper functions for parameters
from .nodes import draw_nodes_properties_ui, draw_node_properties_recursive, socket_node_input

from .rman_ui.rman_ui_base import _RManPanelHeader
from .rman_ui.rman_ui_base import CollectionPanel
from .rman_render import RmanRender

def get_panels():
    exclude_panels = {
        'DATA_PT_area',
        'DATA_PT_camera_dof',
        'DATA_PT_falloff_curve',
        'DATA_PT_light',
        'DATA_PT_preview',
        'DATA_PT_shadow',
        # 'DATA_PT_spot',
        'DATA_PT_sunsky',
        # 'MATERIAL_PT_context_material',
        'MATERIAL_PT_diffuse',
        'MATERIAL_PT_flare',
        'MATERIAL_PT_halo',
        'MATERIAL_PT_mirror',
        'MATERIAL_PT_options',
        'MATERIAL_PT_pipeline',
        'MATERIAL_PT_preview',
        'MATERIAL_PT_shading',
        'MATERIAL_PT_shadow',
        'MATERIAL_PT_specular',
        'MATERIAL_PT_sss',
        'MATERIAL_PT_strand',
        'MATERIAL_PT_transp',
        'MATERIAL_PT_volume_density',
        'MATERIAL_PT_volume_integration',
        'MATERIAL_PT_volume_lighting',
        'MATERIAL_PT_volume_options',
        'MATERIAL_PT_volume_shading',
        'MATERIAL_PT_volume_transp',
        'RENDERLAYER_PT_layer_options',
        'RENDERLAYER_PT_layer_passes',
        'RENDERLAYER_PT_views',
        'RENDER_PT_antialiasing',
        'RENDER_PT_bake',
        'RENDER_PT_motion_blur',
        'RENDER_PT_performance',
        'RENDER_PT_freestyle',
        # 'RENDER_PT_post_processing',
        'RENDER_PT_shading',
        'RENDER_PT_render',
        'RENDER_PT_stamp',
        'RENDER_PT_simplify',
        'RENDER_PT_color_management',
        'TEXTURE_PT_context_texture',
        'WORLD_PT_ambient_occlusion',
        'WORLD_PT_environment_lighting',
        'WORLD_PT_gather',
        'WORLD_PT_indirect_lighting',
        'WORLD_PT_mist',
        'WORLD_PT_preview',
        'WORLD_PT_world',
        'NODE_DATA_PT_light',
        'NODE_DATA_PT_spot',
    }

    panels = []
    for t in bpy.types.Panel.__subclasses__():
        if hasattr(t, 'COMPAT_ENGINES') and 'BLENDER_RENDER' in t.COMPAT_ENGINES:
            if t.__name__ not in exclude_panels:
                panels.append(t)

    return panels


# icons
import os
from . icons.icons import load_icons
from . util import get_addon_prefs


from bpy.props import (PointerProperty, StringProperty, BoolProperty,
                       EnumProperty, IntProperty, FloatProperty, FloatVectorProperty,
                       CollectionProperty)

# ------- UI panel definitions -------
narrowui = 180
subpanel_classes = []

class PRManButtonsPanel(_RManPanelHeader):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"


class RENDER_PT_renderman_render(PRManButtonsPanel, Panel):
    bl_label = "Render"

    def draw(self, context):
        self.layout.use_property_split = True
        self.layout.use_property_decorate = False

        if context.scene.render.engine != "PRMAN_RENDER":
            return

        icons = load_icons()
        layout = self.layout
        rd = context.scene.render
        rm = context.scene.renderman
        rman_render = RmanRender.get_rman_render()
        is_rman_interactive_running = rman_render.rman_interactive_running

        if not is_rman_interactive_running:

            # Render
            row = layout.row(align=True)
            rman_render_icon = icons.get("render")
            row.operator("render.render", text="Render",
                        icon_value=rman_render_icon.icon_id)

            # IPR
            rman_rerender_controls = icons.get("start_ipr")
            row.operator('lighting.start_interactive', text="Start IPR",
                            icon_value=rman_rerender_controls.icon_id)

            # Batch Render
            rman_batch = icons.get("batch_render")
            row.operator("render.render", text="Render Animation",
                        icon_value=rman_batch.icon_id).animation = True

        else:
            row = layout.row(align=True)
            rman_rerender_controls = icons.get("stop_ipr")
            row.operator('lighting.stop_interactive', text="Stop IPR",
                            icon_value=rman_rerender_controls.icon_id)


        split = layout.split(factor=0.33)

        col = layout.column()
        col.enabled = not is_rman_interactive_running
        col = layout.column()
        col.enabled = not is_rman_interactive_running
        row = col.row()
        row.prop(rm, "render_into", text="Render To")

        col = layout.column()
        col.enabled = not is_rman_interactive_running
        #col.prop(context.scene.renderman, "render_selected_objects_only")
        #col.prop(rm, "do_denoise")
        col.prop(rm, "do_holdout_matte", text="Render Holdouts")

class RENDER_PT_renderman_presets(PresetPanel, Panel):
    bl_label = "RenderMan Presets"
    preset_subdir = os.path.join("renderman", "render")
    preset_operator = "script.execute_preset"
    preset_add_operator = "render.renderman_preset_add"
    COMPAT_ENGINES = {'PRMAN_RENDER'}

class RENDER_PT_renderman_sampling(PRManButtonsPanel, Panel):
    bl_label = "Sampling"

    def draw_header_preset(self, context):
        RENDER_PT_renderman_presets.draw_panel_header(self.layout)

    def draw(self, context):
        self.layout.use_property_split = True
        self.layout.use_property_decorate = False

        layout = self.layout
        scene = context.scene
        rm = scene.renderman

        col = layout.column(align=True)
        col.prop(rm, "min_samples", text="Min Samples")
        col.prop(rm, "max_samples", text="Max Samples")
        col.prop(rm, "pixel_variance", text="Pixel Variance")

        col = layout.column(align=True)
        col.prop(rm, "max_specular_depth", text="Specular Depth")
        col.prop(rm, "max_diffuse_depth", text="Diffuse Depth")

        col = layout.column(align=False)
        col.prop(rm, 'incremental')


class RENDER_PT_renderman_sampling_preview(Panel):
    bl_label = "Interactive and Preview Sampling"
    bl_parent_id = 'RENDER_PT_renderman_sampling'
    bl_options = {'DEFAULT_CLOSED'}
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'

    def draw(self, context):
        self.layout.use_property_split = True
        self.layout.use_property_decorate = False

        layout = self.layout
        scene = context.scene
        rm = scene.renderman

        col = layout.column()
        row = col.row(align=True)

        col = layout.column(align=True)
        col.prop(rm, "preview_min_samples", text="Min Samples")
        col.prop(rm, "preview_max_samples", text="Max Samples")
        col.prop(rm, "preview_pixel_variance", text="Pixel Variance")

        col = layout.column(align=True)
        col.prop(rm, "preview_max_specular_depth", text="Specular Depth")
        col.prop(rm, "preview_max_diffuse_depth", text="Diffuse Depth")


def draw_subpanel(panel):

# Define node
    def get_node(panel, context):
        if panel == "integrator" or panel == "advanced_integrator":
            rm = context.scene.renderman
            node = getattr(rm, "%s_settings" % rm.integrator)

        if panel == "world":
            world = context.scene.world
            node = world.renderman.get_light_node()

        if panel == "light":
            light = context.light
            node = light.renderman.get_light_node()

        if panel == "camera":
            cam = context.camera
            node = cam.renderman.get_projection_node()

        return node

# Hide unused subpanels
    @classmethod
    def poll(self, context):
        if panel == "world" and context.scene.world.renderman.renderman_type == 'NONE':
            return

        elif panel == "camera" and context.camera.renderman.projection_type == 'none':
            return

        elif panel == "light" and context.light.renderman.use_renderman_node == False:
            return

        elif panel == "material" or panel == "shader_light":
            if is_renderman_nodetree(context.material):
                if panel == "material":
                    return panel_node_draw(self, context, 'Bxdf', "draw", self.number) == "open"
                else:
                    return panel_node_draw(self, context, 'Light', "draw", self.number) == "open"

        elif panel == "advanced_material":
            return panel_node_draw(self, context, 'Bxdf', "advanced_draw", self.number) == "open"

        else:
            node = get_node(panel, context)
            return draw_panel(node, node.prop_names, self.number, panel) == 'open'

# Get header title
    def draw_header(self, context):
        layout = self.layout
        if panel == "material":
            panel_node_draw(layout, context, 'Bxdf', "header", self.number)
        elif panel == "advanced_material":
            panel_node_draw(layout, context, 'Bxdf', "subheader", self.number)
        elif panel == "shader_light":
            panel_node_draw(layout, context, 'Light', "header", self.number)
        elif panel == "advanced_integrator":
            node = get_node(panel, context)
            draw_properties(node, node.prop_names, self, "subheader" , self.number)
        else:
            node = get_node(panel, context)
            draw_properties(node, node.prop_names, self, "header" , self.number)

# Draw properties
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        if panel == "material":
            panel_node_draw(layout, context, 'Bxdf', "subpanel", self.number)
        elif panel == "advanced_material":
            panel_node_draw(layout, context, 'Bxdf', "subsubpanel", self.number)
        elif panel == "shader_light":
            panel_node_draw(layout, context, 'Light', "subpanel", self.number)
        elif panel == "advanced_integrator":
            node = get_node(panel, context)
            draw_properties(node, node.prop_names, self, "subsubpanel" , self.number)
        else:
            node = get_node(panel, context)
            draw_properties(node, node.prop_names, self, "subpanel" , self.number)

# Create subpanels and assign them to parent panel
    x = 0
    for i in range(26):
        idname = "RENDER_PT_renderman_"+panel+"_subpanel_%d" % i
        if panel == "integrator":
            parent = "RENDER_PT_renderman_integrator"
        elif panel == "material":
            parent = "MATERIAL_PT_renderman_shader_surface"
        elif panel == "shader_light":
            parent = "MATERIAL_PT_renderman_shader_light"
        elif panel == "advanced_material":
            if i % 2 == 0:
                parent = "RENDER_PT_renderman_material_subpanel_%d" % x
                x += 1
        elif panel == "advanced_integrator":
            if i % 2 == 0:
                parent = "RENDER_PT_renderman_integrator_subpanel_%d" % x
                x += 1
        else:
            parent = "DATA_PT_renderman_"+ panel
        index = i

        opclass = type("RENDER_PT_renderman_subpanel_%d" % i,
               (PRManButtonsPanel, Panel),
               {"bl_idname": idname, "bl_label": " ", "bl_options": {'DEFAULT_CLOSED'},
               "number": index,
               "bl_parent_id": parent,
               "poll": poll, "draw": draw, "draw_header": draw_header},
               )
        subpanel_classes.append(opclass)

def draw_properties(node, prop_names, self, place = "panel", number = 0):
    layout = self.layout
    col = layout.column()
    props_list = []
    props_list_advanced = []
    for prop_name in prop_names:
        prop_meta = node.prop_meta[prop_name]
        prop = getattr(node, prop_name)

        # Hide notes
        if prop_name == "Notes":
            continue

        if prop_meta['renderman_type'] == 'page':
            props_list.append(prop_name)

        else:
         if place == "panel":
            col.prop(node, prop_name)

    length = len(props_list)

    if place == "header":
        if number < length:
            props_list_attr = getattr(node, props_list[number])
            for prop in props_list_attr:
                if prop.startswith('enable'):
                    self.layout.prop(node, prop, text="")
                else:
                    return layout.label(text = props_list[number])

    if place == "subheader":
        i = int(number / 2)
        if number < length * 2:
            props_list_attr = getattr(node, props_list[i])
            for prop in props_list_attr:
                prop_meta = node.prop_meta[prop]
                if prop_meta['renderman_type'] == 'page':
                    prop_split = prop.split(".")[1]
                    props_list_advanced.append(prop_split)
                    if len(props_list_advanced) == 2 and number % 2 != 0:
                        return layout.label(text = props_list_advanced[1])
                    if len(props_list_advanced) == 1 and number % 2 == 0:
                        return layout.label(text = props_list_advanced[0])

    if place == "subpanel":
        if number < length:
            if props_list[number] == "Falloff" or props_list[number] == "Ramp":
                rm = bpy.context.light.renderman
                nt = bpy.context.light.node_tree
                float_node = nt.nodes[rm.float_ramp_node]
                layout.template_curve_mapping(float_node, 'mapping')
            elif props_list[number] == "Color Ramp":
                rm = bpy.context.light.renderman
                nt = bpy.context.light.node_tree
                ramp_node = nt.nodes[rm.color_ramp_node]
                layout.template_color_ramp(ramp_node, 'color_ramp')
            else:
                props_list_attr = getattr(node, props_list[number])
                for prop in props_list_attr:
                    prop_meta = node.prop_meta[prop]
                    if prop_meta['renderman_type'] == 'page':
                        continue
                    else:
                        if prop.startswith('enable'):
                            continue
                        else:
                            col.prop(node, prop)

    if place == "subsubpanel":
        i = int(number / 2)
        props_list_attr = getattr(node, props_list[i])
        for prop in props_list_attr:
            prop_meta = node.prop_meta[prop]
            if prop_meta['renderman_type'] == 'page':
                props_list_advanced.append(prop)

        if number % 2 == 0:
            props_list_advanced_attr = getattr(node, props_list_advanced[0])
            for pr in props_list_advanced_attr:
                col.prop(node, pr)
        if number % 2 != 0 and len(props_list_advanced) == 2:
            props_list_advanced_attr = getattr(node, props_list_advanced[1])
            for pr in props_list_advanced_attr:
                col.prop(node, pr)

def draw_panel(node, prop_names, number, panel):
    props_list = []
    props_list_advanced = []
    for prop_name in prop_names:
        prop_meta = node.prop_meta[prop_name]
        if prop_name == "Notes":
            continue

        if prop_meta['renderman_type'] == 'page':
            props_list.append(prop_name)

    length = len(props_list)

    if panel.startswith("advanced"):
        i = int(number / 2)
        if number < length * 2:
            props_list_attr = getattr(node, props_list[i])
            for prop in props_list_attr:
                prop_meta = node.prop_meta[prop]
                if prop_meta['renderman_type'] == 'page':
                    prop_split = prop.split(".")[0]
                    if prop_split in props_list_advanced:
                        if number % 2 != 0:
                            return "open"
                    else:
                        props_list_advanced.append(prop_split)
                        if number % 2 == 0:
                            return "open"

    elif number < length:
        return "open"

class RENDER_PT_renderman_integrator(PRManButtonsPanel, Panel):
    bl_label = "Integrator"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        scene = context.scene
        rm = scene.renderman

        integrator_settings = getattr(rm, "%s_settings" % rm.integrator)

        col = layout.column()
        col.prop(rm, "integrator")

        layout.separator()
        col = layout.column()

        draw_properties(integrator_settings, integrator_settings.prop_names, self)

    draw_subpanel("integrator")
    draw_subpanel("advanced_integrator")

class RENDER_PT_renderman_spooling(PRManButtonsPanel, Panel):
    bl_label = "External Rendering"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        rm = context.scene.renderman

        self.layout.prop(rm, 'enable_external_rendering', text="")

    def draw(self, context):
        self.layout.use_property_split = True
        self.layout.use_property_decorate = False

        layout = self.layout
        scene = context.scene
        rm = scene.renderman

        rman_render = RmanRender.get_rman_render()
        is_rman_interactive_running = rman_render.rman_interactive_running
        layout.enabled = not is_rman_interactive_running

        # button
        icons = load_icons()
        col = layout.column()
        #col.enabled = rm.enable_external_rendering
        rman_batch = icons.get("batch_render")
        col.operator("renderman.external_render",
                     text="External Render", icon_value=rman_batch.icon_id)


#        row = layout.row()
#        split = row.split(factor=0.33)
#        col = split.column()
#        col.prop(rm, "external_denoise")
#        sub_row = col.row()
#        sub_row.enabled = rm.external_denoise
#        sub_row.prop(rm, "crossframe_denoise")
#
#        # display driver
#        split = split.split()
#        col = split.column()

        col.prop(rm, "display_driver", text='Render To')

#        sub_row = col.row()
#        if rm.display_driver == 'openexr':
#            sub_row = col.row()
#            sub_row.prop(rm,  "exr_format_options")
#            sub_row = col.row()
#            sub_row.prop(rm,  "exr_compression")

        # do animation
        col.prop(rm, 'external_animation')
        col = layout.column(align=True)
        col.enabled = rm.external_animation
        col.prop(scene, "frame_start", text="Start")
        col.prop(scene, "frame_end", text="End")

        #col = layout.column()
        #col.enabled = rm.enable_external_rendering
        #col.prop(rm, 'external_denoise')
        #col = layout.column()
        #col.enabled = rm.external_denoise and rm.external_animation
        #col.prop(rm, 'crossframe_denoise')

class RENDER_PT_renderman_spooling_export_options(PRManButtonsPanel, Panel):
    bl_label = "Spool Options"
    bl_parent_id = 'RENDER_PT_renderman_spooling'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        self.layout.use_property_split = True
        self.layout.use_property_decorate = False

        layout = self.layout
        scene = context.scene
        rm = scene.renderman

        rman_render = RmanRender.get_rman_render()
        is_rman_interactive_running = rman_render.rman_interactive_running
        layout.enabled = not is_rman_interactive_running

        #layout.enabled = rm.enable_external_rendering
        col = layout.column()
        col.prop(rm, "queuing_system")

        #col = layout.column()
        #col.prop(rm, "generate_rib")

        #col = layout.column()
        #col.enabled = rm.generate_rib
        #col.prop(rm, "generate_object_rib")

        #col = layout.column()
        #col.prop(rm, "generate_alf")
        #col = layout.column()

        #col.enabled = rm.generate_alf and rm.generate_render
        #col.prop(rm, "do_render")
        #col = layout.column()
       # col.enabled = rm.do_render and rm.generate_alf and rm.generate_render

        col = layout.column(align = True)
        col.prop(rm, "rib_format")
        col.prop(rm, "rib_compression")

        col = layout.column()
        #col.enabled = rm.generate_alf
        #col.prop(rm, 'custom_alfname')
        #col.prop(rm, "convert_textures")
        #col.prop(rm, "generate_render")
        #col = layout.column()
        #col.enabled = rm.generate_render
        col.prop(rm, 'custom_cmd')

        col = layout.column()
        #col.enabled = rm.generate_render
        col.prop(rm, "override_threads")
        col = layout.column()
        col.enabled = rm.override_threads
        col.prop(rm, "external_threads")

        col = layout.column()
        #col.enabled = rm.external_denoise and rm.generate_alf
        col.prop(rm, 'denoise_cmd')
        #col.prop(rm, 'spool_denoise_aov')
        col = layout.column()
        #col.enabled =not rm.spool_denoise_aov and rm.external_denoise
        col.prop(rm, "denoise_gpu")

        # checkpointing
        col = layout.column()
        #col.enabled = rm.generate_alf and rm.generate_render
        col.prop(rm, 'recover')
        col.prop(rm, 'enable_checkpoint')
        col = layout.column()
        col.enabled = rm.enable_checkpoint
        col.prop(rm, 'asfinal')
        col.prop(rm, 'checkpoint_type')
        col.prop(rm, 'checkpoint_interval')
        col.prop(rm, 'render_limit')


class RENDER_PT_renderman_motion_blur(PRManButtonsPanel, Panel):
    bl_label = "Motion Blur"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        rm = context.scene.renderman

        self.layout.prop(rm, "motion_blur", text="")

    def draw(self, context):
        self.layout.use_property_split = True
        self.layout.use_property_decorate = False

        rm = context.scene.renderman
        layout = self.layout

        col = layout.column()
        col.enabled = rm.motion_blur
        col.prop(rm, "motion_segments")
        col.prop(rm, "sample_motion_blur")
        col.prop(rm, "shutter_timing")

        col = layout.column(align=True)
        col.enabled = rm.motion_blur
        col.prop(rm, "shutter_angle")
        col.prop(rm, "shutter_efficiency_open")
        col.prop(rm, "shutter_efficiency_close")


class RENDER_PT_renderman_baking(PRManButtonsPanel, Panel):
    bl_label = "Baking"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        rman_render = RmanRender.get_rman_render()
        is_rman_interactive_running = rman_render.rman_interactive_running
        layout.enabled = not is_rman_interactive_running
        row = layout.row()
        icons = load_icons()
        rman_batch = icons.get("batch_render")
        row.operator("renderman.bake",
                     text="Bake", icon_value=rman_batch.icon_id)


class RENDER_PT_renderman_advanced_settings(PRManButtonsPanel, Panel):
    bl_label = "Advanced"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        self.layout.use_property_split = True
        self.layout.use_property_decorate = False

        layout = self.layout
        scene = context.scene
        rm = scene.renderman

        col = layout.column()

        col.prop(rm, "threads")
        #col.prop(rm, 'hider_decidither')


        #col.prop(rm, "shadingrate")
        #col.prop(rm, "dicing_strategy")
        #col.prop(rm, "worlddistancelength")

        layout.separator()
        col = layout.column()

        col.prop(rm, "texture_cache_size")
        col.prop(rm, "geo_cache_size")
        col.prop(rm, "opacity_cache_size")

        layout.separator()
        col = layout.column(align = True)

        col.prop(rm, "pixelfilter", text="Pixel Filter:")
        col.prop(rm, "pixelfilter_x", text="Size X")
        col.prop(rm, "pixelfilter_y", text="Size Y")

        #col = layout.column()
        #col.prop(rm, "dark_falloff")

        col = layout.column(align = True)
        col.prop(rm, "bucket_shape")
        if rm.bucket_shape == 'SPIRAL':
            col = layout.column(align = True)
            col.prop(rm, "bucket_sprial_x", text="X")
            col.prop(rm, "bucket_sprial_y", text="Y")

        col = layout.column()
        col.prop(rm, "use_metadata")
        col = layout.column()
        col.enabled = rm.use_metadata
        col.prop(rm, "custom_metadata")

        col = layout.column()
        col.prop(rm, "use_statistics", text="Output stats")

        #col.operator('rman.open_stats')
        #col.operator('rman.open_rib')

        layout.separator()
        col = layout.column()

        #col.prop(rm, "editor_override")

        #col = layout.column(align = True)
        #col.prop(rm, "rib_format")
        #col.prop(rm, "rib_compression")

        col = layout.column()
        #col.prop(rm, "always_generate_textures")
        #col.prop(rm, "lazy_rib_gen")



class MESH_PT_renderman_prim_vars(CollectionPanel, Panel):
    bl_context = "data"
    bl_label = "Primitive Variables"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_item(self, layout, context, item):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        ob = context.object
        if context.mesh:
            geo = context.mesh
        layout.prop(item, "name")

        col = layout.column()
        col.prop(item, "data_source", text="Source")
        if item.data_source == 'VERTEX_COLOR':
            col.prop_search(item, "data_name", geo, "vertex_colors", text="")
        elif item.data_source == 'UV_TEXTURE':
            col.prop_search(item, "data_name", geo, "uv_textures", text="")
        elif item.data_source == 'VERTEX_GROUP':
            col.prop_search(item, "data_name", ob, "vertex_groups", text="")

    @classmethod
    def poll(cls, context):
        if not context.mesh:
            return False
        return CollectionPanel.poll(context)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        mesh = context.mesh
        rm = mesh.renderman

        self._draw_collection(context, layout, rm, "Primitive Variables:",
                              "collection.add_remove", "mesh", "prim_vars",
                              "prim_vars_index")

        layout.prop(rm, "export_default_uv")
        layout.prop(rm, "export_default_vcol")
        layout.prop(rm, "export_flipv")
        layout.prop(rm, "interp_boundary")
        layout.prop(rm, "face_boundary")


class ShaderNodePanel(_RManPanelHeader):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_label = 'Node Panel'

    bl_context = ""

    @classmethod
    def poll(cls, context):
        if not _RManPanelHeader.poll(context):
            return False
        if cls.bl_context == 'material':
            if context.material and context.material.node_tree != '':
                return True
        if cls.bl_context == 'data':
            if not context.light:
                return False
            if context.light.renderman.use_renderman_node:
                return True
        return False


class ShaderPanel(_RManPanelHeader):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'

    shader_type = 'surface'
    param_exclude = {}

    @classmethod
    def poll(cls, context):
        is_rman = _RManPanelHeader.poll(context)
        if cls.bl_context == 'data' and cls.shader_type == 'light':
            return (hasattr(context, "light") and context.light is not None and is_rman)
        elif cls.bl_context == 'world':
            return (hasattr(context, "world") and context.world is not None and is_rman)
        elif cls.bl_context == 'material':
            return (hasattr(context, "material") and context.material is not None and is_rman)


class MATERIAL_PT_renderman_preview(Panel, ShaderPanel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_options = {'DEFAULT_CLOSED'}
    bl_context = "material"
    bl_label = "Preview"

    def draw(self, context):
        layout = self.layout
        mat = context.material
        row = layout.row()



        if mat:
            row.template_preview(context.material, show_buttons=1)
            # if mat.node_tree:
            #    layout.prop_search(
            #        mat, "node_tree", bpy.data, "node_groups")

        layout.separator()
        split = layout.split()

        col = split.column(align=True)
        col.label(text="Viewport Color:")
        col.prop(mat, "diffuse_color", text="")
        #col.prop(mat, "alpha")

        #col.separator()
        #col.label("Viewport Alpha:")
        #col.prop(mat.game_settings, "alpha_blend", text="")

        col = split.column(align=True)
        col.label(text="Viewport Specular:")
        col.prop(mat, "specular_color", text="")
        #FIXME col.prop(mat, "specular_hardness", text="Hardness")

class MATERIAL_PT_renderman_shader_surface(ShaderPanel, Panel):
    bl_context = "material"
    bl_label = "Surface"
    shader_type = 'Bxdf'

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        mat = context.material
        rm = mat.renderman
        row = layout.row()

        if is_renderman_nodetree(mat):
            panel_node_draw(layout, context, input_name='Bxdf')

        else:
            row.prop(rm, "copy_color_params")
            layout.operator('shading.add_renderman_nodetree').idtype = "material"

    draw_subpanel("material")
    draw_subpanel("advanced_material")

class MATERIAL_PT_renderman_shader_light(ShaderPanel, Panel):
    bl_context = "material"
    bl_label = "Light Emission"
    shader_type = 'Light'

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        if context.material.node_tree:

            panel_node_draw(layout, context, input_name='Light')
    draw_subpanel("shader_light")


class MATERIAL_PT_renderman_shader_displacement(ShaderPanel, Panel):
    bl_context = "material"
    bl_label = "Displacement"
    shader_type = 'Displacement'

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        if context.material.node_tree:
            panel_node_draw(layout, context, input_name='Displacement')
            # BBM addition begin

        # BBM addition end
        # self._draw_shader_menu_params(layout, context, rm)


class RENDER_PT_layer_options(PRManButtonsPanel, Panel):
    bl_label = "Layer"
    bl_context = "render_layer"

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        rd = scene.render
        rl = rd.layers.active

        split = layout.split()

        col = split.column()
        col.prop(scene, "layers", text="Scene")

        rm = scene.renderman
        rm_rl = None
        active_layer = context.view_layer
        for l in rm.render_layers:
            if l.render_layer == active_layer.name:
                rm_rl = l
                break
        if rm_rl is None:
            return
            # layout.operator('renderman.add_pass_list')
        else:
            split = layout.split()
            col = split.column()
            # cutting this for now until we can export multiple cameras
            # col.prop_search(rm_rl, 'camera', bpy.data, 'cameras')
            col.prop_search(rm_rl, 'light_group',
                            scene.renderman, 'light_groups')
            col.prop_search(rm_rl, 'object_group',
                            scene.renderman, 'object_groups')

            col.prop(rm_rl, "denoise_aov")
            col.prop(rm_rl, 'export_multilayer')
            if rm_rl.export_multilayer:
                col.prop(rm_rl, 'use_deep')
                col.prop(rm_rl, "exr_format_options")
                col.prop(rm_rl, "exr_compression")
                col.prop(rm_rl, "exr_storage")


# class RENDER_PT_layer_passes(PRManButtonsPanel, Panel):
#     bl_label = "Passes"
#     bl_context = "render_layer"
#     # bl_options = {'DEFAULT_CLOSED'}

#     def draw(self, context):
#         layout = self.layout

#         scene = context.scene
#         rd = scene.render
#         rl = rd.layers.active
#         rm = rl.renderman

#         layout.prop(rm, "combine_outputs")
#         split = layout.split()

        # col = split.column()
        # col.prop(rl, "use_pass_combined")
        # col.prop(rl, "use_pass_z")
        # col.prop(rl, "use_pass_normal")
        # col.prop(rl, "use_pass_vector")
        # col.prop(rl, "use_pass_uv")
        # col.prop(rl, "use_pass_object_index")
        # #col.prop(rl, "use_pass_shadow")
        # #col.prop(rl, "use_pass_reflection")

        # col = split.column()
        # col.label(text="Diffuse:")
        # row = col.row(align=True)
        # row.prop(rl, "use_pass_diffuse_direct", text="Direct", toggle=True)
        # row.prop(rl, "use_pass_diffuse_indirect", text="Indirect", toggle=True)
        # row.prop(rl, "use_pass_diffuse_color", text="Albedo", toggle=True)
        # col.label(text="Specular:")
        # row = col.row(align=True)
        # row.prop(rl, "use_pass_glossy_direct", text="Direct", toggle=True)
        # row.prop(rl, "use_pass_glossy_indirect", text="Indirect", toggle=True)

        # col.prop(rl, "use_pass_subsurface_indirect", text="Subsurface")
        # col.prop(rl, "use_pass_refraction", text="Refraction")
        # col.prop(rl, "use_pass_emit", text="Emission")

        # layout.separator()
        # row = layout.row()
        # row.label('Holdouts')
        # rm = scene.renderman.holdout_settings
        # layout.prop(rm, 'do_collector_shadow')
        # layout.prop(rm, 'do_collector_reflection')
        # layout.prop(rm, 'do_collector_refraction')
        # layout.prop(rm, 'do_collector_indirectdiffuse')
        # layout.prop(rm, 'do_collector_subsurface')

        # col.prop(rl, "use_pass_ambient_occlusion")


class DATA_PT_renderman_camera(ShaderPanel, Panel):
    bl_context = "data"
    bl_label = "RenderMan Camera"

    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        if not context.camera:
            return False
        return rd.engine == 'PRMAN_RENDER'

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        cam = context.camera
        scene = context.scene
        col = layout.column()

        col.prop(cam.dof, "use_dof")
        col = layout.column()
        col.enabled = cam.dof.use_dof
        col.prop(cam.dof, "aperture_fstop")
        col = layout.column()
        col.prop(cam.dof, "focus_object")
        col = layout.column()
        col.active = (cam.dof.focus_object is None)
        col.prop(cam.dof, "focus_distance", text="Distance")
        col = layout.column(align = True)

        col.label(text="Aperture Controls:")
        col.prop(cam.dof, "aperture_ratio", text="Ratio")
        col.prop(cam.dof, "aperture_blades", text="Blades")
        col.prop(cam.dof, "aperture_rotation", text="Rotation")
        col.prop(cam.renderman, "aperture_roundness", text="Roundness")
        col.prop(cam.renderman, "aperture_density", text="Density")

        layout.prop(cam.renderman, "projection_type")
        if cam.renderman.projection_type != 'none':
            projection_node = cam.renderman.get_projection_node()
            draw_properties(projection_node, projection_node.prop_names, self)

    draw_subpanel("camera")

class DATA_PT_renderman_world(ShaderPanel, Panel):
    bl_context = "world"
    bl_label = "World"
    shader_type = 'world'

    def draw(self, context):
        layout = self.layout
        layout.use_property_decorate = False

        world = context.scene.world

        """
        DISABLE FOR NOW

        if not world.renderman.use_renderman_node:
            #FIXME layout.prop(world, "horizon_color")
            layout.prop(world, 'color')
            layout.operator('shading.add_renderman_nodetree').idtype = 'world'
            return
        else:
            layout.prop(world.renderman, "renderman_type", expand=True)
            layout.use_property_split = True
            if world.renderman.renderman_type == 'NONE':
                return
            layout.prop(world.renderman, 'light_primary_visibility')
            light_node = world.renderman.get_light_node()
            if light_node:
                draw_props(light_node, light_node.prop_names, layout)
        """

class DATA_PT_renderman_light(ShaderPanel, Panel):
    bl_context = "data"
    bl_label = "Light"
    shader_type = 'light'

    def draw(self, context):
        layout = self.layout

        light = context.light
        ipr_running = False
        if not light.renderman.use_renderman_node:
            layout.prop(light, "type", expand=True)
            layout.operator('shading.add_renderman_nodetree').idtype = 'light'
            #layout.operator('shading.convert_cycles_stuff')
            return
        else:
            layout.use_property_decorate = False
            layout.use_property_split = True
            if ipr_running:
                layout.label(text="Note: Some items cannot be edited while IPR running.")
            row = layout.row()
            row.enabled = not ipr_running
            row.prop(light.renderman, "renderman_type")
            if light.renderman.renderman_type == 'FILTER':
                row = layout.row()
                row.enabled = not ipr_running
                row.prop(light.renderman, "filter_type")
            if light.renderman.renderman_type == "AREA":
                col = layout.column()
                col.enabled = not ipr_running
                col.prop(light.renderman, "area_shape")
                if light.renderman.area_shape == "rect":
                    col.prop(light, 'size', text="Size X")
                    col.prop(light, 'size_y')
                else:
                    col.prop(light, 'size', text="Diameter")
            # layout.prop(light.renderman, "shadingrate")

        # layout.prop_search(light.renderman, "nodetree", bpy.data, "node_groups")
        col = layout.column()
        col.enabled = not ipr_running
        col.prop(light.renderman, 'illuminates_by_default')
        if light.renderman.renderman_type != 'FILTER':
            layout.prop(light.renderman, 'light_primary_visibility')

    draw_subpanel("light")

class DATA_PT_renderman_display_filters(CollectionPanel, Panel):
    bl_label = "Display Filters"
    bl_context = 'scene'
    bl_options = {'DEFAULT_CLOSED'}

    def draw_item(self, layout, context, item):
        layout.prop(item, 'filter_type')
        layout.separator()
        filter_node = item.get_filter_node()
        draw_properties(filter_node, filter_node.prop_names, self)

    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        return rd.engine == 'PRMAN_RENDER'

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        scene = context.scene
        rm = scene.renderman

        self._draw_collection(context, layout, rm, "Display Filters:",
                              "collection.add_remove", "scene", "display_filters",
                              "display_filters_index")


class DATA_PT_renderman_Sample_filters(CollectionPanel, Panel):
    bl_label = "Sample Filters"
    bl_context = 'scene'
    bl_options = {'DEFAULT_CLOSED'}

    def draw_item(self, layout, context, item):
        scene = context.scene
        rm = scene.renderman
        layout.prop(item, 'filter_type')
        filter_node = item.get_filter_node()
        draw_properties(filter_node, filter_node.prop_names, self)
        if rm.sample_filters[0].filter_type == "PxrWatermarkFilter":
            layout.label(text="TxMake Options:")
            draw_properties(filter_node, filter_node.prop_names, self, "subpanel")

    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        return rd.engine == 'PRMAN_RENDER'

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        scene = context.scene
        rm = scene.renderman

        self._draw_collection(context, layout, rm, "Sample Filters:",
                              "collection.add_remove", "scene", "sample_filters",
                              "sample_filters_index")


class DATA_PT_renderman_node_filters_light(CollectionPanel, Panel):
    bl_label = "Light Filters"
    bl_context = 'data'
    bl_options = {'DEFAULT_CLOSED'}

    def draw_item(self, layout, context, item):
        layout.prop(item, 'filter_name')

    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        return rd.engine == 'PRMAN_RENDER' and hasattr(context, "light") \
            and context.light is not None and hasattr(context.light, 'renderman') \
            and context.light.renderman.renderman_type != 'FILTER'

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        light = context.light

        self._draw_collection(context, layout, light.renderman, "",
                              "collection.add_remove", "light", "light_filters",
                              "light_filters_index")


class OBJECT_PT_renderman_object_geometry(Panel, CollectionPanel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    bl_label = "RenderMan Geometry"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        if context.object.type in ['CAMERA', 'LIGHT']:
            return False
        return (context.object and rd.engine in {'PRMAN_RENDER'})

    def draw_item(self, layout, context, item):
        col = layout.column()
        col.prop(item, "name")
        col.prop(item, "type")

    def draw(self, context):
        self.layout.use_property_split = True
        self.layout.use_property_decorate = False

        layout = self.layout
        ob = context.object
        rm = ob.renderman
        anim = rm.archive_anim_settings
        active = context.active_object

        rman_render = RmanRender.get_rman_render()
        rman_interactive_running = rman_render.rman_interactive_running

        col = layout.column()
        col.prop(rm, "primitive")
        col = layout.column(align = True)

        if rm.primitive in ('ARCHIVE', 'DELAYED_LOAD_ARCHIVE'):
            col.prop(rm, "path_archive")

            col.prop(anim, "animated_sequence")
            if anim.animated_sequence:
                col = layout.column(align = True)
                col.prop(anim, "blender_start")
                col.prop(anim, "sequence_in")
                col.prop(anim, "sequence_out")

        elif rm.primitive == 'PROCEDURAL_RUN_PROGRAM':
            col.prop(rm, "path_runprogram")
            col.prop(rm, "path_runprogram_args")
        elif rm.primitive == 'DYNAMIC_LOAD_DSO':
            col.prop(rm, "path_dso")
            col.prop(rm, "path_dso_initial_data")
        elif rm.primitive == 'OPENVDB':
            col.prop(rm, 'path_archive', text='OpenVDB file')
            self._draw_collection(context, layout, rm, "",
                                "collection.add_remove", "object.renderman",
                                "openvdb_channels", "openvdb_channel_index")

        if rm.primitive in ('DELAYED_LOAD_ARCHIVE',
                                'PROCEDURAL_RUN_PROGRAM',
                                'DYNAMIC_LOAD_DSO',
                                'OPENVDB'):
            col = layout.column()
            col.prop(rm, "procedural_bounds")

            if rm.procedural_bounds == 'MANUAL':
                col = layout.column()
                col.prop(rm, "procedural_bounds_min")
                col.prop(rm, "procedural_bounds_max")

        if rm.primitive in ('CONE', 'DISK'):
            col.prop(rm, "primitive_height")
        if rm.primitive in ('SPHERE', 'CYLINDER', 'CONE', 'DISK'):
            col.prop(rm, "primitive_radius")
        if rm.primitive == 'TORUS':
            col.prop(rm, "primitive_majorradius")
            col.prop(rm, "primitive_minorradius")
            col.prop(rm, "primitive_phimin")
            col.prop(rm, "primitive_phimax")
        if rm.primitive in ('SPHERE', 'CYLINDER', 'CONE', 'TORUS'):
            col.prop(rm, "primitive_sweepangle")
        if rm.primitive in ('SPHERE', 'CYLINDER'):
            col.prop(rm, "primitive_zmin")
            col.prop(rm, "primitive_zmax")
        if rm.primitive == 'POINTS':
            col.prop(rm, "primitive_point_type")
            col.prop(rm, "primitive_point_width")


        """
        col = layout.column()
        col.prop(rm, "geometry_source")

        if rm.geometry_source in ('ARCHIVE', 'DELAYED_LOAD_ARCHIVE'):
            col.prop(rm, "path_archive")

            col.prop(anim, "animated_sequence")
            if anim.animated_sequence:
                col = layout.column(align = True)
                col.prop(anim, "blender_start")
                col.prop(anim, "sequence_in")
                col.prop(anim, "sequence_out")

        elif rm.geometry_source == 'PROCEDURAL_RUN_PROGRAM':
            col.prop(rm, "path_runprogram")
            col.prop(rm, "path_runprogram_args")
        elif rm.geometry_source == 'DYNAMIC_LOAD_DSO':
            col.prop(rm, "path_dso")
            col.prop(rm, "path_dso_initial_data")
        elif rm.geometry_source == 'OPENVDB':
            col.prop(rm, 'path_archive', text='OpenVDB file')
            self._draw_collection(context, layout, rm, "",
                                  "collection.add_remove", "object.renderman",
                                  "openvdb_channels", "openvdb_channel_index")

        if rm.geometry_source in ('DELAYED_LOAD_ARCHIVE',
                                  'PROCEDURAL_RUN_PROGRAM',
                                  'DYNAMIC_LOAD_DSO',
                                  'OPENVDB'):
            col = layout.column()
            col.prop(rm, "procedural_bounds")

            if rm.procedural_bounds == 'MANUAL':
                col = layout.column()
                col.prop(rm, "procedural_bounds_min")
                col.prop(rm, "procedural_bounds_max")

        if rm.geometry_source == 'BLENDER_SCENE_DATA':
            col.prop(rm, "primitive")

            col = layout.column(align = True)

            if rm.primitive in ('CONE', 'DISK'):
                col.prop(rm, "primitive_height")
            if rm.primitive in ('SPHERE', 'CYLINDER', 'CONE', 'DISK'):
                col.prop(rm, "primitive_radius")
            if rm.primitive == 'TORUS':
                col.prop(rm, "primitive_majorradius")
                col.prop(rm, "primitive_minorradius")
                col.prop(rm, "primitive_phimin")
                col.prop(rm, "primitive_phimax")
            if rm.primitive in ('SPHERE', 'CYLINDER', 'CONE', 'TORUS'):
                col.prop(rm, "primitive_sweepangle")
            if rm.primitive in ('SPHERE', 'CYLINDER'):
                col.prop(rm, "primitive_zmin")
                col.prop(rm, "primitive_zmax")
            if rm.primitive == 'POINTS':
                col.prop(rm, "primitive_point_type")
                col.prop(rm, "primitive_point_width")

            # col.prop(rm, "export_archive")
            # if rm.export_archive:
            #    col.prop(rm, "export_archive_path")

        """
        rman_archive = load_icons().get("archive_RIB")
        col = layout.column()
        col.enabled = not rman_interactive_running
        col.operator("export.export_rib_archive",
                     text="Export Object as RIB Archive.", icon_value=rman_archive.icon_id)


        col = layout.column()
        # col.prop(rm, "export_coordsys")

        col.prop(rm, "displacementbound", text="Displacement Bound")

        col.prop(rm, "motion_segments_override")
        col.active = rm.motion_segments_override
        col.prop(rm, "motion_segments")
        #col.prop(ob.rman, 'trace_displacements')

"""
class RendermanRibBoxPanel(_RManPanelHeader):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_label = "RIB Box"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        return (rd.engine in {'PRMAN_RENDER'})

    def draw_rib_boxes(self, layout, rib_box_names, item):
        rm = item.renderman
        for rib_box in rib_box_names:
            row = layout.row()
            row.prop_search(rm, rib_box, bpy.data, "texts")
            if getattr(item.renderman, rib_box) != '':
                text_name = getattr(item.renderman, rib_box)
                rib_box_string = bpy.data.texts.get(text_name)
                for line in rib_box_string.lines:
                    row = layout.row()
                    row.label(text=line.body)


class OBJECT_PT_renderman_rib_box(RendermanRibBoxPanel, Panel):
    bl_context = "object"
    bl_label = "Object RIB boxes"

    def draw(self, context):
        self.draw_rib_boxes(self.layout, ['pre_object_rib_box', 'post_object_rib_box'],
                            context.object)


class WORLD_PT_renderman_rib_box(RendermanRibBoxPanel, Panel):
    bl_context = "world"
    bl_label = "World RIB box"

    def draw(self, context):
        self.draw_rib_boxes(self.layout, ['world_rib_box'],
                            context.world)


class SCENE_PT_renderman_rib_box(RendermanRibBoxPanel, Panel):
    bl_context = "scene"
    bl_label = "Scene RIB box"

    def draw(self, context):
        self.draw_rib_boxes(self.layout, ['frame_rib_box'],
                            context.scene)
"""

class OBJECT_PT_renderman_object_render(CollectionPanel, Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    bl_label = "Shading and Visibility"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        if context.object.type == 'CAMERA':
            return False
        return (context.object and rd.engine in {'PRMAN_RENDER'})

    def draw_item(self, layout, context, item):
        ob = context.object
        rm = bpy.data.objects[ob.name].renderman
        ll = rm.light_linking
        index = rm.light_linking_index

        col = layout.column()
        col.prop(item, "group")
        col.prop(item, "mode")

    def draw(self, context):
        self.layout.use_property_split = True
        self.layout.use_property_decorate = False

        layout = self.layout
        ob = context.object
        rm = ob.renderman

        col = layout.column()
        row = col.row()
        row.prop(rm, "visibility_camera", text="Camera")
        row.prop(rm, "visibility_trace_indirect", text="Indirect")
        row = col.row()
        row.prop(rm, "visibility_trace_transmission", text="Transmission")
        row.prop(rm, "matte")
        row = col.row()
        col.prop(rm, "holdout")

        col.separator()

        col.prop(rm, 'shading_override')

        col = layout.column()
        col.enabled = rm.shading_override
        col.prop(rm, "watertight")
        col = layout.column(align = True)
        col.enabled = rm.shading_override
        col.prop(rm, "shadingrate")
        col.prop(rm, "geometric_approx_motion")
        col.prop(rm, "geometric_approx_focus")


class OBJECT_PT_renderman_object_raytracing(CollectionPanel, Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    bl_label = "Ray Tracing"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        if context.object.type == 'CAMERA':
            return False
        return (context.object and rd.engine in {'PRMAN_RENDER'})

    def draw_item(self, layout, context, item):
        col = layout.column()
        col.prop(item, "group")
        col.prop(item, "mode")

    def draw(self, context):
        self.layout.use_property_split = True
        self.layout.use_property_decorate = False

        layout = self.layout
        ob = context.object
        rm = ob.renderman

        col = layout.column()
        col.prop(rm, "raytrace_intersectpriority", text="Intersection Priority")
        col.prop(rm, "raytrace_ior")
        col.prop(rm, "raytrace_override", text="Override Default Ray Tracing")

        col = layout.column(align = True)
        col.enabled = rm.raytrace_override
        col.prop(rm, "raytrace_maxdiffusedepth", text="Max Diffuse Depth")
        col.prop(rm, "raytrace_maxspeculardepth", text="Max Specular Depth")
        col.prop(rm, "raytrace_pixel_variance")
        col = layout.column()
        col.enabled = rm.raytrace_override
        col.prop(rm, "raytrace_tracedisplacements", text="Trace Displacements")
        col.prop(rm, "raytrace_autobias", text="Ray Origin Auto Bias")
        col = layout.column()
        col.active = not rm.raytrace_autobias
        col.enabled = rm.raytrace_override
        col.prop(rm, "raytrace_bias", text="Ray Origin Bias Amount")
        col = layout.column()
        col.enabled = rm.raytrace_override
        col.prop(rm, "raytrace_samplemotion", text="Sample Motion Blur")
        col.prop(rm, "raytrace_decimationrate", text="Decimation Rate")


class OBJECT_PT_renderman_object_matteid(Panel, _RManPanelHeader):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    bl_label = "Matte ID"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        if context.object.type == 'CAMERA':
            return False
        return (context.object and rd.engine in {'PRMAN_RENDER'})

    def draw(self, context):
        self.layout.use_property_split = True
        self.layout.use_property_decorate = False

        layout = self.layout
        ob = context.object
        rm = ob.renderman

        col = layout.column()
        col.prop(rm, 'MatteID0')
        col.prop(rm, 'MatteID1')
        col.prop(rm, 'MatteID2')
        col.prop(rm, 'MatteID3')
        col.prop(rm, 'MatteID4')
        col.prop(rm, 'MatteID5')
        col.prop(rm, 'MatteID6')
        col.prop(rm, 'MatteID7')


class RENDER_PT_layer_custom_aovs(CollectionPanel, Panel):
    bl_label = "Passes"
    bl_context = "view_layer"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'

    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        return rd.engine in {'PRMAN_RENDER'}

    def draw_item(self, layout, context, item):
        scene = context.scene
        rm = scene.renderman
        # ll = rm.light_linking
        # row = layout.row()
        # row.prop(item, "layers")

        col = layout.column()
        col.label(text=item.name)
        row = col.row()
        row.prop(item, "aov_display_driver")
        row = col.row()
        row.label(text="Channels")
        row = col.row()
        row.template_list("UI_UL_list", "PRMAN", item, "dspy_channels", item,
                          "dspy_channels_index", rows=1)

        if item.dspy_channels_index < 0:
            return

        channel = item.dspy_channels[item.dspy_channels_index]

        col = layout.column()
        col.prop(channel, "aov_name")
        if channel.aov_name == "color custom_lpe":
            col.prop(channel, "name")
            col.prop(channel, "custom_lpe_string")

        col = layout.column()
        icon = 'DISCLOSURE_TRI_DOWN' if channel.show_advanced \
            else 'DISCLOSURE_TRI_RIGHT'

        row = col.row()
        row.prop(channel, "show_advanced", icon=icon, text="Advanced",
                 emboss=False)
        if channel.show_advanced:
            col.label(text="Exposure Settings")
            col.prop(channel, "exposure_gain")
            col.prop(channel, "exposure_gamma")

            col = layout.column()
            col.label(text="Remap Settings")
            row = col.row(align=True)
            row.prop(channel, "remap_a", text="A")
            row.prop(channel, "remap_b", text="B")
            row.prop(channel, "remap_c", text="C")
            layout.separator()
            row = col.row()
            row.label(text="Quantize Settings:")
            row = col.row(align=True)
            row.prop(channel, "quantize_zero")
            row.prop(channel, "quantize_one")
            row.prop(channel, "quantize_min")
            row.prop(channel, "quantize_max")
            row = col.row()
            row.prop(channel, "aov_pixelfilter")
            row = col.row()
            if channel.aov_pixelfilter != 'default':
                row.prop(channel, "aov_pixelfilter_x", text="Size X")
                row.prop(channel, "aov_pixelfilter_y", text="Size Y")
            layout.separator()
            row = col.row()
            row.prop(channel, "stats_type")
            layout.separator()

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        rm = scene.renderman
        rm_rl = None
        active_layer = context.view_layer
        for l in rm.render_layers:
            if l.render_layer == active_layer.name:
                rm_rl = l
                break
        if rm_rl is None:
            layout.operator('renderman.add_renderman_aovs')
            split = layout.split()
            col = split.column()
            rl = active_layer
            #col.prop(rl, "use_metadata")
            col.prop(rl, "use_pass_combined")
            col.prop(rl, "use_pass_z")
            col.prop(rl, "use_pass_normal")
            col.prop(rl, "use_pass_vector")
            col.prop(rl, "use_pass_uv")
            col.prop(rl, "use_pass_object_index")
            # col.prop(rl, "use_pass_shadow")
            # col.prop(rl, "use_pass_reflection")

            col = split.column()
            col.label(text="Diffuse:")
            row = col.row(align=True)
            row.prop(rl, "use_pass_diffuse_direct", text="Direct", toggle=True)
            row.prop(rl, "use_pass_diffuse_indirect",
                     text="Indirect", toggle=True)
            row.prop(rl, "use_pass_diffuse_color", text="Albedo", toggle=True)
            col.label(text="Specular:")
            row = col.row(align=True)
            row.prop(rl, "use_pass_glossy_direct", text="Direct", toggle=True)
            row.prop(rl, "use_pass_glossy_indirect",
                     text="Indirect", toggle=True)

            col.prop(rl, "use_pass_subsurface_indirect", text="Subsurface")
            #col.prop(rl, "use_pass_refraction", text="Refraction")
            col.prop(rl, "use_pass_emit", text="Emission")

            # layout.separator()
            # row = layout.row()
            # row.label('Holdouts')
            # rm = scene.renderman.holdout_settings
            # layout.prop(rm, 'do_collector_shadow')
            # layout.prop(rm, 'do_collector_reflection')
            # layout.prop(rm, 'do_collector_refraction')
            # layout.prop(rm, 'do_collector_indirectdiffuse')
            # layout.prop(rm, 'do_collector_subsurface')

            col.prop(rl, "use_pass_ambient_occlusion")
        else:
            layout.context_pointer_set("pass_list", rm_rl)
            self._draw_collection(context, layout, rm_rl, "",
                                  "collection.add_remove", "pass_list",
                                  "custom_aovs", "custom_aov_index")


class PARTICLE_PT_renderman_particle(ParticleButtonsPanel, Panel, _RManPanelHeader):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "particle"
    bl_label = "Render"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        # XXX todo: handle strands properly

        psys = context.particle_system
        rm = psys.settings.renderman

        col = layout.column()
        row = col.row()
        row.use_property_split = False

        if psys.settings.type == 'EMITTER':
            row.row().prop(rm, "particle_type", expand=True)
            if rm.particle_type == 'OBJECT':
                col.prop_search(rm, "particle_instance_object", bpy.data,
                                "objects", text="")
                col.prop(rm, 'use_object_material')
            elif rm.particle_type == 'GROUP':
                col.prop_search(rm, "particle_instance_object", bpy.data,
                                "groups", text="")

            if rm.particle_type == 'OBJECT' and rm.use_object_material:
                pass
            else:
                col.prop(psys.settings, "material_slot")
            col.row().prop(rm, "constant_width", text="Override Width")
            col.row().prop(rm, "width")

        else:
            col.prop(psys.settings, "material_slot")

        # XXX: if rm.type in ('sphere', 'disc', 'patch'):
        # implement patchaspectratio and patchrotation

        split = layout.split()
        col = split.column()

        if psys.settings.type == 'HAIR':
            #row = col.row()
            #row.prop(psys.settings.cycles, "root_width", text='Root Width')
            #row.prop(psys.settings.cycles, "tip_width", text='Tip Width')
            #row = col.row()
            #row.prop(psys.settings.cycles, "radius_scale", text='Width Multiplier')

            col.prop(rm, 'export_scalp_st')
            col.prop(rm, 'round_hair')


class PARTICLE_PT_renderman_prim_vars(CollectionPanel, Panel):
    bl_context = "particle"
    bl_label = "Primitive Variables"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_item(self, layout, context, item):
        ob = context.object
        layout.prop(item, "name")

        row = layout.row()
        row.prop(item, "data_source", text="Source")

    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        if not context.particle_system:
            return False
        return rd.engine == 'PRMAN_RENDER'

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        psys = context.particle_system
        rm = psys.settings.renderman

        self._draw_collection(context, layout, rm, "Primitive Variables:",
                              "collection.add_remove",
                              "particle_system.settings",
                              "prim_vars", "prim_vars_index")

        layout.prop(rm, "export_default_size")

# headers to draw the interactive start/stop buttons


class PRMAN_HT_DrawRenderHeaderInfo(bpy.types.Header):
    bl_space_type = "INFO"

    def draw(self, context):
        if context.scene.render.engine != "PRMAN_RENDER":
            return
        layout = self.layout
        icons = load_icons()
        rman_render = RmanRender.get_rman_render()
        is_rman_interactive_running = rman_render.rman_interactive_running

        if not is_rman_interactive_running:

            # Render
            row = layout.row(align=True)
            rman_render_icon = icons.get("render")
            row.operator("render.render", text="Render",
                        icon_value=rman_render_icon.icon_id)

            # IPR
            rman_rerender_controls = icons.get("start_ipr")
            row.operator('lighting.start_interactive', text="Start IPR",
                            icon_value=rman_rerender_controls.icon_id)

            # Batch Render
            rman_batch = icons.get("batch_render")
            row.operator("renderman.external_render",
                         text="External Render", icon_value=rman_batch.icon_id)

        else:
            row = layout.row(align=True)
            rman_rerender_controls = icons.get("stop_ipr")
            row.operator('lighting.stop_interactive', text="Stop IPR",
                            icon_value=rman_rerender_controls.icon_id)

class PRMAN_HT_DrawRenderHeaderNode(bpy.types.Header):
    bl_space_type = "NODE_EDITOR"

    def draw(self, context):
        if context.scene.render.engine != "PRMAN_RENDER":
            return
        layout = self.layout

        row = layout.row(align=True)

        if hasattr(context.space_data, 'id') and \
                type(context.space_data.id) == bpy.types.Material and \
                not is_renderman_nodetree(context.space_data.id):
            row.operator(
                'shading.add_renderman_nodetree', text="Convert to RenderMan").idtype = "node_editor"

        row.operator('nodes.new_bxdf')


class PRMAN_HT_DrawRenderHeaderImage(bpy.types.Header):
    bl_space_type = "IMAGE_EDITOR"

    def draw(self, context):
        if context.scene.render.engine != "PRMAN_RENDER":
            return
        layout = self.layout
        icons = load_icons()

        rman_render = RmanRender.get_rman_render()
        is_rman_interactive_running = rman_render.rman_interactive_running

        if not is_rman_interactive_running:

            # Render
            row = layout.row(align=True)
            rman_render_icon = icons.get("render")
            row.operator("render.render", text="Render",
                        icon_value=rman_render_icon.icon_id)

            # IPR
            rman_rerender_controls = icons.get("start_ipr")
            row.operator('lighting.start_interactive', text="Start IPR",
                            icon_value=rman_rerender_controls.icon_id)

        else:
            row = layout.row(align=True)
            rman_rerender_controls = icons.get("stop_ipr")
            row.operator('lighting.stop_interactive', text="Stop IPR",
                            icon_value=rman_rerender_controls.icon_id)


def PRMan_menu_func(self, context):
    if context.scene.render.engine != "PRMAN_RENDER":
        return
    self.layout.separator()

    rman_render = RmanRender.get_rman_render()
    is_rman_interactive_running = rman_render.rman_interactive_running

    if not is_rman_interactive_running:
        self.layout.operator('lighting.start_interactive',
                            text="RenderMan Start Interactive Rendering")
    else:
        self.layout.operator('lighting.stop_interactive',
                            text="RenderMan Stop Interactive Rendering")

#################
#       Tab     #
#################
class PRMAN_PT_Renderman_Light_Panel(CollectionPanel, Panel):
    # bl_idname = "renderman_light_panel"
    bl_label = "RenderMan Light Groups"
    bl_context = "scene"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'  # bl_category = "Renderman"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        rm = scene.renderman
        # if len(rm.light_groups) == 0:
        #    light_group = rm.object_groups.add()
        #    light_group.name = 'All'
        self._draw_collection(context, layout, rm, "",
                              "collection.add_remove",
                              "scene.renderman",
                              "light_groups", "light_groups_index", default_name=str(len(rm.light_groups)))

    def draw_item(self, layout, context, item):
        scene = context.scene
        rm = scene.renderman
        light_group = rm.light_groups[rm.light_groups_index]
        # row.template_list("RENDERMAN_GROUP_UL_List", "Renderman_light_group_list",
        #                    light_group, "members", light_group, 'members_index',
        #                    rows=9, maxrows=100, type='GRID', columns=9)

        row = layout.row()
        add = row.operator('renderman.add_to_group', text='Add Selected to Group')
        add.item_type = 'light'
        add.group_index = rm.light_groups_index

        # row = layout.row()
        remove = row.operator('renderman.remove_from_group',
                              text='Remove Selected from Group')
        remove.item_type = 'light'
        remove.group_index = rm.light_groups_index

        light_names = [member.name for member in light_group.members]
        if light_group.name == 'All':
            light_names = [
                light.name for light in context.scene.objects if light.type == 'LIGHT']

        if len(light_names) > 0:
            box = layout.box()
            row = box.row()
            columns = box.column_flow(columns=8)
            columns.label(text='Name')
            columns.label(text='Solo')
            columns.label(text='Mute')
            columns.label(text='Intensity')
            columns.label(text='Exposure')
            columns.label(text='Color')
            columns.label(text='Temperature')

            for light_name in light_names:
                if light_name not in scene.objects:
                    continue
                light = scene.objects[light_name].data
                light_rm = light.renderman
                if light_rm.renderman_type == 'FILTER':
                    continue
                row = box.row()
                columns = box.column_flow(columns=8)
                columns.label(text=light_name)
                columns.prop(light_rm, 'solo', text='')
                columns.prop(light_rm, 'mute', text='')
                light_shader = light.renderman.get_light_node()
                if light_shader:

                    columns.prop(light_shader, 'intensity', text='')
                    columns.prop(light_shader, 'exposure', text='')
                    if light_shader.bl_label == 'PxrEnvDayLight':
                        # columns.label('sun tint')
                        columns.prop(light_shader, 'skyTint', text='')
                        columns.label(text='')
                    else:
                        columns.prop(light_shader, 'lightColor', text='')
                        row = columns.row()
                        row.prop(light_shader, 'enableTemperature', text='')
                        row.prop(light_shader, 'temperature', text='')
                else:
                    columns.label(text='')
                    columns.label(text='')
                    columns.prop(light, 'energy', text='')
                    columns.prop(light, 'color', text='')
                    columns.label(text='')


class RENDERMAN_UL_LIGHT_list(bpy.types.UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        rm = context.scene.renderman
        icon = 'NONE'
        ll_prefix = "lg_%s>%s" % (rm.ll_light_type, item.name)
        label = item.name
        for ll in rm.ll.keys():
            if ll_prefix in ll:
                icon = 'TRIA_RIGHT'
                break

        layout.alignment = 'CENTER'
        layout.label(text=label, icon=icon)


class RENDERMAN_UL_OBJECT_list(bpy.types.UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        rm = context.scene.renderman
        icon = 'NONE'
        light_type = rm.ll_light_type
        lg = bpy.data.lights if light_type == "light" else rm.light_groups
        ll_prefix = "lg_%s>%s>obj_%s>%s" % (
            light_type, lg[rm.ll_light_index].name, rm.ll_object_type, item.name)

        label = item.name
        if ll_prefix in rm.ll.keys():
            ll = rm.ll[ll_prefix]
            if ll.illuminate == 'DEFAULT':
                icon = 'TRIA_RIGHT'
            elif ll.illuminate == 'ON':
                icon = 'DISCLOSURE_TRI_RIGHT'
            else:
                icon = 'DISCLOSURE_TRI_DOWN'

        layout.alignment = 'CENTER'
        layout.label(text=label, icon=icon)


class PRMAN_PT_Renderman_Light_Link_Panel(CollectionPanel, Panel):
    # bl_idname = "renderman_light_panel"
    bl_label = "RenderMan Light Linking"
    bl_context = "scene"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'  # bl_category = "Renderman"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        return rd.engine == 'PRMAN_RENDER'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        rm = scene.renderman
        row = layout.row()

        flow = row.column_flow(columns=3)
        # first colomn select Light
        flow.prop(rm, 'll_light_type')
        flow.prop(rm, 'll_object_type')
        flow.label(text='')

        # second row the selectors
        row = layout.row()
        flow = row.column_flow(columns=3)
        if rm.ll_light_type == 'light':
            flow.template_list("RENDERMAN_UL_LIGHT_list", "Renderman_light_link_list",
                               bpy.data, "lights", rm, 'll_light_index')
        else:
            flow.template_list("RENDERMAN_UL_LIGHT_list", "Renderman_light_link_list",
                               rm, "light_groups", rm, 'll_light_index')

        if rm.ll_object_type == 'object':
            flow.template_list("RENDERMAN_UL_OBJECT_list", "Renderman_light_link_list",
                               bpy.data, "objects", rm, 'll_object_index')
        else:
            flow.template_list("RENDERMAN_UL_OBJECT_list", "Renderman_light_link_list",
                               rm, "object_groups", rm, 'll_object_index')

        if rm.ll_light_index == -1 or rm.ll_object_index == -1:
            flow.label(text="Select light and object")
        else:
            from_name = bpy.data.lights[rm.ll_light_index] if rm.ll_light_type == 'light' \
                else rm.light_groups[rm.ll_light_index]
            to_name = bpy.data.objects[rm.ll_object_index] if rm.ll_object_type == 'object' \
                else rm.object_groups[rm.ll_object_index]
            ll_name = "lg_%s>%s>obj_%s>%s" % (rm.ll_light_type, from_name.name,
                                              rm.ll_object_type, to_name.name)

            col = flow.column()
            if ll_name in rm.ll:
                col.prop(rm.ll[ll_name], 'illuminate')
                rem = col.operator(
                    'renderman.add_rem_light_link', text='Remove Light Link')
                rem.ll_name = ll_name
                rem.add_remove = "remove"
            else:
                add = col.operator(
                    'renderman.add_rem_light_link', text='Add Light Link')
                add.ll_name = ll_name
                add.add_remove = 'add'


class RENDERMAN_GROUP_UL_List(bpy.types.UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):

        # We could write some code to decide which icon to use here...
        custom_icon = 'OBJECT_DATAMODE'
        # Make sure your code supports all 3 layout types
        layout.alignment = 'CENTER'
        layout.label(text=item.name, icon=custom_icon)


class PRMAN_PT_Renderman_Object_Panel(CollectionPanel, Panel):
    #bl_idname = "renderman_object_groups_panel"
    bl_label = "RenderMan Object Groups"
    bl_context = "scene"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'  # bl_category = "Renderman"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        return rd.engine == 'PRMAN_RENDER'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        rm = scene.renderman
        # if len(rm.object_groups) == 0:
        #    collector_group = rm.object_groups.add()
        #    collector_group.name = 'collector'

        self._draw_collection(context, layout, rm, "",
                              "collection.add_remove",
                              "scene.renderman",
                              "object_groups", "object_groups_index",
                              default_name=str(len(rm.object_groups)))

    def draw_item(self, layout, context, item):
        row = layout.row()
        scene = context.scene
        rm = scene.renderman
        group = rm.object_groups[rm.object_groups_index]

        row = layout.row()
        row.operator('renderman.add_to_group',
                     text='Add Selected to Group').group_index = rm.object_groups_index
        row.operator('renderman.remove_from_group',
                     text='Remove Selected from Group').group_index = rm.object_groups_index

        row = layout.row()
        row.template_list("RENDERMAN_GROUP_UL_List", "Renderman_group_list",
                          group, "members", group, 'members_index',
                          item_dyntip_propname='name',
                          type='GRID', columns=3)


class PRMAN_PT_Renderman_UI_Panel(bpy.types.Panel, _RManPanelHeader):
    #bl_idname = "renderman_ui_panel"
    bl_label = "RenderMan"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Renderman"

    def draw(self, context):
        icons = load_icons()
        layout = self.layout
        scene = context.scene
        rm = scene.renderman

        # save Scene
        # layout.operator("wm.save_mainfile", text="Save Scene", icon='FILE_TICK')

        # layout.separator()

        if context.scene.render.engine != "PRMAN_RENDER":
            return

        # Render
        rman_render = RmanRender.get_rman_render()
        is_rman_interactive_running = rman_render.rman_interactive_running

        if not is_rman_interactive_running:

            row = layout.row(align=True)
            rman_render_icon = icons.get("render")
            row.operator("render.render", text="Render",
                        icon_value=rman_render_icon.icon_id)

            row.prop(context.scene, "rm_render", text="",
                    icon='DISCLOSURE_TRI_DOWN' if context.scene.rm_render else 'DISCLOSURE_TRI_RIGHT')

            if context.scene.rm_render:
                scene = context.scene
                rd = scene.render

                box = layout.box()
                row = box.row(align=True)

                # Display Driver
                row.prop(rm, "render_into")

                # presets
                row = box.row(align=True)
                row.label(text="Sampling Preset:")
                row.menu("PRMAN_MT_presets", text=bpy.types.WM_MT_operator_presets.bl_label)
                row.operator("render.renderman_preset_add", text="", icon='ADD')
                row.operator("render.renderman_preset_add", text="",
                            icon='REMOVE').remove_active = True

                # denoise, holdouts and selected row
                row = box.row(align=True)
                #row.prop(rm, "do_denoise", text="Denoise")
                row.prop(rm, "do_holdout_matte", text="Render Holdouts")

                #row.prop(rm, "render_selected_objects_only",
                #         text="Render Selected")


                # animation
                row = box.row(align=True)
                rman_batch = icons.get("batch_render")
                row.operator("render.render", text="Render Animation",
                            icon_value=rman_batch.icon_id).animation = True

                # row = box.row(align=True)
                # rman_batch = icons.get("batch_render")
                # row.operator("render.render",text="Batch Render",icon_value=rman_batch.icon_id).animation=True

                # #Resolution
                # row = box.row(align=True)
                # sub = row.column(align=True)
                # sub.label(text="Resolution:")
                # sub.prop(rd, "resolution_x", text="X")
                # sub.prop(rd, "resolution_y", text="Y")
                # sub.prop(rd, "resolution_percentage", text="")

                # # layout.prop(rm, "display_driver")
                # #Sampling
                # row = box.row(align=True)
                # row.label(text="Sampling:")
                # row = box.row(align=True)
                # col = row.column()
                # col.prop(rm, "pixel_variance")
                # row = col.row(align=True)
                # row.prop(rm, "min_samples", text="Min Samples")
                # row.prop(rm, "max_samples", text="Max Samples")
                # row = col.row(align=True)
                # row.prop(rm, "max_specular_depth", text="Specular Depth")
                # row.prop(rm, "max_diffuse_depth", text="Diffuse Depth")

            # IPR

            # Start IPR

            row = layout.row(align=True)
            rman_rerender_controls = icons.get("start_ipr")
            row.operator('lighting.start_interactive', text="Start IPR",
                            icon_value=rman_rerender_controls.icon_id)

            row.prop(context.scene, "rm_ipr", text="",
                        icon='DISCLOSURE_TRI_DOWN' if context.scene.rm_ipr else 'DISCLOSURE_TRI_RIGHT')


            if context.scene.rm_ipr:

                scene = context.scene
                rm = scene.renderman

                # STart IT
                rman_it = icons.get("start_it")
                layout.operator("rman.start_it", text="Start IT",
                                icon_value=rman_it.icon_id)

                # Interactive and Preview Sampling
                box = layout.box()
                row = box.row(align=True)

                col = row.column()
                col.prop(rm, "preview_pixel_variance")
                row = col.row(align=True)
                row.prop(rm, "preview_min_samples", text="Min Samples")
                row.prop(rm, "preview_max_samples", text="Max Samples")
                row = col.row(align=True)
                row.prop(rm, "preview_max_specular_depth",
                            text="Specular Depth")
                row.prop(rm, "preview_max_diffuse_depth", text="Diffuse Depth")
                row = col.row(align=True)

            row = layout.row(align=True)
            rman_batch = icons.get("batch_render")

            row.operator("renderman.external_render",
                        text="External Render", icon_value=rman_batch.icon_id)

            row.prop(context.scene, "rm_render_external", text="",
                    icon='DISCLOSURE_TRI_DOWN' if context.scene.rm_render_external else 'DISCLOSURE_TRI_RIGHT')
            if context.scene.rm_render_external:
                scene = context.scene
                rd = scene.render

                box = layout.box()
                row = box.row(align=True)

                # Display Driver
                row.prop(rm, "display_driver", text='Render into')

                # animation
                row = box.row(align=True)
                row.prop(rm, "external_animation")

                row = box.row(align=True)
                row.enabled = rm.external_animation
                row.prop(scene, "frame_start", text="Start")
                row.prop(scene, "frame_end", text="End")

                # presets
                row = box.row(align=True)
                row.label(text="Sampling Preset:")
                row.menu("PRMAN_MT_presets")

                #row = box.row(align=True)
                #row.prop(rm, "render_selected_objects_only",
                #        text="Render Selected")

                # spool render
                row = box.row(align=True)
                col = row.column()
                col.prop(rm, "queuing_system", text='')

        else:
            row = layout.row(align=True)
            rman_rerender_controls = icons.get("stop_ipr")
            row.operator('lighting.stop_interactive', text="Stop IPR",
                            icon_value=rman_rerender_controls.icon_id)

        layout.separator()

        # Create Camera
        row = layout.row(align=True)
        row.operator("object.add_prm_camera",
                     text="Add Camera", icon='CAMERA_DATA')

        row.prop(context.scene, "prm_cam", text="",
                 icon='DISCLOSURE_TRI_DOWN' if context.scene.prm_cam else 'DISCLOSURE_TRI_RIGHT')

        if context.scene.prm_cam:
            ob = bpy.context.object
            box = layout.box()
            row = box.row(align=True)
            row.menu("PRMAN_MT_Camera_List_Menu",
                     text="Camera List", icon='CAMERA_DATA')

            if ob.type == 'CAMERA':

                row = box.row(align=True)
                row.prop(ob, "name", text="", icon='LIGHT_HEMI')
                row.prop(ob, "hide_viewport", text="")
                row.prop(ob, "hide_render",
                         icon='RESTRICT_RENDER_OFF', text="")
                row.operator("object.delete_cameras",
                             text="", icon='PANEL_CLOSE')

                row = box.row(align=True)
                row.scale_x = 2
                row.operator("view3d.object_as_camera", text="", icon='CURSOR')

                row.scale_x = 2
                row.operator("view3d.view_camera", text="", icon='VISIBLE_IPO_ON')

                if context.space_data.lock_camera == False:
                    row.scale_x = 2
                    row.operator("wm.context_toggle", text="",
                                 icon='UNLOCKED').data_path = "space_data.lock_camera"
                elif context.space_data.lock_camera == True:
                    row.scale_x = 2
                    row.operator("wm.context_toggle", text="",
                                 icon='LOCKED').data_path = "space_data.lock_camera"

                row.scale_x = 2
                row.operator("view3d.camera_to_view",
                             text="", icon='VIEW3D')

                row = box.row(align=True)
                row.label(text="Depth Of Field :")

                row = box.row(align=True)
                row.prop(context.object.data.dof, "focus_object", text="")
                #row.prop(context.object.data.cycles, "aperture_type", text="")

                row = box.row(align=True)
                row.prop(context.object.data.dof, "focus_distance", text="Distance")

            else:
                row = layout.row(align=True)
                row.label(text="No Camera Selected")

        layout.separator()

        # Create Env Light
        row = layout.row(align=True)
        rman_RMSEnvLight = icons.get("envlight")
        row.operator("object.mr_add_hemi", text="Add EnvLight",
                     icon_value=rman_RMSEnvLight.icon_id)

        lights = [obj for obj in bpy.context.scene.objects if obj.type == "LIGHT"]

        light_hemi = False
        light_area = False
        light_point = False
        light_spot = False
        light_sun = False

        if len(lights):
            for light in lights:
                if light.data.type == 'HEMI':
                    light_hemi = True

                if light.data.type == 'AREA':
                    light_area = True

                if light.data.type == 'POINT':
                    light_point = True

                if light.data.type == 'SPOT':
                    light_spot = True

                if light.data.type == 'SUN':
                    light_sun = True

        if light_hemi:

            row.prop(context.scene, "rm_env", text="",
                     icon='DISCLOSURE_TRI_DOWN' if context.scene.rm_env else 'DISCLOSURE_TRI_RIGHT')

            if context.scene.rm_env:
                ob = bpy.context.object
                box = layout.box()
                row = box.row(align=True)
                row.menu("PRMAN_MT_Hemi_List_Menu",
                         text="EnvLight List", icon='LIGHT_HEMI')

                if ob.type == 'LIGHT' and ob.data.type == 'HEMI':

                    row = box.row(align=True)
                    row.prop(ob, "name", text="", icon='LIGHT_HEMI')
                    row.prop(ob, "hide_viewport", text="")
                    row.prop(ob, "hide_render",
                             icon='RESTRICT_RENDER_OFF', text="")
                    row.operator("object.delete_lights",
                                 text="", icon='PANEL_CLOSE')
                    row = box.row(align=True)
                    row.prop(ob, "rotation_euler", index=2, text="Rotation")

                else:
                    row = layout.row(align=True)
                    row.label(text="No EnvLight Selected")

        # Create Area Light

        row = layout.row(align=True)
        rman_RMSAreaLight = icons.get("arealight")
        row.operator("object.mr_add_area", text="Add AreaLight",
                     icon_value=rman_RMSAreaLight.icon_id)

        lights = [obj for obj in bpy.context.scene.objects if obj.type == "LIGHT"]

        light_hemi = False
        light_area = False
        light_point = False
        light_spot = False
        light_sun = False

        if len(lights):
            for light in lights:
                if light.data.type == 'HEMI':
                    light_hemi = True

                if light.data.type == 'AREA':
                    light_area = True

                if light.data.type == 'POINT':
                    light_point = True

                if light.data.type == 'SPOT':
                    light_spot = True

                if light.data.type == 'SUN':
                    light_sun = True

        if light_area:

            row.prop(context.scene, "rm_area", text="",
                     icon='DISCLOSURE_TRI_DOWN' if context.scene.rm_area else 'DISCLOSURE_TRI_RIGHT')

            if context.scene.rm_area:
                ob = bpy.context.object
                box = layout.box()
                row = box.row(align=True)
                row.menu("PRMAN_MT_Area_List_Menu",
                         text="AreaLight List", icon='LIGHT_AREA')

                if ob.type == 'LIGHT' and ob.data.type == 'AREA':

                    row = box.row(align=True)
                    row.prop(ob, "name", text="", icon='LIGHT_AREA')
                    row.prop(ob, "hide_viewport", text="")
                    row.prop(ob, "hide_render",
                             icon='RESTRICT_RENDER_OFF', text="")
                    row.operator("object.delete_lights",
                                 text="", icon='PANEL_CLOSE')

                else:
                    row = layout.row(align=True)
                    row.label(text="No AreaLight Selected")

        # Daylight

        row = layout.row(align=True)
        rman_PxrStdEnvDayLight = icons.get("daylight")
        row.operator("object.mr_add_sky", text="Add Daylight",
                     icon_value=rman_PxrStdEnvDayLight.icon_id)

        lights = [obj for obj in bpy.context.scene.objects if obj.type == "LIGHT"]

        light_hemi = False
        light_area = False
        light_point = False
        light_spot = False
        light_sun = False

        if len(lights):
            for light in lights:
                if light.data.type == 'SUN':
                    light_sun = True

                if light.data.type == 'HEMI':
                    light_hemi = True

                if light.data.type == 'AREA':
                    light_area = True

                if light.data.type == 'POINT':
                    light_point = True

                if light.data.type == 'SPOT':
                    light_spot = True

        if light_sun:

            row.prop(context.scene, "rm_daylight", text="",
                     icon='DISCLOSURE_TRI_DOWN' if context.scene.rm_daylight else 'DISCLOSURE_TRI_RIGHT')

            if context.scene.rm_daylight:
                ob = bpy.context.object
                box = layout.box()
                row = box.row(align=True)
                row.menu("PRMAN_MT_DayLight_List_Menu",
                         text="DayLight List", icon='LIGHT_SUN')

                if ob.type == 'LIGHT' and ob.data.type == 'SUN':

                    row = box.row(align=True)
                    row.prop(ob, "name", text="", icon='LIGHT_SUN')
                    row.prop(ob, "hide_viewport", text="")
                    row.prop(ob, "hide_render",
                             icon='RESTRICT_RENDER_OFF', text="")
                    row.operator("object.delete_lights",
                                 text="", icon='PANEL_CLOSE')

                else:
                    row = layout.row(align=True)
                    row.label(text="No DayLight Selected")

        # Dynamic Binding Editor

        # Create Holdout

        # Open Linking Panel
        # row = layout.row(align=True)
        # row.operator("renderman.lighting_panel")

        selected_objects = []
        if context.selected_objects:
            for obj in context.selected_objects:
                if obj.type not in ['CAMERA', 'LIGHT', 'SPEAKER']:
                    selected_objects.append(obj)

        if selected_objects:
            layout.separator()
            layout.label(text="Seleced Objects:")
            box = layout.box()

            # Create PxrLM Material
            render_PxrDisney = icons.get("pxrdisney")
            box.operator_menu_enum(
                "object.add_bxdf", 'bxdf_name', text="Add New Material", icon='MATERIAL')

            # Make Selected Geo Emissive∂
            rman_RMSGeoAreaLight = icons.get("geoarealight")
            box.operator("object.addgeoarealight", text="Make Emissive",
                         icon_value=rman_RMSGeoAreaLight.icon_id)

            # Add Subdiv Sheme
            rman_subdiv = icons.get("add_subdiv_sheme")
            box.operator("object.add_subdiv_sheme",
                         text="Make Subdiv", icon_value=rman_subdiv.icon_id)

            # Add/Create RIB Box /
            # Create Archive node
            rman_archive = icons.get("archive_RIB")
            box.operator("export.export_rib_archive",
                         icon_value=rman_archive.icon_id)
        # Create Geo LightBlocker

        # Update Archive !! Not needed with current system.

        # Open Last RIB
        #rman_open_last_rib = icons.get("open_last_rib")
        #layout.prop(rm, "path_rib_output",icon_value=rman_open_last_rib.icon_id)

        # Inspect RIB Selection

        # Shared Geometry Attribute

        # Add/Atach Coordsys

        # Open Tmake Window  ?? Run Tmake on everything.

        # Create OpenVDB Visualizer
        layout.separator()
        # RenderMan Doc
        rman_help = icons.get("help")
        layout.operator("wm.url_open", text="RenderMan Docs",
                        icon_value=rman_help.icon_id).url = "https://github.com/prman-pixar/RenderManForBlender/wiki/Documentation-Home"
        rman_info = icons.get("info")
        layout.operator("wm.url_open", text="About RenderMan",
                        icon_value=rman_info.icon_id).url = "https://renderman.pixar.com/store/intro"

        # Reload the addon
        # rman_reload = icons.get("reload_plugin")
        # layout.operator("renderman.restartaddon", icon_value=rman_reload.icon_id)

        # Enable the menu item to display the examples menu in the RenderMan
        # Panel.
        layout.separator()
        layout.menu("PRMAN_MT_examples", icon_value=rman_help.icon_id)

class PRMAN_PT_context_material(_RManPanelHeader, Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_label = ""
    bl_context = "material"
    bl_options = {'HIDE_HEADER'}
    COMPAT_ENGINES = {'PRMAN_RENDER'}

    @classmethod
    def poll(cls, context):
        if context.active_object and context.active_object.type == 'GPENCIL':
            return False
        else:
            return (context.material or context.object) and _RManPanelHeader.poll(context)

    def draw(self, context):
        layout = self.layout

        mat = context.material
        ob = context.object
        slot = context.material_slot
        space = context.space_data

        if ob:
            is_sortable = len(ob.material_slots) > 1
            rows = 1
            if (is_sortable):
                rows = 4

            row = layout.row()

            row.template_list("MATERIAL_UL_matslots", "", ob, "material_slots", ob, "active_material_index", rows=rows)

            col = row.column(align=True)
            col.operator("object.material_slot_add", icon='ADD', text="")
            col.operator("object.material_slot_remove", icon='REMOVE', text="")

            col.menu("MATERIAL_MT_context_menu", icon='DOWNARROW_HLT', text="")

            if is_sortable:
                col.separator()

                col.operator("object.material_slot_move", icon='TRIA_UP', text="").direction = 'UP'
                col.operator("object.material_slot_move", icon='TRIA_DOWN', text="").direction = 'DOWN'

            if ob.mode == 'EDIT':
                row = layout.row(align=True)
                row.operator("object.material_slot_assign", text="Assign")
                row.operator("object.material_slot_select", text="Select")
                row.operator("object.material_slot_deselect", text="Deselect")

        split = layout.split(factor=0.65)

        if ob:
            split.template_ID(ob, "active_material", new="material.new")
            row = split.row()

            if slot:
                row.prop(slot, "link", text="")
            else:
                row.label()
        elif mat:
            split.template_ID(space, "pin_id")
            split.separator()

classes = [
    RENDER_PT_renderman_render,
    RENDER_PT_renderman_presets,
    RENDER_PT_renderman_sampling,
    RENDER_PT_renderman_sampling_preview,
    RENDER_PT_renderman_integrator,
    RENDER_PT_renderman_spooling,
    RENDER_PT_renderman_spooling_export_options,
    RENDER_PT_renderman_motion_blur,
    RENDER_PT_renderman_baking,
    RENDER_PT_renderman_advanced_settings,
    MESH_PT_renderman_prim_vars,
    MATERIAL_PT_renderman_preview,
    MATERIAL_PT_renderman_shader_surface,
    MATERIAL_PT_renderman_shader_light,
    MATERIAL_PT_renderman_shader_displacement,
    RENDER_PT_layer_options,
    DATA_PT_renderman_camera,
    DATA_PT_renderman_world,
    DATA_PT_renderman_light,
    DATA_PT_renderman_display_filters,
    DATA_PT_renderman_Sample_filters,
    DATA_PT_renderman_node_filters_light,
    OBJECT_PT_renderman_object_geometry,
    OBJECT_PT_renderman_object_render,
    OBJECT_PT_renderman_object_raytracing,
    OBJECT_PT_renderman_object_matteid,
    #RENDER_PT_layer_custom_aovs,
    PARTICLE_PT_renderman_particle,
    PARTICLE_PT_renderman_prim_vars,
    PRMAN_HT_DrawRenderHeaderInfo,
    PRMAN_HT_DrawRenderHeaderNode,
    PRMAN_HT_DrawRenderHeaderImage,
    PRMAN_PT_Renderman_Light_Panel,
    PRMAN_PT_Renderman_Light_Link_Panel,
    PRMAN_PT_Renderman_Object_Panel,
    PRMAN_PT_Renderman_UI_Panel,
    PRMAN_PT_context_material,
    ]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    for cls in subpanel_classes:
        bpy.utils.register_class(cls)

    bpy.utils.register_class(RENDERMAN_GROUP_UL_List)
    bpy.utils.register_class(RENDERMAN_UL_LIGHT_list)
    bpy.utils.register_class(RENDERMAN_UL_OBJECT_list)
    # bpy.utils.register_class(RENDERMAN_OUTPUT_list)
    # bpy.utils.register_class(RENDERMAN_CHANNEL_list)
    #bpy.types.TOPBAR_MT_render.append(PRMan_menu_func)

    for panel in get_panels():
        panel.COMPAT_ENGINES.add('PRMAN_RENDER')


def unregister():
    bpy.utils.unregister_class(RENDERMAN_GROUP_UL_List)
    bpy.utils.unregister_class(RENDERMAN_UL_LIGHT_list)
    bpy.utils.unregister_class(RENDERMAN_UL_OBJECT_list)
    # bpy.utils.register_class(RENDERMAN_OUTPUT_list)
    # bpy.utils.register_class(RENDERMAN_CHANNEL_list)
    #bpy.types.TOPBAR_MT_render.remove(PRMan_menu_func)

    for panel in get_panels():
        panel.COMPAT_ENGINES.remove('PRMAN_RENDER')

    for cls in subpanel_classes:
        bpy.utils.unregister_class(cls)

    for cls in classes:
        bpy.utils.unregister_class(cls)
