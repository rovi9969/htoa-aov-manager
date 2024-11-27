####################################################################################################################################################################################
# NAME : HtoA AOVs Manager                                                                                                                                                         #
# Author : Ravi Motwani     Contact : motwani.ravi20@gmail.com                                                                                                                     #
# Script Config in Houdini                                                                                                                                                         #
# 1. Copy the htoa_aov_manager folder in scripts folder of Houdini Documents.                                                                                                      #
# i.e. C:/Users//Documents/houdini{version}/scripts/python/                                                                                                                        #
# 2. To access this script through shelf use the following command.                                                                                                                #
# import importlib ;from htoa_aov_manager import tool ;importlib.reload(tool) ;tool.main()
####################################################################################################################################################################################

'''
1. this script will create arnold aovs from the list of aovs checked over the arnold rops selected.
2. second feature of this script is to copy aovs from one rop to other rop(s)

if you select nothing or not a single arnold rop and run the ok button, it will warn to select the arnold rop,
if the aov is already present then it will skip that to add over rop, 
if any blank or disabled aov found than will be removed.
'''

import hou
from PySide2 import QtCore, QtWidgets, QtGui
import json
import re
import os

def list_active_windows():
    app = QtWidgets.QApplication.instance() # Get the main application
    windows = [w for w in app.topLevelWidgets() if w.isWindow()] # Retrieve all top-level widgets
    window_info = [w for w in windows if w.windowTitle() == get_window_title()] # Collect window titles and object names
    return window_info

def get_window_title():
    return "HtoA AOV Manager v1.2 beta"
    
