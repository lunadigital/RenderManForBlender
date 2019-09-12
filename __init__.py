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
import sys

bl_info = {
    "name": "RenderMan For Blender",
    "author": "Pixar",
    "version": (22, 6, 0),
    "blender": (2, 80, 0),
    "location": "Info Header, render engine menu",
    "description": "RenderMan 22.6 integration",
    "warning": "",
    "category": "Render"}


class PRManRender(bpy.types.RenderEngine):
    bl_idname = 'PRMAN_RENDER'
    bl_label = "RenderMan Render"
    bl_use_preview = True
    bl_use_save_buffers = True
    bl_use_shading_nodes = True
    bl_use_shading_nodes_custom = False

    def __init__(self):
        self.render_pass = None

    def __del__(self):
        if hasattr(self, "render_pass"):
            if self.render_pass is not None:
                engine.free(self)

    # main scene render
    def update(self, data, depsgraph):
        if(engine.ipr):
            return
        if self.is_preview:
            if not self.render_pass:
                engine.create(self, data, depsgraph)
        else:
            if not self.render_pass:
                engine.create(self, data, depsgraph)
            else:
                engine.reset(self, data, depsgraph)

        engine.update(self, data, depsgraph)

    def render(self, depsgraph):
        if engine.ipr:
            engine.ipr.scene = depsgraph.scene
            engine.ipr.depsgraph = depsgraph
            engine.ipr.start_interactive_sg()
        elif self.render_pass is not None:
            engine.render(self, depsgraph)


# these handlers are for marking files as dirty for ribgen
def add_handlers(scene):
    if engine.update_timestamp not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(engine.update_timestamp)
    if properties.initial_groups not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.load_post.append(properties.initial_groups)


def remove_handlers():
    if properties.initial_groups in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(properties.initial_groups)
    if engine.update_timestamp in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(engine.update_timestamp)


def load_addon():
    # if rmantree is ok load the stuff
    from .util import guess_rmantree, throw_error
    from . import preferences

    if guess_rmantree():
        # else display an error, tell user to correct
        # and don't load anything else
        from . import ui
        from . import properties
        from . import operators
        from . import nodes
        # need this now rather than at beginning to make
        # sure preferences are loaded
        from . import engine
        properties.register()
        operators.register()
        ui.register()
        add_handlers(None)
        nodes.register()

    else:
        # display loading error
        throw_error(
            "Error loading addon.  Correct RMANTREE setting in addon preferences.")

classes = [
    PRManRender,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    from . import presets
    presets.register()
    from . import preferences
    preferences.register()
    load_addon()



def unregister():
    from . import preferences
    remove_handlers()
    properties.unregister()
    operators.unregister()
    ui.unregister()
    nodes.unregister()
    preferences.unregister()
    from . import presets
    presets.unregister()
    
    for cls in classes:
        bpy.utils.unregister_class(cls)

