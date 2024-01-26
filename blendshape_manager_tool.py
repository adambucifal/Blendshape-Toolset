import maya.cmds as cmds
import maya.mel as mel
from maya.api.OpenMaya import MGlobal
import DashCommand as dash


class blendShapeManagerTool:
    def __init__(self):
        # UI information
        self.window_name = "adams_blendshape_manager_tool_ui"
        self.window_title = "Adam's Blendshape Manager Tool v1.0"
        self.window_width = 385
        # Call UI
        self.user_interface()

    def user_interface(self):
        # Checks if the UI already exists
        if cmds.window(self.window_name, exists=True):
            cmds.deleteUI(self.window_name)
        # Defines the main window
        main_ui_window = cmds.window(
            self.window_name, 
            title=self.window_title, 
            width=self.window_width, 
            height=450, 
            sizeable=False,
        )
        main_layout = cmds.columnLayout(adjustableColumn=True)
        # Button layout for general functions
        general_layout = cmds.frameLayout(label="General")
        general_button_layout = cmds.rowColumnLayout(
            numberOfColumns=4, 
            columnWidth=[(i, self.window_width/4) for i in range(1, 5)],
        )
        # Create blendshape button
        create_blendshape_button = cmds.button(
            "create_blendshape_button", 
            label="Blendshape", 
            command=lambda *args: cmds.blendShape(),
        )
        # Zero out any avalible / unlocked attribute channels on a 
        # selected geometry's blendshape nodes button
        zero_non_connected_shapes_button = cmds.button(
            "zero_out_blendshape_weight_channel_button", 
            label="Zero Shapes", 
            command=self.zero_blendshape_weights, 
            annotation="Zeros out any blendshape channels on the selected mesh. " 
            "If any channel has an incoming connection, it will be skipped",
        )
        # Bakes current selected deformed mesh to a new mesh 
        # with attributes cleaned button
        baked_current_pose_button = cmds.button(
            "bake_current_pose_button", 
            label="Bake Current", 
            command=self.bake_current_pose, 
            annotation="Bakes the current pose of the selected mesh and " 
            "removes any extra attributes/unlocks all default attributes.",
        )
        # Cleans a selected object's attributes and unlocks the base attrs button
        clean_object_button = cmds.button(
            "clean_object_button", 
            label="Clean Obj", 
            command=self.clean_object, 
            annotation="Removes extra attrs and unlocks.",
        )
        # Inverts the selected corrective to get the delta button
        get_delta_button = cmds.button(
            "get_delta_button", 
            label="Invert Shape (all)", 
            command=self.get_delta, 
            annotation="Select the corrective pose and the base geo "
            "(in pose) and run",
        )
        # Inverts only skinned geo button
        invert_skinned_shape_button = cmds.button(
            "invert_skinned_shape_button", 
            label="Invert Shape (skin)", 
            command=self.invert_shape_skinned,
        )
        # Returns the selected blendshape attribute's index button
        get_blendshape_channel_index_button = cmds.button(
            "get_blendshape_channel_index_button", 
            label="Get Shape Index", 
            command=self.get_blendshape_channel_index,
        )
        # Bakes out all shapes in a blendshape node button
        batch_bake_shapes_button = cmds.button(
            "batch_bake_shapes_button", 
            label="Batch Bake Shapes", 
            command=self.bake_shapes,
        )
        # Hookup corrective shape layout section
        cmds.setParent(main_layout)
        cmds.separator(style="none", height=15)
        corrective_shapes_layout = cmds.frameLayout(
            "Hookup Corrective Shapes", 
            annotation="Looks at the active blendshape channels on the "
            "specified blendshape node and builds a combination shape "
            "using the combination shape geo and the active channels as the drivers.",
        )
        # Text fields for the corrective shape setup
        self.base_geo_field = self.txt_grp(
            self, label="Base geo:", add_button=True
        )
        self.blendshape_node_field = self.txt_grp(
            self, label="Blendshape Node:", add_button=True
        )
        self.comb_shape_field = self.txt_grp(
            self, label="Combination Shape Geo:", add_button=True
        )
        # Title for combination shape naming
        cmds.setParent(corrective_shapes_layout)
        cmds.separator()
        cmds.text(label="Combination Shape Node Naming")
        cmds.separator()
        cmds.rowColumnLayout(numberOfColumns=2, columnWidth=[(1,300),(2,50)])
        # Values in renaming the nodes
        self.comb_shape_look_for_field = cmds.textFieldGrp(
            label="Look for", text="corrective_delta"
        )
        cmds.separator(style="none")
        self.comb_shape_replace_field = cmds.textFieldGrp(
            label="Replace with", text="cs"
        )
        cmds.separator(style="none")

        cmds.setParent(corrective_shapes_layout)
        # Hookup correctives button
        hookup_corrective_button = cmds.button(
            label="Hookup Corrective", command=self.hookup_combination_shape
        )
        cmds.setParent(main_layout)
        cmds.separator(style="none", height=15)
        # Deformer weights sections
        blendshape_weights_layout = cmds.frameLayout("Deformer Weights")

        self.inverse_bs_base_geo_field = self.txt_grp(
            self, label="Base geo:", add_button=True
        ) 
        cmds.setParent(blendshape_weights_layout)
        cmds.rowColumnLayout(numberOfColumns=2, columnWidth=[(1,275),(2,100)])
        filter_deformers = ["----"]
        all_deformers = [filter_deformers + cmds.ls(type=deformer_name) 
            for deformer_name in ["blendShape", "wire", "cluster", "deltaMush", "jiggle"] 
            if cmds.ls(type=deformer_name)
        ][0]
        self.source_blendshape_option = self.option_menu_grp(
            label="Source Deformer: ", 
            items=all_deformers
        )
        self.source_blendshape_index_option = cmds.intField(minValue=0)
        
        # Choose a target blendshape deformer
        self.target_blendshape_option = self.option_menu_grp(
            label="Target Deformer: ", items=all_deformers
        )
        self.target_blendshape_index_option = cmds.intField(minValue=0)

        cmds.setParent(blendshape_weights_layout)
        # Copy weights method
        self.copy_method_option = self.option_menu_grp(
            label="Method:", items=["Copy Weights", "Inverse Mask"]
        )
        # Transfer weights button
        transfer_deformer_weights_button = cmds.button(
            label="Transfer", command=self.copy_and_inverse_blendshape_weights
        )
        cmds.setParent(main_layout)
        cmds.showWindow(self.window_name)
    
    # Wraps UI objects with separators
    def create_separators(func):
        def wrapper(self, *args, **kwargs):
            """
            Wraps UI object in separators
            :param separator_location: string, 'none', 'both', 'below', 'above', 
                determines where the separators are placed in relation to the UI object
            :param separator_style: string, style of the separators
            :param separator_height: float, height of the separators
            :return result: returns the string of the ui object to be accessed
            """
            # Gets keyword arguments
            separator_location = kwargs.get("separator_location", "none")
            separator_style = kwargs.get("separator_style", "none")
            separator_height = kwargs.get("separator_height", 1)
            
            # Checks the keyword arguments
            if separator_location == "both" or separator_location == "above":
                cmds.separator(style=separator_style, height=separator_height)
            # Runs the UI object function
            result = func(self, *args, **kwargs)
            if separator_location == "both" or separator_location == "below":
                cmds.separator(style=separator_style, height=separator_height)
            return result
        return wrapper
        
    @create_separators
    def option_menu_grp(self, items, **kwargs):
        """
        Creates an option menu group
        :param label: string, label for the option menu
        :param items: list, options for the option menu
        :return option_menu_group: string, name of the option menu object
        """
        label = kwargs.get("label", "")
        # Creates option menu
        option_menu_group = cmds.optionMenuGrp(label=label)
        [cmds.menuItem(label=item) for item in items]
        return option_menu_group
    
    @create_separators
    def txt_grp(self, *args, **kwargs):
        """
        Creates a text field group
        :param label: string, label for the text field
        :param add_button: bool, if true create button that adds selected to text field
        :return txt_field_grp: string, name of the text field object
        """
        # Gets keyword arguments
        label = kwargs.get("label", "UNAMED LABEL")
        add_button = kwargs.get("add_button", False)
        
        # Adds a button for the text group
        if add_button:
            cmds.rowColumnLayout(
                numberOfColumns=3, columnWidth=[(1,325),(2,10),(3,50)]
            )
        # Creates text field
        txt_field_grp = cmds.textFieldGrp(label=label)
        if add_button:
            cmds.separator(style="none")
            self.add_selected_blendshape = cmds.button(
                label="Add", command=lambda *args: self.add_selected(txt_field_grp)
            )
            cmds.setParent('..')
        return txt_field_grp
    
    def copy_and_inverse_blendshape_weights(self, *args):
        """
        Transfers blendshape mask weights
        :return dictionary: new mask weights
        """
        # Gets UI results
        # Base geo that is used to get all the vertex weight values
        mesh = cmds.textFieldGrp(
            self.inverse_bs_base_geo_field, query=True, text=True
        )
        # Source deformer
        source_blendshape = cmds.optionMenuGrp(
            self.source_blendshape_option, query=True, value=True
        )
        # Source Deformer Index (Only looked at if source deformer is a blendshape)
        source_index = cmds.intField(
            self.source_blendshape_index_option, query=True, value=True
        )
        # Target deformer
        target_blendshape = cmds.optionMenuGrp(
            self.target_blendshape_option, query=True, value=True
        )
         # Target Deformer Index (Only looked at if target deformer is a blendshape)
        target_index = cmds.intField(
            self.target_blendshape_index_option, query=True, value=True
        )
        # Method in which the weights are copied over
        weight_method = cmds.optionMenuGrp(
            self.copy_method_option, query=True, value=True
        )
        # List of base geo verts
        vertices = cmds.ls(f"{mesh}.vtx[*]", flatten=True)
        if source_blendshape == "----" or target_blendshape == "----":
            return
        
        # Creates dictionary to store mask weights
        weights_mask_dict = {}
        for index, vertex in enumerate(vertices):
            source_attribute = self.attribute_name(
                source_blendshape, vertex=index, index=source_index
            )
            target_attribute = self.attribute_name(
                target_blendshape, vertex=index, index=target_index
            )
            # Gets the current vertex's blendshape weights
            current_value = cmds.getAttr(source_attribute)
            # Determines the new value
            if weight_method == "Inverse Mask":
                new_value = 1 - current_value
            else:
                new_value = current_value
            # Adds the current vertex weights to the weights_mask_dict dictionary
            weights_mask_dict[index] = new_value 
            # Sets the current vertex as the new value   
            cmds.setAttr(target_attribute, new_value)
        # Display message confirming that the weights were transfered
        try: 
            source_attr = cmds.listAttr(
                f"{source_blendshape}.w", multi=True
            )[source_index]
        except ValueError:
            source_attr = ""
        try:
            target_attr = cmds.listAttr(
                f"{target_blendshape}.w", multi=True
            )[target_index]
        except ValueError:
            target_attr = ""   
        # Maya command message to show results
        MGlobal.displayInfo(f"{source_blendshape} {source_attr} was transfered to "
            f"{target_blendshape} {target_attr} using {weight_method}".replace("  ", " ")
        )
    
        return weights_mask_dict
    
    def attribute_name(self, your_deformer, vertex, index):
        """
        Gets the appropriate attribute string for querying and setting 
        vertex deformer weights depending on the deformer provided
        :param your_deformer: string, name of your deformer
        :param vertex: int, index of the vertex you would like to operate on
        :param index: int, index of the blendshape target you would like to 
        opperate on (only applicable when the deformer type is a blendshape)
        :return string: Name of the attribute
        """
        if cmds.nodeType(your_deformer) == "blendShape":
            return (f"{your_deformer}.inputTarget[0]."
                   f"inputTargetGroup[{index}].targetWeights[{vertex}]")
        else:
            return (f"{your_deformer}.weightList[0].weights[{vertex}]")
    
    def bake_shapes(self, *args):
        """
        Bakes shapes into separate geometry
        """
        selection = cmds.ls(selection=True, type="blendShape")
        if not selection:
            cmds.error("Nothing selected")
        
        blendshape = selection[0]
        # Search for the base geometry through the blendshape's connections 
        geo = cmds.listConnections(f"{blendshape}.outputGeometry")[0]
        
        # While loop to find the base geo through any extra deformers in the input list
        while cmds.nodeType(geo) != "transform":
            geo = cmds.listConnections(
                f"{geo}.outputGeometry"
            )[0]
        # Gets any selected channels in the blendshape node
        selected_targets = dash.getAllSelectedChannels()

        if not selected_targets:
            targets = cmds.listAttr(f"{blendshape}.w", multi=True)
        else:
            targets = selected_targets
        # Zeros all blendshape targets before baking
        zero_all_targets = [cmds.setAttr(f"{blendshape}.{target}", 0) 
            for target in targets
        ]
        new_shapes = []
        for index, target in enumerate(targets):
            cmds.setAttr(f"{blendshape}.{target}", 1)
            new_geo = cmds.duplicate(geo, name=f"{target}_baked")[0]
            local_pos = cmds.xform(
                new_geo, query=True, translation=True, worldSpace=False
            )
            cmds.move(
                local_pos[0]+(index+1)*25, *local_pos[1:3], new_geo
            ) 
            cmds.setAttr(f"{blendshape}.{target}", 0)
            new_shapes.append(new_geo)
        
        MGlobal.displayInfo(f"Baked {len(new_shapes)}/{len(targets)} shapes")
        return new_shapes
    
    def get_blendshape_channel_index(self, *args):
        """
        Prints out the index of a selected blendshape channel
        :return index: index of the selected attribute
        """
        # Gets the selected blendshape
        selected_blendshape = cmds.ls(selection=True, type="blendShape")
        if not selected_blendshape:
            cmds.error("No blendshape selected")
        # Gets the selected channel
        selected_channel = dash.getAllSelectedChannels()
        if not selected_channel:
            cmds.error("No channel selected")
        # Lists all the blendshape channels
        all_blendshape_attrs = cmds.listAttr(
            f"{selected_blendshape[0]}.w", multi=True
        )
        # Checks if the selected channel is within the blendshape's attributes
        if selected_channel[0] in all_blendshape_attrs:
            index = all_blendshape_attrs.index(selected_channel[0])
        
            MGlobal.displayInfo(f"{selected_channel[0]}: {index}")
            return index
    
    def add_selected(self, element, type=""):
        """
        Adds the first selected object to a text field grp ui object
        :param element: string of the ui object that the 
            selected objects will be added to
        :param type: string of the type of object that should be added
        """
        selected = cmds.ls(selection=True)
        
        if not selected:
            return
        if type == "blendShape":
            if cmds.nodeType(selected[0]) == "blendShape":
                cmds.textFieldGrp(element, edit=True, text=selected[0])
            else:
                deformers = cmds.findDeformers(selected[0])
                if deformers:
                    blendshape = [deformer_node 
                        for deformer_node in deformers 
                        if cmds.nodeType(deformer_node) == "blendShape"
                    ][0]
                    cmds.textFieldGrp(element, edit=True, text=blendshape)
        else:
            cmds.textFieldGrp(element, edit=True, text=selected[0])
    
    def hookup_combination_shape(self, *args):
        """
        Hooks up a corrective shape based on the active blendshape 
            channels on the blendshape node
        """
        # Gets all UI results
        blendshape = cmds.textFieldGrp(
            self.blendshape_node_field, query=True, text=True
        )
        driven_shape = cmds.textFieldGrp(
            self.comb_shape_field, query=True, text=True
        )
        look_for = cmds.textFieldGrp(
            self.comb_shape_look_for_field, query=True, text=True
        )
        replace_with = cmds.textFieldGrp(
            self.comb_shape_replace_field, query=True, text=True
        )
        # Lists the blendshape attributes
        blendshape_attributes = cmds.listAttr(f"{blendshape}.w", multi=True)
        if cmds.attributeQuery(driven_shape, node=blendshape, exists=True) is False:
            cmds.error("Can't find the combination shape geo in the blendshape node")
            return
        # Error check
        [cmds.error(f"Object '{object}' does not exist") 
            for object in [blendshape, driven_shape] 
            if not cmds.objExists(object)
        ]
        if cmds.nodeType(blendshape) != "blendShape":
            cmds.error(f"'{blendshape}' is not a blendshape")
        # Gets all blendshape channels that are equal to 1
        active_attrs = [
            attr 
            for attr in blendshape_attributes 
            if cmds.getAttr(f"{blendshape}.{attr}") == 1
        ]
        # Creates combination shape node
        cs_node = cmds.createNode(
            "combinationShape", name=driven_shape.replace(look_for, replace_with)
        )
        # Connects the blendshape channels into the combination shape node
        [cmds.connectAttr(f"{blendshape}.{attr}", f"{cs_node}.inputWeight[{index}]") 
            for index, attr in enumerate(active_attrs)
        ]
        # Connects the output of the combination shape node into the driven shape
        cmds.connectAttr(f"{cs_node}.outputWeight", f"{blendshape}.{driven_shape}")
    
    def bake_current_pose(self, *args):
        """
        Bakes the current pose of the selected objects and cleans it
        """
        selection = cmds.ls(selection=True)
        for object in selection:
            object_shapes = cmds.listRelatives(object, shapes=True)
            [    
                object_shapes.remove(node) 
                for node in object_shapes 
                if node[-4:] == "Orig"
            ]
            object_instance = cmds.instance(object_shapes)
            cmds.duplicate(object_instance, name=f"{object}_baked")
            cmds.delete(object_instance)
            
    def clean_object(self, *args):
        """
        Unlocks main attrs and deletes any unimportant attrs
        """
        selection = cmds.ls(selection=True)
        # All main attributes
        main_attrs = [
            'visibility', 
            'translateX', 
            'translateY', 
            'translateZ', 
            'rotateX', 
            'rotateY', 
            'rotateZ', 
            'scaleX', 
            'scaleY', 
            'scaleZ'
        ]
        # Deletes any other attributes than the main attrs and sets the main attrs to unlocked
        for object in selection:
            other_attrs = cmds.listAttr(object, keyable=True)
            if other_attrs:
                [
                    cmds.deleteAttr(f"{object}.{attr}") 
                    for attr in other_attrs 
                    if attr not in main_attrs
                ]
                
            [
                cmds.setAttr(f"{object}.{attr}", lock=False, keyable=True) 
                for attr in main_attrs
            ]
        
    def invert_shape_skinned(self, *args):
        """
        Inverts just skinned geo, will not work with blendshapes or other deformers
        """
        try:
            corrective_shape_geo, base_skinned_geo = cmds.ls(selection=True)
        except ValueError as v:
            cmds.error(f"Select corrective shape and the base geo (in pose), {v}")
        # Runs the invert shape maya command
        cmds.invertShape()
    
    def zero_blendshape_weights(self, *args):
        """
        Zeros out any unlocked or non connected channels in an 
            object's blendshape nodes
        """
        selection = cmds.ls(selection=True)
        if not selection:
            cmds.warning("Nothing selected")
        for object in selection:
            # Gets any deformers on the current object
            object_deformers = cmds.findDeformers(object)
            if not object_deformers:
                cmds.warning(f"'{object}' does not contain any blendshape nodes")
                continue
            # Filters out the blendshape nodes
            object_blendshapes = [
                node 
                for node in object_deformers 
                if cmds.nodeType(node) == "blendShape"
            ]
            if not object_blendshapes:
                cmds.warning(f"'{object}' does not contain any blendshape nodes")
                continue
            # For each blendshape node, checks to see what channels are avalible to zero out
            for object_blendshape in object_blendshapes:
                blendshape_weights = cmds.listAttr(f"{object_blendshape}.w", multi=True)
                weights_to_zero = [
                    weight 
                    for weight in blendshape_weights 
                    if cmds.getAttr(f"{object_blendshape}.{weight}") != 0
                ]
                
                for weight in weights_to_zero:
                    first_connection = cmds.listConnections(
                        f"{object_blendshape}.{weight}", 
                        source=True, 
                        destination=False, 
                        plugs=True, 
                        skipConversionNodes=True,
                    )
                    if first_connection is None:
                        cmds.setAttr(f"{object_blendshape}.{weight}", 0)
                        continue

    def get_delta(self, *args):
        """
        Gets the delta (difference) of the corrective shape and base deformed geometry 
            (deformers + skinned geo)
        """
        try:
            corrective_shape_geo, base_geo = cmds.ls(selection=True)
        except ValueError as v:
            cmds.error(f"Select corrective shape and the base geo (in pose), {v}")
        # Finds any deformers on the geo
        base_geo_deformers = cmds.findDeformers(base_geo)
        # Sets all their envolopes to zero
        [
            cmds.setAttr(f"{deformer_node}.envelope", 0) 
            for deformer_node in base_geo_deformers
        ]
        # Creates new base geo
        duplicated_base_geo = cmds.duplicate(base_geo, name="test")[0]
        # Creates temporary blendshape to create the delta
        temporary_blendshape = cmds.blendShape(
            corrective_shape_geo, base_geo, duplicated_base_geo
        )[0]
        # Turn back on all the deformers
        [
            cmds.setAttr(f"{deformer_node}.envelope", 1) 
            for deformer_node in base_geo_deformers
        ]
        # Set the temporary blendshape attrs accordingly 
        cmds.setAttr(f"{temporary_blendshape}.{corrective_shape_geo}", 1)
        cmds.setAttr(f"{temporary_blendshape}.{base_geo}", -1)
        # Bake new delta geo
        baked_delta = cmds.duplicate(
            duplicated_base_geo, name=f"{corrective_shape_geo}_inverted_shape"
        )
        # Delete unimportant nodes
        cmds.delete(duplicated_base_geo, temporary_blendshape)
        # Parent under the world
        try:
            cmds.parent(baked_delta, world=True)
        except RuntimeError:
            pass
        # Clean the new delta shape
        cmds.select(baked_delta)
        self.clean_object()

if __name__ == "__main__":
    blendShapeManagerTool()