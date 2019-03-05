# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


import os, shutil, math, time, sys, pip, bpy

modulename = 'PIL'
if modulename not in sys.modules:
    if int(pip.__version__.split('.')[0])>9:
        from pip._internal import main
    else:
        from pip import main

    main(['install', 'Pillow'])

from bpy.props import *
from PIL import Image


bl_info = {
    "name" : "Sprite Sheet Generator",
    "author" : "Vladislovas Kidanovas",
    "description" : "Sprite sheet generator, Addon for Blender 2.8",
    "blender" : (2, 80, 0),
    "location" : "",
    "warning" : "",
    "category" : "Render"
}

bpy.types.Scene.render_object = StringProperty(
    description = "Select animation object"
)

bpy.types.Scene.use_nla_tracks = BoolProperty(
    name="Enable or Disable",
    description="A simple bool property",
    default = True
)

bpy.types.Scene.tmp_image_output = StringProperty(
    name = "Temporary Storage",
    description = "Temporary Image Storage",
    subtype = "DIR_PATH",
    default = "/tmp/")

bpy.types.Scene.sprite_sheet_padding = IntProperty(
    name = "Padding",
    description = "Sets a padding between sprites",
    default = 1)

bpy.types.Scene.sprite_sheet_image_output = StringProperty(
    name = "Sprite Sheet Image Folder",
    description = "Save folder for sprite sheet image",
    subtype = "FILE_PATH",
    default = "/tmp/")


class SSG_OT_sprite_sheet_generator(bpy.types.Operator):
    bl_idname = "render.sprite_sheet_generator"
    bl_label = "Sprite sheet generator"

    @classmethod
    def poll(cls, context):
        return context.scene != None

    def execute(self, context):
        scene = context.scene

        if scene.render_object == None or scene.render_object == '' or scene.objects[scene.render_object] == None:
            self.report({'ERROR_INVALID_INPUT'}, "Missing render object")
            return {'CANCELLED'}
        animation_name = "spritesheet"
        if scene.use_nla_tracks:
            obj = scene.objects[scene.render_object]
            ad = obj.animation_data
            #parse
            ta = scene.object_nla_tracks.split("__")
            
            if ad:
                for track in ad.nla_tracks:
                    if track.name == ta[0]:
                        track.is_solo = True
                        for strip in track.strips:
                            if strip.name == ta[1]:                                
                                scene.frame_start = strip.frame_start
                                scene.frame_end = strip.frame_end
                                animation_name = strip.name


        tmp_output = scene.tmp_image_output
        output = scene.sprite_sheet_image_output
        
        #Clean Temporary folder
        self.cleanTempFolder(tmp_output)

        bpy.context.scene.render.filepath = tmp_output + "####"
        bpy.ops.render.render(animation=True)

        frames = []
        tile_width = 0
        tile_height = 0

        spritesheet_width = 0
        spritesheet_height = 0

        files = os.listdir(tmp_output)
        files.sort()
        max_frames_row = 8
        # max_frames_row = int(math.ceil(math.sqrt(len(files))))

        for current_file in files :
            try:
                with Image.open(tmp_output + current_file) as im :
                    frames.append(im.getdata())
            except:
                print(current_file + " is not a valid image")
        
        self.cleanTempFolder(tmp_output)
        
        tile_width = frames[0].size[0]
        tile_height = frames[0].size[1]

        if len(frames) > max_frames_row :
            spritesheet_width = tile_width * max_frames_row
            required_rows = math.ceil(len(frames)/max_frames_row)
            spritesheet_height = tile_height * required_rows
        else:
            spritesheet_width = tile_width*len(frames)
            spritesheet_height = tile_height
            
        print(frames)
        print(tile_height)

        spritesheet = Image.new("RGBA",(int(spritesheet_width), int(spritesheet_height)))

        for current_frame in frames :
            top = tile_height * math.floor((frames.index(current_frame))/max_frames_row)
            left = tile_width * (frames.index(current_frame) % max_frames_row)
            bottom = top + tile_height
            right = left + tile_width
            
            box = (left,top,right,bottom)
            box = [int(i) for i in box]
            cut_frame = current_frame.crop((0,0,tile_width,tile_height))
            
            spritesheet.paste(cut_frame, box)

        if not os.path.exists(output):
            os.makedirs(output)
            
        spritesheet.save(output+animation_name+"_" + time.strftime("%Y-%m-%dT%H-%M-%S") + ".png", "PNG", dpi=[300,300])
        # spritesheet.save(output+animation_name+".png", "PNG", dpi=[300,300])
        

        return {'FINISHED'}

    def cleanTempFolder(self, folder):
        for the_file in os.listdir(folder):
            file_path = os.path.join(folder, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path): shutil.rmtree(file_path)
            except Exception as e:
                print(e)

class SSG_PT_sprite_sheet_panel(bpy.types.Panel):
    bl_idname = "SSG_PT_sprite_sheet_panel"
    bl_label = "Sprite Sheet Generator"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context  = "render"

    def item_cb(self, context): 
        scene = context.scene
        obj = scene.objects[scene.render_object]
        
        al = []

        ad = obj.animation_data
        if ad:
            for track in ad.nla_tracks:
                for strip in track.strips:
                    al.append((track.name+"__"+strip.action.name, track.name+"->"+strip.action.name, "track name -> animation name"))
                     
        return al
    
    bpy.types.Scene.object_nla_tracks = EnumProperty(
        items=item_cb,
        description = "Select object animation, before select set it in NLA Tracks"
    ) 

    def draw(self, context):
        layout = self.layout

        scene = context.scene

        if scene == None:
            return

        row = layout.row()

        row.label(text='Animation settings')

        layout.prop_search(scene, "render_object", context.scene, "objects", text="Animation object")

        row = layout.row()
        row.prop(scene, "use_nla_tracks", text="Use Nonlinear animations")

        if scene.use_nla_tracks:
            row = layout.row()
            row.prop(scene, "object_nla_tracks", text="Select animation")
        else:
            row = layout.row()
            row.prop(scene, "frame_start")

            row = layout.row()
            row.prop(scene, "frame_end")

        layout.separator()
        layout.label(text='Output')

        row = layout.row()
        row.prop(scene, 'tmp_image_output')

        row = layout.row()
        row.prop(scene, 'sprite_sheet_image_output')

        row = layout.row()
        row.prop(scene, 'sprite_sheet_padding')

        row = layout.row()
        layout.separator()
        layout.label(text="Render")

        row = layout.row()
        row.scale_y = 3.0

        row.operator(SSG_OT_sprite_sheet_generator.bl_idname)

classes = (SSG_OT_sprite_sheet_generator, SSG_PT_sprite_sheet_panel)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    



def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

if __name__ == "__main__":register()