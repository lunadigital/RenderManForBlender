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

from bpy.props import *
from bpy.types import PropertyGroup
import bpy.utils
from .. import util
from . import icons
import json
import os

# update the tree structure from disk file
def refresh_presets_libraries(disk_lib, preset_library):
    dirs = os.listdir(disk_lib)
    for dir in dirs:
        cdir = os.path.join(disk_lib, dir)
        # skip if not a dir
        if not os.path.isdir(cdir):
            continue
        
        is_asset = '.rma' in dir
        path = os.path.join(disk_lib, dir)

        if is_asset:
            preset = preset_library.presets.get(dir, None)
            if not preset:
                preset = preset_library.presets.add()
            

            preset.name = dir
            json_path = os.path.join(path, 'asset.json')
            data = json.load(open(json_path))
            preset.label = data['RenderManAsset']['label']
            preset.path = path
            preset.json_path = os.path.join(path, 'asset.json')

        else:
            sub_group = preset_library.sub_groups.get(dir, None)
            if not sub_group:
                sub_group = preset_library.sub_groups.add()
            sub_group.name = dir
            sub_group.path = path

            refresh_presets_libraries(cdir, sub_group)

    for i,sub_group in enumerate(preset_library.sub_groups):
        if sub_group.name not in dirs:
            preset_library.sub_groups.remove(i)
    for i,preset in enumerate(preset_library.presets):
        if preset.name not in dirs:
            preset_library.presets.remove(i)

# This file holds the properties for the preset browser.  
# They will be parsed from the json file

# get the enum items

# an actual preset
class RendermanPreset(PropertyGroup):
    bl_label = "RenderMan Preset Group"
    bl_idname = 'RendermanPreset'

    #def get_enum_items(self, context):
    #    return icons.enum_items

    @classmethod
    def get_from_path(cls, lib_path):
        if not lib_path:
            return
        group_path,preset = os.path.split(lib_path)

        group = RendermanPresetGroup.get_from_path(group_path)
        return group.presets[preset] if preset in group.presets.keys() else None
    
    name: StringProperty(default='')
    label: StringProperty(default='')
    #thumbnail: EnumProperty(items=get_enum_items)
    thumb_path: StringProperty(subtype='FILE_PATH')
    path: StringProperty(subtype='FILE_PATH')
    json_path: StringProperty(subtype='FILE_PATH')


# forward define preset group
class RendermanPresetGroup(PropertyGroup):
    bl_label = "RenderMan Preset Group"
    bl_idname = 'RendermanPresetGroup'
    pass

# A property group holds presets and sub groups
class RendermanPresetGroup(PropertyGroup):
    bl_label = "RenderMan Preset Group"
    bl_idname = 'RendermanPresetGroup'

    @classmethod
    def get_from_path(cls, lib_path):
        ''' get from abs lib_path '''
        head = util.get_addon_prefs().presets_library
        lib_path = os.path.relpath(lib_path, head.path)
        active = head
        for sub_path in lib_path.split(os.sep):
            if sub_path in active.sub_groups.keys():
                active = active.sub_groups[sub_path]            
        refresh_presets_libraries(active.path, active)
        return active

    # get the active library from the addon pref
    @classmethod
    def get_active_library(cls):
        active_path = util.get_addon_prefs().active_presets_path
        if active_path != '':
            return cls.get_from_path(active_path)
        else:
            return None

    name: StringProperty(default='')
    ui_open: BoolProperty(default=True)

    def generate_previews(self, context):
        return icons.load_previews(self)
    
    def update_path(self, context):
        util.get_addon_prefs().presets_path = self.path

    path: StringProperty(default='', name='Preset Library', update=update_path, subtype="FILE_PATH")
    presets: CollectionProperty(type=RendermanPreset)
    current_preset: EnumProperty(items=generate_previews, name='Current Preset')

    # gets the presets and all from children
    def get_presets(self):
        all_presets = self.presets[:]
        for group in self.sub_groups:
            all_presets += group.get_presets()
        return all_presets 

    def is_active(self):
        return self.path == util.get_addon_prefs().active_presets_path


def register():
    bpy.utils.register_class(RendermanPreset)
    bpy.utils.register_class(RendermanPresetGroup)

    # set sub groups type we have to do this after registered
    RendermanPresetGroup.sub_groups = CollectionProperty(type=RendermanPresetGroup)
    

def unregister():
    bpy.utils.unregister_class(RendermanPresetGroup)
    bpy.utils.unregister_class(RendermanPreset)