class process(object):
    def __init__(self):
        #TYPE
        # all RGB
        self.ar_aov_type = 1

    def warning_info(self, message_box_title, message_box_text):
        QtWidgets.QMessageBox.warning(None, message_box_title, message_box_text, QtWidgets.QMessageBox.Ok)

    # CREATION OF AOVS
    def aov_type_mod(self, aov_name, aov, i):
        self.type5 = ["Z", "depth"] #float
        self.type6 = ["N", "P" , "Pref" ] #vector
        #self.type7 = ["motionvector"] #vector2d
        if aov_name in self.type5:
            aov.parm("ar_aov_type" + str(i)).set("FLOAT")
        elif aov_name in self.type6:
            aov.parm("ar_aov_type" + str(i)).set("VECTOR")
        else:
            pass

    def aov_precision_mod(self, aov_name, aov, i):
        # PRECISION 
        #normal, p, pref, z, motionvector, same as beauty
        #res all float16
        self.beauty_precision = ["N", "P", "Pref", "depth", "motionvector"] #same as beauty
        if aov_name in self.beauty_precision:
            aov.parm("ar_aov_exr_precision" + str(i)).set("beauty")
        else:
            aov.parm("ar_aov_exr_precision" + str(i)).set("half")
            
    def aov_filter_mod(self, aov_name, aov, i):
        # FILTER 
        #all same as beauty except z closest filter
        self.filter_pixel = ["Z", "depth"] #"closest_filter"
        if aov_name in self.filter_pixel:
            aov.parm("ar_aov_pixel_filter" + str(i)).set("closest_filter")
        else:
            pass

    def rop_selection_qc(self, rop_type = "arnold"):
        selection = hou.selectedNodes()
        if selection:
            rop_list = [x for x in selection if x.type().name() == rop_type]
            return rop_list
    
    def remove_unused_aovs(self, sel):
        parms = sel.parms()
        # total number of arnold's aovs
        aov_enables_list = [x for x in parms if x.name().startswith(self.aov_enable) and x.name()[-1].isdigit()]
        # index of aovs off in arnold aov
        aov_off_enable_val = [ int(x.name().split(self.aov_enable)[-1])-1 for x in aov_enables_list if x.eval() == False]

        # total number of arnold's labels aovs
        aov_label_list = [x for x in parms if x.name().startswith(self.aov_label) and x.name()[-1].isdigit()]
        # index of aovs label blank in arnold aov
        aov_off_label_val = [ int(x.name().split(self.aov_label)[-1])-1 for x in aov_label_list if x.eval() == ""]
        
        # sum up off aovs and blank aovs
        non_working_aov_index = list(set(aov_off_label_val+aov_off_enable_val))
        # removing  off aovs and blank aovs
        for index in reversed(non_working_aov_index):
            sel.parm(self.aov_count).removeMultiParmInstance(index)
                        
    def aovs_creation(self, aov_labels, clear_unused=True):
        title = "ROP Selection"
        message = "Works only on Arnold ROPs!!!"
        
        with hou.undos.group("AOVs Creation Action"):
            selection = self.rop_selection_qc("arnold")
            if selection:
                print(f"Process for creation of aovs started.")
                for sel in selection:
                    aovs_count = sel.parm(self.aov_count).eval()                
                    
                    if aovs_count:
                        if clear_unused == True:
                            self.remove_unused_aovs(sel) ##############
                        aovs_count = sel.parm(self.aov_count).eval()
                        parms = sel.parms()
                        aovs = [x.eval() for x in parms if self.aov_label in x.name() ]
                        aovs_create = [x for x in aov_labels if x not in aovs ]
                        self.adding_aovs(sel, aov_labels, aovs_create, aovs_count) ################
                    else:
                        aovs_create = aov_labels
                        aovs_count = 0
                        self.adding_aovs(sel, aov_labels, aovs_create, aovs_count) ################
            else:
                self.warning_info(title, message)

    def adding_aovs(self, rop_node, aov_labels, aovs_creation_list, total_aovs_count):
        counter = 1
        for aov_create in aovs_creation_list:
            num = total_aovs_count + counter
            rop_node.parm(self.aov_count).set(num)
            rop_node.parm(self.aov_label + str(num)).set(aov_create)
            self.aov_type_mod(aov_create, rop_node, num)
            self.aov_precision_mod(aov_create, rop_node, num)
            self.aov_filter_mod(aov_create, rop_node, num)
            counter += 1
        print(f"{aovs_creation_list} created aovs.")
        print(f"{len(aov_labels)} aovs were selected to add in layers, {len(aovs_creation_list)} were added.")

    # COPYING AOVs
    def get_parent_rop_aovs(self, event, qt_parent_linedit, qt_aovs_list_widget):
        """
        Input for user to add single arnold rop to copy aovs from.
        Args :
            event (QEvent): Left Click - Choice to select Arnold ROP & Right Click - Clears all the field for parent line.
        """
        if event.button() == QtCore.Qt.LeftButton:
            self.get_parent_aovs(qt_parent_linedit, qt_aovs_list_widget)
        elif event.button() == QtCore.Qt.RightButton:
            qt_parent_linedit.setText("")
            qt_aovs_list_widget.clear()
        else:
            pass

    def get_parent_aovs(self, qt_parent_linedit, qt_aovs_list_widget):
        """
        List out the aovs from the selected rop to qlistwidget as items.
        """
        rop = self.get_arnold_rops(0, qt_parent_linedit, "arnold")
        if rop:
            node, aovs_count = self.ar_rop_aov_count(rop)
            aov_labels = self.ar_rop_aov_labels(node, aovs_count)
            qt_aovs_list_widget.clear()
            if aov_labels:
                for i in aov_labels:
                    item = QtWidgets.QListWidgetItem(i)
                    qt_aovs_list_widget.addItem(item)

    def get_arnold_rops(self, multiple_select, lineedit, rop_type):
        """
        Retrieves the ROP node/s for specific type and updates the UI lineedit field.

        Args:
            multiple_select (bool): Allows choice for multiple (True) or single ROP (False) (Render Output Process) node.
            lineedit (parm): A QT Interface parameter to display the ROP node names.
            rop_type (str): filtering the ROP by type eg: 'arnold'
        Returns :
            str or None:
                -If `multiple_select` is False with arnold ROP type, returns and sets single ROP node else sets multiplw ROP nodes.
        """
        print("Starting to retrieve ROP nodes.")
        print(f"ROP Type: {rop_type}, Multiple Select: {multiple_select}")

        return_msg = f'Please ensure to select only {rop_type} ROP node(s).'
        return_msg_title = "Selection Warning !!!"

        # Get the ROP nodes.
        rop_nodes = hou.ui.selectNode( node_type_filter = hou.nodeTypeFilter.Rop, multiple_select = multiple_select)#, initial_node = q_nodes )
        print(f"User selected node(s): {rop_nodes}")
        if rop_nodes:
            rop_nodes = [rop_nodes] if isinstance(rop_nodes, str) else list(rop_nodes)
            valid_rop_nodes = [x for x in rop_nodes if hou.node(x).type().name() == rop_type]
            if valid_rop_nodes:
                formatted_rop_nodes = (re.sub(r"[\[\],']", "", str(valid_rop_nodes)))
                formatted_rop_nodes = formatted_rop_nodes.replace(" ", "\n")
                lineedit.setText(str(formatted_rop_nodes))
                # Return a single node if `multiple_select` is False, else return the list
                return valid_rop_nodes[0] if not multiple_select else valid_rop_nodes
            else:
                hou.ui.displayMessage( text = return_msg, title = return_msg_title)

    def ar_rop_aov_count(self, rop_path): 
        #only arnold supported but can be extended.
        """
        Retrieves the specified ROP node and the count of AOVs (Arbitrary Output Variables) from it.

        Args:
            rop_path (str): The Houdini node path to the ROP (Render Output Process) node.

        Returns:
            tuple: A tuple containing:
                - node (hou.Node): The Houdini node object corresponding to the provided ROP path.
                - aovs_count (int): The count of AOVs associated with the specified ROP node.
        """
        node = hou.node(rop_path)
        aovs_count = node.parm(self.aov_count).eval()
        return(node, aovs_count)

    def ar_rop_aov_labels(self, node, aovs_count):#, status
        """
        Retrieves the AOV (Arbitrary Output Variable) labels from the specified ROP node.
        Args:
            node (hou.Node): The Houdini node object  for arnold ROP (Render Output Process).
            aovs_count (int): The total number of AOVs to retrieve.
        Returns:
            aov_labels (list): The list of aov labels containing in arnold ROP.
        """
        if aovs_count:
            #aov_labels = [ node.parm( f"{self.aov_label}{x+1}" ).eval() for x in range (aovs_count) ]
            #aov_labels = [ node.parm( f"{self.aov_label}{x+1}" ).eval() for x in range (aovs_count) if node.parm( f"{self.aov_enable}{x+1}" ).eval()]
            aov_labels = [ node.parm( f"{self.aov_label}{x+1}" ).eval() +"( DISABLE )" 
            if not node.parm(f"{self.aov_enable}{x+1}").eval() 
            else node.parm(f"{self.aov_label}{x+1}").eval() 
            for x in range (aovs_count)]
            return(aov_labels)

    def get_children_rop_aovs(self, event, qt_child_linedit):
        """
        Input for user to add multiple child arnold rop nodes to copy aovs onto.
        Args :
            event (QEvent): Left Click - Choice to select Arnold ROPs & Right Click - Clears all the field for parent line.
        """
        if event.button() == QtCore.Qt.LeftButton:
            self.get_arnold_rops(1, qt_child_linedit, "arnold")
        elif event.button() == QtCore.Qt.RightButton:
            qt_child_linedit.setText("")
        else:
            pass

    def exec_copy_aovs(self, del_permission, main_rop_node, index, child_rop_nodes):
        for i in index:
            aov_num = i+1
            search_pattern = self.aov_prefix + ".*(?<!\d)" + str(aov_num)+"$"
            # list of parms starts with prefix ar_aov under aov_keys
            aov_keys = [x.name() for x in main_rop_node.parms() if re.match( search_pattern, x.name() )]
            # returning the values from the aov_keys 
            aov_values =  [ main_rop_node.parm(x).eval() for x in aov_keys ]
            # check if the aov is enable or disable that specifc index : aov_num
            aov_enable_attr = main_rop_node.parm(f"{self.aov_enable}{aov_num}").eval()
            # get the aov label of that specific index :aov_num for primary rop.
            parent_aov_label = (main_rop_node.parm(f"{self.aov_label}{aov_num}").eval())
            
            for child_rop_node in child_rop_nodes:
                # get label parm for each aov 
                child_aovs_labels = [x for x in child_rop_node.parms() if self.aov_label in x.name()]
                
                # if the selected aov already exists on child rop than delete it.
                if del_permission == 1:
                    old_aovs_exist = [x.name() for x in child_aovs_labels if parent_aov_label == x.eval()]
                    if old_aovs_exist:
                        # get index for aov already exists on child rop and remove its instance.
                        aov_del_index = int((old_aovs_exist[0]).replace(self.aov_label, "")[0])
                        child_rop_node.parm(self.aov_count).removeMultiParmInstance(aov_del_index-1)
                
                ############# ADDS COUNT
                # query for aovs count on child rop and +1 , IF primary rop's aov found disable than copies disabled aov.
                child_aov_count = child_rop_node.parm( self.aov_count ).eval()
                child_aov_count += 1
                child_rop_node.parm( self.aov_count ).set(child_aov_count)
                child_rop_node.parm(f"{self.aov_enable}{child_aov_count}").set(aov_enable_attr)
                
                # x.split(str(aov_num))[0]+str(child_aov_count) = attribute_child_aov_count eg : ar_aov_label1
                child_aov_keys =  [ x.split(str(aov_num))[0]+str(child_aov_count) for x in aov_keys if re.match(search_pattern, x)]
                if len(child_aov_keys) == len(aov_values):
                    i = 0
                    for child_aov in child_aov_keys:
                        child_rop_node.parm(child_aov).set(aov_values[i])
                        i += 1
                    print(f"Copied {parent_aov_label} on {child_rop_node.path()}")

class ui( QtWidgets.QDialog , process):
    def __init__(self):
        """
        Produce UI for HtoA AOV Manager.
        """
        super().__init__()
        
        self.script_loc = os.path.abspath(os.path.dirname(__file__))
        self.checkboxes_json_path = os.path.join(self.script_loc, "checkboxes.json")
        self.setWindowIcon(QtGui.QIcon(os.path.join(self.script_loc,"icon/icon.svg")))
        
        self.main_win_width = 450
        self.main_win_height = 600
        
        self.title = get_window_title()
        self.setWindowTitle(self.title)
        self.setMinimumSize(self.main_win_width, self.main_win_height)
        self.setMaximumSize(self.main_win_width, self.main_win_height)#*1.2)

        self.init_attributes()
        self.create_layout()
        self.create_widgets()
        self.create_connections()
        
        # Set parent to Houdini's main window
        self.setParent(hou.ui.mainQtWindow(), QtCore.Qt.Dialog)
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)

    def init_attributes(self):
        """
        Initialize the attributes for create and transfer aovs.
        """
        self.beauty_aovs = [ "RGBA_*", "diffuse_direct", "diffuse_indirect", "emission", "specular_direct", "specular_indirect", "specular_direct_*", "specular_indirect_*", "diffuse_albedo"]
        self.shaders_aovs = [ "coat", "direct", "indirect", "sheen", "sss", "specular"]
        self.tech_aovs = ["Z", "crypto_material", "crypto_object", "N", "P", "Pref", "motionvector", "AO"]
        self.coat_aovs = [ "coat_direct", "coat_indirect", "coat_direct_*", "coat_indirect_*"]
        self.sss_aovs = [ "sss_direct", "sss_indirect", "sss_direct_*", "sss_indirect_*"]
        self.other_aovs = [ "albedo", "specular_albedo", "sss_albedo", "volume_direct", "volume_indirect", "volume_direct_*", "volume_indirect_*", "sheen_direct", "sheen_indirect", "sheen_direct_*", "sheen_indirect_*", "transmission_direct", "transmission_indirect"]
        
        self.aov_count = "ar_aovs"
        self.aov_label = "ar_aov_label"
        self.aov_prefix = "ar_aov"
        self.aov_enable = "ar_enable_aov"

    def add_selection_list(self):
        """
        Checks for the json file and retrieves the information.
        """
        default_items = ["1", "2", "3", "4", "5"]
        with open(self.checkboxes_json_path, 'r') as file:
            data = json.load(file)
            dict_names = data.keys()
            if dict_names:
                list_names = list(dict_names)
                list_names_shorten = [x[0] for x in list_names]
                for default_item in default_items:
                    if default_item in list_names_shorten:
                        pass
                    else:
                        list_names.append(default_item)
            else:
                list_names = default_items
        list_names.sort()
        return(list_names)
        
    def create_layout(self):
        # Create the main layout
        main_layout = QtWidgets.QVBoxLayout()
        
        # Create PRIMARY TAB layout
        self.primary_lay_tabs  = QtWidgets.QTabWidget()
        
        # Tabs creation for primary tab layout
        self.primary_lay_tab1 = QtWidgets.QWidget()
        self.primary_lay_tab2 = QtWidgets.QWidget()

        # PRIMARY TAB LAYOUT 1
        # main ground for primary tab1 layout 
        self.tab1_main_layout = QtWidgets.QVBoxLayout()
        
        # record adding button's layout - FIRST
        self.rec_widgets_layout = QtWidgets.QHBoxLayout()

        # Initialize tab - SECOND
        self.tabs = QtWidgets.QTabWidget()
        self.main_tab = QtWidgets.QWidget()
        self.extra_tab = QtWidgets.QWidget()
        #self.tabs.resize(300,200)
        
        # Create main tab layout
        self.main_tab_layout = QtWidgets.QVBoxLayout()

        # MAIN TAB AOVs LAYOUT
        self.beauty_box_layout, self.beauty_scroll_layout = self.child_layout( "Beauty AOVs", True )
        self.shader_box_layout, self.shader_scroll_layout = self.child_layout( "Shader AOVs", True )
        self.tech_box_layout, self.tech_scroll_layout = self.child_layout( "Technical AOVs" , True)
        
        # Create extra tab layout
        self.extra_tab_layout = QtWidgets.QVBoxLayout()

        # EXTRA TAB AOVs LAYOUT
        self.coat_box_layout, self.coat_scroll_layout = self.child_layout( "Coat AOVs", False )
        self.sss_box_layout, self.sss_scroll_layout = self.child_layout( "SSS AOVs" , False)
        self.other_box_layout, self.other_scroll_layout = self.child_layout( "Other AOVs" , False)
        
        # execution of creation of AOVs Layout - THIRD
        self.btn_widgets_layout = QtWidgets.QHBoxLayout()

        # adding primary tab layout widget in main layout
        main_layout.addWidget(self.primary_lay_tabs)
        
        # Add tabs to primary tabs layout
        self.primary_lay_tabs.addTab(self.primary_lay_tab1,"Create AOVs")
        self.primary_lay_tabs.addTab(self.primary_lay_tab2,"Copy AOVs")

        # adding layouts and widgets for first primary tab 1
        self.primary_lay_tab1.setLayout(self.tab1_main_layout)
        
        self.tab1_main_layout.addLayout(self.rec_widgets_layout)
        self.tab1_main_layout.addWidget(self.tabs)
        self.tab1_main_layout.addLayout(self.btn_widgets_layout)

        # Add AOVs tabs to tabs layout
        self.tabs.addTab(self.main_tab,"Main AOVs")
        self.tabs.addTab(self.extra_tab,"Extra AOVs")

        self.main_tab.setLayout(self.main_tab_layout)

        # Add the group box of main aovs to the main tab layout
        self.main_tab_layout.addWidget(self.beauty_box_layout)
        self.main_tab_layout.addWidget(self.shader_box_layout)
        self.main_tab_layout.addWidget(self.tech_box_layout)

        self.extra_tab.setLayout(self.extra_tab_layout)
        
        # Add the group box of main aovs to the extra tab layout
        self.extra_tab_layout.addWidget(self.coat_box_layout)
        self.extra_tab_layout.addWidget(self.sss_box_layout)
        self.extra_tab_layout.addWidget(self.other_box_layout)

        # PRIMARY TAB LAYOUT 2
        # main ground for primary tab2 layout 
        self.tab2_main_layout = QtWidgets.QVBoxLayout()

        # adding layouts and widgets for first primary tab 1
        self.primary_lay_tab2.setLayout(self.tab2_main_layout)

        # Layout for retrieving of main rop to copy from 
        self.rop_get_node_layout = QtWidgets.QHBoxLayout()
        
        # Layout for retrieving of child rops to copy aovs on 
        self.rop_set_node_layout = QtWidgets.QHBoxLayout()
        
        # aovs list layout vertical box
        self.aovs_layout = QtWidgets.QVBoxLayout()
        
        # executer for transfer aovs 
        self.aov_set_node_layout = QtWidgets.QHBoxLayout()
        
        self.tab2_main_layout.addLayout(self.rop_get_node_layout)
        self.tab2_main_layout.addLayout(self.rop_set_node_layout)
        self.tab2_main_layout.addLayout(self.aovs_layout)
        self.tab2_main_layout.addLayout(self.aov_set_node_layout)

        # Set the main layout for the dialog
        self.setLayout(main_layout)

    def child_layout(self, title , checked_status):
        # Create the Beauty AOVs group box
        box_layout = QtWidgets.QGroupBox( title )
        box_layout.setCheckable(True)
        box_layout.setChecked(checked_status)

        # Create a QScrollArea
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)  # Make it resize with the dialog
        
        # Create a widget to hold the contents of the scroll area
        scroll_widget = QtWidgets.QWidget()
        scroll_layout = QtWidgets.QVBoxLayout(scroll_widget)  # Set layout for the scroll widget

        # Set the scroll widget as the widget for the scroll area
        scroll_area.setWidget(scroll_widget)

        # Add the scroll area to the group box layout
        box_layout.setLayout(QtWidgets.QVBoxLayout())
        box_layout.layout().addWidget(scroll_area)
        
        return box_layout, scroll_layout
        
    def create_widgets(self):
        # Create widgets for Save Selection, Reset Records and Recorder. -PRIMARY TAB 1
        self.save_btn_widget = QtWidgets.QPushButton("Save Selection")
        self.reset_btn_widget = QtWidgets.QPushButton("Reset Records")
        self.rec_combobox_widget = QtWidgets.QComboBox()
        self.rec_combobox_widget.addItems( self.add_selection_list())#####
        self.rec_widgets_layout.addWidget(self.save_btn_widget, 33)
        self.rec_widgets_layout.addWidget(self.reset_btn_widget, 33)
        self.rec_widgets_layout.addWidget(self.rec_combobox_widget, 33)
        self.loadCheckboxStates()

        # Create widgets for aovs elements -PRIMARY TAB 1
        beauty_widgets = self.create_aovs_elements(self.beauty_aovs, self.beauty_scroll_layout, True)
        shaders_widgets = self.create_aovs_elements(self.shaders_aovs, self.shader_scroll_layout, True)
        tech_widgets = self.create_aovs_elements(self.tech_aovs, self.tech_scroll_layout, True)
        coat_widgets = self.create_aovs_elements(self.coat_aovs, self.coat_scroll_layout, False)
        sss_widgets = self.create_aovs_elements(self.sss_aovs, self.sss_scroll_layout, False)
        other_widgets = self.create_aovs_elements(self.other_aovs, self.other_scroll_layout, False)
        
        # Create execution widgets OK, Cancel and extender -PRIMARY TAB 1
        self.ok_btn_widget = QtWidgets.QPushButton("OK")
        self.cancel_btn_widget = QtWidgets.QPushButton("Cancel")
        self.extender_btn_widget = QtWidgets.QPushButton("+")
        self.btn_widgets_layout.addWidget(self.ok_btn_widget, 45)
        self.btn_widgets_layout.addWidget(self.cancel_btn_widget, 45)
        self.btn_widgets_layout.addWidget(self.extender_btn_widget, 10)

        # added button and lineedit for selection of primary rop -PRIMARY TAB 2
        self.parent_lbtn = QtWidgets.QPushButton( 'Copy AOVs FROM :')
        self.parent_lbtn.setToolTip('<b>LMB</b> to add a Arnold ROP <b>RMB</b> to clear.')
        self.parent_lbtn.setFlat(True)
        self.parent_linedit = QtWidgets.QLineEdit(frame=False)
        self.parent_linedit.setFixedSize(self.main_win_width/2, 40)
        self.parent_linedit.setReadOnly(True)

        # added button and textedit for selection of child rops -PRIMARY TAB 2
        self.child_lbtn = QtWidgets.QPushButton( 'Copy AOVs TO :     ')
        self.child_lbtn.setToolTip('<b>LMB</b> to add a Arnold ROP <b>RMB</b> to clear.')
        self.child_lbtn.setFlat(True)
        self.child_linedit = QtWidgets.QTextEdit()
        self.child_linedit.setFixedSize(self.main_win_width/2, 80)
        self.child_linedit.setReadOnly(True)

        # buttons, lineedit and textedits adding widgets followed by list widgets
        self.rop_get_node_layout.addWidget(self.parent_lbtn)
        self.rop_get_node_layout.addWidget(self.parent_linedit)
        self.rop_set_node_layout.addWidget(self.child_lbtn)
        self.rop_set_node_layout.addWidget(self.child_linedit)

        # AOVs List Widget Layout 
        self.aovs_list_widgets = QtWidgets.QListWidget()
        self.aovs_list_widgets.setFixedHeight(350)
        self.aovs_list_widgets.setSelectionMode(QtWidgets.QListWidget.MultiSelection)
        self.aovs_layout.addWidget(self.aovs_list_widgets)

        # buttons for actions for copying aovs
        self.select_all_btn = QtWidgets.QPushButton("select all")
        self.select_none_btn = QtWidgets.QPushButton("select none")
        self.aovs_accept_btn = QtWidgets.QPushButton("accept")
        self.aovs_cancel_btn = QtWidgets.QPushButton("cancel")
        
        # added action buttons to layout for copying aovs
        self.aov_set_node_layout.addWidget(self.select_all_btn)
        self.aov_set_node_layout.addWidget(self.select_none_btn)
        self.aov_set_node_layout.addStretch()
        self.aov_set_node_layout.addWidget(self.aovs_accept_btn)
        self.aov_set_node_layout.addWidget(self.aovs_cancel_btn)
        
    def create_aovs_elements(self, aovs, scroll_layout, checked_status):
        for i in aovs:
            aov_widget = QtWidgets.QCheckBox(f"{i}")
            aov_widget.setObjectName(f"{i}")
            aov_widget.setChecked(checked_status)
            scroll_layout.addWidget(aov_widget) 

    def create_connections(self):
        # Create onnections between widgets and functions . -PRIMARY TAB 1
        self.beauty_box_layout.mousePressEvent = lambda event: self.handle_groupbox_click(event, self.beauty_box_layout)
        self.shader_box_layout.mousePressEvent = lambda event: self.handle_groupbox_click(event, self.shader_box_layout)
        self.tech_box_layout.mousePressEvent = lambda event: self.handle_groupbox_click(event, self.tech_box_layout)
        self.coat_box_layout.mousePressEvent = lambda event: self.handle_groupbox_click(event, self.coat_box_layout)
        self.sss_box_layout.mousePressEvent = lambda event: self.handle_groupbox_click(event, self.sss_box_layout)
        self.other_box_layout.mousePressEvent = lambda event: self.handle_groupbox_click(event, self.other_box_layout)
        
        self.ok_btn_widget.mousePressEvent = lambda event: self.on_ok_btn_pressed(event)
        self.cancel_btn_widget.clicked.connect( self.on_cancel_btn_pressed )
        self.extender_btn_widget.clicked.connect( self.on_extender_btn_pressed )
        
        self.save_btn_widget.clicked.connect(self.saveCheckboxStates)
        self.reset_btn_widget.clicked.connect(self.resetCheckboxStates)
        self.rec_combobox_widget.currentIndexChanged.connect(self.loadCheckboxStates)
        
        # Create onnections between widgets and functions . -PRIMARY TAB 2
        self.parent_lbtn.mousePressEvent = lambda event: self.get_parent_rop_aovs(event, self.parent_linedit, self.aovs_list_widgets)
        self.child_lbtn.mousePressEvent = lambda event: self.get_children_rop_aovs(event, self.child_linedit)
        self.select_all_btn.mousePressEvent = ( lambda event : self.select_all_aovs_list(event) )
        self.select_none_btn.clicked.connect( lambda : self.aovs_list_selection(0) )
        self.aovs_accept_btn.mousePressEvent = ( lambda event : self.copy_aovs_btn(event) )
        self.aovs_cancel_btn.clicked.connect( self.on_cancel_btn_pressed )
        
        # TAB Changed action for PRIMARY TABs
        self.primary_lay_tabs.currentChanged.connect(self.reset_size)
        
    def reset_size(self):
        self.setMinimumSize(self.main_win_width, self.main_win_height)
        self.setMaximumSize(self.main_win_width, self.main_win_height)
        self.extender_btn_widget.setText("+") 
            
    def reset2Default(self):
        self.on_groupbox_pressed(self.beauty_box_layout)
        self.on_groupbox_pressed(self.shader_box_layout)
        self.on_groupbox_pressed(self.tech_box_layout)
        self.coat_box_layout.setChecked(False)
        self.sss_box_layout.setChecked(False)
        self.other_box_layout.setChecked(False)
        self.on_groupbox_pressed(self.coat_box_layout)
        self.on_groupbox_pressed(self.sss_box_layout)
        self.on_groupbox_pressed(self.other_box_layout)
        
    def resetCheckboxStates(self):
        data = {}
        with open(self.checkboxes_json_path, 'w') as file:
            json.dump(data, file)
        self.rec_combobox_widget.clear()
        self.rec_combobox_widget.addItems( self.add_selection_list())#####
        self.reset2Default()

    def loadCheckboxStates(self):
        state_name = self.rec_combobox_widget.currentText()
        if state_name:
            try:
                children = self.tabs.findChildren(QtWidgets.QGroupBox)
                all_yes = [ x.setChecked(True) for x in children]
                with open(self.checkboxes_json_path, 'r') as file:
                    data = json.load(file)
                    states = data.get(state_name, {})
                    if states:
                        for key, value in states.items():
                            checkbox = self.tabs.findChild(QtWidgets.QCheckBox, key)
                            if checkbox:
                                checkbox.setChecked(value)
                    else:
                        self.reset2Default()
            except:
                pass

    def input_combo_text(self):
        text, ok = QtWidgets.QInputDialog.getText(self, 'Input', 'Enter text:')
        return(text)

    def saveCheckboxStates(self):
        # Save the current states
        state_name = self.rec_combobox_widget.currentText()
        children = self.tabs.findChildren(QtWidgets.QCheckBox)
        aovs_name = [ x.text() for x in children]
        aovs_value = [ x.isChecked() for x in children]
        
        value = self.input_combo_text()
        if not value:
            pass
        else:
            new_state_name = f"{state_name[0]}_{value}"
            changed_widget = self.rec_combobox_widget.setItemText(self.rec_combobox_widget.currentIndex(), new_state_name)
            if value:
                try:
                    with open(self.checkboxes_json_path, 'r') as file:
                        data = json.load(file)
                        if state_name in data:
                            data.pop(state_name)
                except :
                    data={}
            data[new_state_name] = dict(zip(aovs_name, aovs_value))###
            print(data)
            # Limit to 5 states
            if len(data) > 5:
                data = dict(list(data.items())[-5:])
            with open(self.checkboxes_json_path, 'w') as file:
                json.dump(data, file)
                print("Data saved successfully." + self.checkboxes_json_path)
            print(f"Checkbox states for '{state_name}' saved.")
        
    def on_extender_btn_pressed(self):
        get_title =  self.extender_btn_widget.text() 
        if get_title == "+":
            self.setMinimumSize(self.main_win_width, self.main_win_height*1.2)
            self.setMaximumSize(self.main_win_width, self.main_win_height*1.2)
            self.extender_btn_widget.setText("-")
        else:
            self.reset_size()   

    def on_ok_btn_pressed(self, event):
        check_tab = self.tabs.currentIndex()
        if check_tab == 0:
            list_active_aovs = []
            if self.beauty_box_layout.isChecked() == True:
                children = self.beauty_box_layout.findChildren(QtWidgets.QCheckBox)
                active_aovs = [ x.text() for x in children if x.isChecked() == True]
                list_active_aovs.extend(active_aovs)
            if self.shader_box_layout.isChecked() == True:
                children = self.shader_box_layout.findChildren(QtWidgets.QCheckBox)
                active_aovs = [ x.text() for x in children if x.isChecked() == True]
                list_active_aovs.extend(active_aovs)
            if self.tech_box_layout.isChecked() == True:
                children = self.tech_box_layout.findChildren(QtWidgets.QCheckBox)
                active_aovs = [ x.text() for x in children if x.isChecked() == True]
                list_active_aovs.extend(active_aovs)
        else:
            list_active_aovs = []
            if self.coat_box_layout.isChecked() == True:
                children = self.coat_box_layout.findChildren(QtWidgets.QCheckBox)
                active_aovs = [ x.text() for x in children if x.isChecked() == True]
                list_active_aovs.extend(active_aovs)
            if self.sss_box_layout.isChecked() == True:
                children = self.sss_box_layout.findChildren(QtWidgets.QCheckBox)
                active_aovs = [ x.text() for x in children if x.isChecked() == True]
                list_active_aovs.extend(active_aovs)
            if self.other_box_layout.isChecked() == True:
                children = self.other_box_layout.findChildren(QtWidgets.QCheckBox)
                active_aovs = [ x.text() for x in children if x.isChecked() == True]
                list_active_aovs.extend(active_aovs)
        
        if list_active_aovs:
            if event.button() == QtCore.Qt.LeftButton:
                self.aovs_creation(list_active_aovs, clear_unused=True)
            else:
                self.aovs_creation(list_active_aovs, clear_unused=False)
            #print(f"{len(list_active_aovs)} aovs were selected to add in layers.")
        else:
            QtWidgets.QMessageBox.warning(None, "AOVs Selection", "Please select atleast 1 AOV to work !!!", QtWidgets.QMessageBox.Ok )
        
    def on_cancel_btn_pressed(self):
        self.close()
        
    def on_groupbox_pressed(self, groupbox):
        if groupbox.isChecked() == True:
            children = groupbox.findChildren(QtWidgets.QCheckBox)
            for child in children:
                child.setChecked(True)
        elif groupbox.isChecked() == False:
            children = groupbox.findChildren(QtWidgets.QCheckBox)
            for child in children:
                child.setChecked(False)
        else:
            pass

    def handle_groupbox_click(self, event, groupbox):
        if event.button() == QtCore.Qt.LeftButton:
            if groupbox.isChecked() == False:
                groupbox.setChecked(True)
                self.on_groupbox_pressed(groupbox)
            else:
                groupbox.setChecked(False)
                self.on_groupbox_pressed(groupbox)
        elif event.button() == QtCore.Qt.RightButton:
            if event.modifiers() == QtCore.Qt.ControlModifier: # print(f"Ctl + Right Click detected on checkbox: ")
                if groupbox.isChecked() == True:
                    children = groupbox.findChildren(QtWidgets.QCheckBox)
                    [x.setChecked(True) for x in children]
            else :
                if groupbox.isChecked() == True:
                    children = groupbox.findChildren(QtWidgets.QCheckBox)
                    [x.setChecked(False) for x in children]
        super(QtWidgets.QGroupBox, groupbox).mousePressEvent(event)

    # PRIMARY TAB2
    # UI Information retriver hub ##################################
    def selection_qlist_widgets(self, list_widget, selection=True):
        items = [ list_widget.item(i).setSelected(selection) for i in range(list_widget.count()) ]
        
    def selected_items_qlist_widgets(self, list_widget):
        items_text = [ x for x in list_widget.selectedItems() if x]
        return(items_text)

    def get_qlineedit_widgets(self, line_edit_widget):
        text = line_edit_widget.text()
        return(text)

    def get_qtextedit_widgets(self, text_edit_widget):
        """
        Retrieves the Child ROP(s) from QTextEdit field.
        Args :
            text_edit_widget (parm): A QT Interface parameter to display the child ROP node(s) names.
        Returns :
            list_elem (list): Split the new line and returns out as list.
        """
        text = text_edit_widget.toPlainText()
        if text:
            list_elem = text.split("\n")
            return(list_elem)
        else:
            list_elem = []
            return(list_elem)

    def aovs_list_selection(self, selection=True):
        # Selection for all/none aovs in list widget of interface.
        self.selection_qlist_widgets(self.aovs_list_widgets, selection)

    def select_all_aovs_list(self, event):
        # Selects all aovs from the list widget if left mouse click else only aov enabled aovs will be selected.
        selection = True
        if event.button() == QtCore.Qt.LeftButton:
            self.aovs_list_selection(selection)
        else:
            items = [ self.aovs_list_widgets.item(i).setSelected(selection) for i in range(self.aovs_list_widgets.count()) if "( DISABLE )" not in self.aovs_list_widgets.item(i).text()]            

    def copy_aovs_btn(self, event):
        # If Left mouse btn then delete already existing aovs  
        if event.button() == QtCore.Qt.LeftButton:
            del_permission = 1
        else:
            del_permission = 0

        # Starting for copying aovs action.
        with hou.undos.group("AOVs Copying Action"):
            print("Verifying to Start Process for Copying AOVs")
            
            # gets child rops and primary main rop for execution.
            list_child_rops = self.get_qtextedit_widgets(self.child_linedit)
            main_rop = self.get_qlineedit_widgets(self.parent_linedit)
            try:
                list_child_rops.remove(main_rop)
            except:
                pass

            # gets selected aovs from the list widget. 
            list_selected_aovs_items = self.selected_items_qlist_widgets(self.aovs_list_widgets)
            if not list_child_rops or not list_selected_aovs_items:
                print("Please Add ROPs and select AOVs.")
                self.warning_info("Warning!!!", "Please Add ROPs and select AOVs.")
            else:
                print(f"Copy AOVs From: {main_rop}")
                print(f"Copy AOVs To: {list_child_rops}")
                
                # get selected aovs index from the list widget and aov label.
                aov_elem_index, aov_elem_label = zip(*[(self.aovs_list_widgets.row(x), x.text()) for x in list_selected_aovs_items])
                print(f"List of selected AOVs: {aov_elem_label}")
                list_child_rop_nodes = [hou.node(x) for x in list_child_rops]
                
                # get primary rop node from lineedit
                main_rop_node = hou.node(self.parent_linedit.text())
                self.exec_copy_aovs(del_permission, main_rop_node, aov_elem_index, list_child_rop_nodes) ####################

def main():
    active_windows = list_active_windows()
    if active_windows:
        for window in active_windows:
            window.deleteLater()  # Remove the existing window
    new_ui_instance = ui()  # Create a new instance of the UI
    new_ui_instance.show()  # Show the new instance