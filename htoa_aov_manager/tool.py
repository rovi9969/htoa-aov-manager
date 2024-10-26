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
this script will create arnold aovs from the list of aovs checked over the arnold rops selected.

if you select nothing or not a single arnold rop and run the ok button, it will warn to select the arnold rop,
if the aov is already present then it will skip that to add over rop, 
if any blank or disabled aov found than will be removed.

'''

import hou
from PySide2 import QtCore, QtWidgets, QtGui
#from logic import process

import os

def list_active_windows():
    # Get the main application
    app = QtWidgets.QApplication.instance()
    
    # Retrieve all top-level widgets
    windows = [w for w in app.topLevelWidgets() if w.isWindow()]
    
    # Collect window titles and object names
    window_info = [w for w in windows if w.windowTitle() == " HtoA AOV Manager v1.0 beta"]
    
    return window_info

class process(object):
    def __init__(self):
        #TYPE
        # all RGB
        self.ar_aov_type = 1

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

    # HOUDINI
    def aovs_creation(self, aov_labels):
        selection = hou.selectedNodes()
        if selection:
            for sel in selection:
                if sel.type().name() == "arnold":
                    #print(sel.name())
                    aovs_count = sel.parm("ar_aovs").eval()
                    parms = sel.parms()
                    
                    if aovs_count:
                        aov_enables_list = [x for x in parms if x.name().startswith("ar_enable_aov") and x.name()[-1].isdigit()] 
                        aov_off_enable_val = [ int(x.name().split("ar_enable_aov")[-1])-1 for x in aov_enables_list if x.eval() == False]
                        
                        aov_label_list = [x for x in parms if x.name().startswith("ar_aov_label") and x.name()[-1].isdigit()] 
                        aov_off_label_val = [ int(x.name().split("ar_aov_label")[-1])-1 for x in aov_label_list if x.eval() == ""]

                        non_working_aov_index = list(set(aov_off_label_val+aov_off_enable_val))
                        for index in reversed(non_working_aov_index):
                            sel.parm("ar_aovs").removeMultiParmInstance(index)
                        
                        aovs_count = sel.parm("ar_aovs").eval()
                        parms = sel.parms()
                        aovs = [x.eval() for x in parms if "ar_aov_label" in x.name() ]
                        aovs_create = [x for x in aov_labels if x not in aovs ]
                        counter = 1
                        for aov_create in aovs_create:
                            num = aovs_count + counter
                            sel.parm("ar_aovs").set(num)
                            sel.parm("ar_aov_label" + str(num)).set(aov_create)
                            self.aov_type_mod(aov_create, sel, num)
                            self.aov_precision_mod(aov_create, sel, num)
                            self.aov_filter_mod(aov_create, sel, num)
                            counter += 1
                    else:
                        sel.parm("ar_aovs").set(len(aov_labels))
                        aovs_create = aov_labels
                        counter = 1
                        for aov_create in aovs_create:
                            attr = sel.parm( "ar_aov_label"+str(counter) )
                            attr.set(aov_create)
                            self.aov_type_mod(aov_create, sel, counter)
                            self.aov_precision_mod(aov_create, sel, counter)
                            self.aov_filter_mod(aov_create, sel, counter)
                            counter += 1
                else:
                    QtWidgets.QMessageBox.warning(None, "ROP Selection", "Works only on Arnold ROPs!!!", QtWidgets.QMessageBox.Ok)
        else:
            QtWidgets.QMessageBox.warning(None, "ROP Selection", "Works only on Arnold ROPs!!!", QtWidgets.QMessageBox.Ok)

class ui( QtWidgets.QDialog , process):
    def __init__(self):
        super().__init__()

        self.beauty_aovs = [ "RGBA_*", "diffuse_direct", "diffuse_indirect", "emission", "specular_direct", "specular_indirect", "specular_direct_*", "specular_indirect_*", "diffuse_albedo"]
        self.shaders_aovs = [ "coat", "direct", "indirect", "sheen", "sss", "specular"]
        self.tech_aovs = ["Z", "crypto_material", "crypto_object", "N", "P", "Pref", "motionvector", "AO"]
        self.coat_aovs = [ "coat_direct", "coat_indirect", "coat_direct_*", "coat_indirect_*"]
        self.sss_aovs = [ "sss_direct", "sss_indirect", "sss_direct_*", "sss_indirect_*"]
        self.other_aovs = [ "albedo", "specular_albedo", "sss_albedo", "volume_direct", "volume_indirect", "volume_direct_*", "volume_indirect_*", "sheen_direct", "sheen_indirect", "sheen_direct_*", "sheen_indirect_*", "transmission_direct", "transmission_indirect"]
        
        self.tool_version = "v1.0 beta"
        
        script_loc = os.path.abspath(os.path.dirname(__file__))
        self.setWindowIcon(QtGui.QIcon(os.path.join(script_loc,"icon/icon.svg")));
        
        self.main_win_width = 400
        self.main_win_height = 600
        
        self.title = " HtoA AOV Manager "+self.tool_version
        self.setWindowTitle(self.title)
        self.setMinimumSize(self.main_win_width, self.main_win_height)
        self.setMaximumSize(self.main_win_width, self.main_win_height)#*1.2)
        
        self.create_layout()
        self.create_widgets()
        self.create_connections()

        # Set parent to Houdini's main window
        self.setParent(hou.ui.mainQtWindow(), QtCore.Qt.Dialog)
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        
    def create_layout(self):
        # Create the main layout
        main_layout = QtWidgets.QVBoxLayout()
        
        # Initialize tab screen
        self.tabs = QtWidgets.QTabWidget()
        self.main_tab = QtWidgets.QWidget()
        self.extra_tab = QtWidgets.QWidget()
        #self.tabs.resize(300,200)
        
        # Add tabs
        self.tabs.addTab(self.main_tab,"Main AOVs")
        self.tabs.addTab(self.extra_tab,"Extra AOVs")

        # Create main tab layout
        self.main_tab_layout = QtWidgets.QVBoxLayout()
        self.extra_tab_layout = QtWidgets.QVBoxLayout()
        #self.main_tab_layout.addWidget(self.pushButton1)

        # MAIN AOVs LAYOUT
        self.beauty_box_layout, self.beauty_scroll_layout = self.child_layout( "Beauty AOVs", True )
        self.shader_box_layout, self.shader_scroll_layout = self.child_layout( "Shader AOVs", True )
        self.tech_box_layout, self.tech_scroll_layout = self.child_layout( "Technical AOVs" , True)

        # Add the group box of main aovs to the main tab layout
        self.main_tab_layout.addWidget(self.beauty_box_layout)
        self.main_tab_layout.addWidget(self.shader_box_layout)
        self.main_tab_layout.addWidget(self.tech_box_layout)

        self.btn_widgets_layout = QtWidgets.QHBoxLayout()

        self.coat_box_layout, self.coat_scroll_layout = self.child_layout( "Coat AOVs", False )
        self.sss_box_layout, self.sss_scroll_layout = self.child_layout( "SSS AOVs" , False)
        self.other_box_layout, self.other_scroll_layout = self.child_layout( "Other AOVs" , False)

        self.extra_tab_layout.addWidget(self.coat_box_layout)
        self.extra_tab_layout.addWidget(self.sss_box_layout)
        self.extra_tab_layout.addWidget(self.other_box_layout)
        
        self.main_tab.setLayout(self.main_tab_layout)
        self.extra_tab.setLayout(self.extra_tab_layout)
        
        main_layout.addWidget(self.tabs)
        main_layout.addLayout(self.btn_widgets_layout)
        
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
        beauty_widgets = self.create_aovs_elements(self.beauty_aovs, self.beauty_scroll_layout, True)
        shaders_widgets = self.create_aovs_elements(self.shaders_aovs, self.shader_scroll_layout, True)
        tech_widgets = self.create_aovs_elements(self.tech_aovs, self.tech_scroll_layout, True)
        coat_widgets = self.create_aovs_elements(self.coat_aovs, self.coat_scroll_layout, False)
        sss_widgets = self.create_aovs_elements(self.sss_aovs, self.sss_scroll_layout, False)
        other_widgets = self.create_aovs_elements(self.other_aovs, self.other_scroll_layout, False)
        
        self.ok_btn_widget = QtWidgets.QPushButton("OK")
        self.cancel_btn_widget = QtWidgets.QPushButton("Cancel")
        self.extender_btn_widget = QtWidgets.QPushButton("+")
        self.btn_widgets_layout.addWidget(self.ok_btn_widget, 45)
        self.btn_widgets_layout.addWidget(self.cancel_btn_widget, 45)
        self.btn_widgets_layout.addWidget(self.extender_btn_widget, 10)
            
    def create_aovs_elements(self, aovs, scroll_layout, checked_status):
        # Add some example elements to the scroll area
        for i in aovs:
            aov_widget = QtWidgets.QCheckBox(f"{i}")
            aov_widget.setChecked(checked_status)
            scroll_layout.addWidget(aov_widget) 

    def create_connections(self):
        self.beauty_box_layout.clicked.connect( lambda: self.on_groupbox_pressed(self.beauty_box_layout) )
        self.shader_box_layout.clicked.connect( lambda: self.on_groupbox_pressed(self.shader_box_layout) )
        self.tech_box_layout.clicked.connect( lambda: self.on_groupbox_pressed(self.tech_box_layout) )
        self.coat_box_layout.clicked.connect( lambda: self.on_groupbox_pressed(self.coat_box_layout) )
        self.sss_box_layout.clicked.connect( lambda: self.on_groupbox_pressed(self.sss_box_layout) )
        self.other_box_layout.clicked.connect( lambda: self.on_groupbox_pressed(self.other_box_layout) )
        self.ok_btn_widget.clicked.connect( self.on_ok_btn_pressed )
        self.cancel_btn_widget.clicked.connect( self.on_cancel_btn_pressed )
        self.extender_btn_widget.clicked.connect( self.on_extender_btn_pressed )
        
    def on_extender_btn_pressed(self):
        get_title =  self.extender_btn_widget.text() 
        if get_title == "+":
            self.setMinimumSize(self.main_win_width, self.main_win_height*1.2)
            self.setMaximumSize(self.main_win_width, self.main_win_height*1.2)
            self.extender_btn_widget.setText("-")
        else:
            self.setMinimumSize(self.main_win_width, self.main_win_height)
            self.setMaximumSize(self.main_win_width, self.main_win_height)
            self.extender_btn_widget.setText("+")    

    def on_ok_btn_pressed(self):
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
            print("pressed")
            self.aovs_creation(list_active_aovs)
            print(f"{len(list_active_aovs)} aovs were selected to add in layers.")
        else:
            QtWidgets.QMessageBox.warning(None, "AOVs Selection", "Please select atleast 1 AOV to work !!!", QtWidgets.QMessageBox.Ok )
        
    def on_cancel_btn_pressed(self):
        self.close()
        
    def on_groupbox_pressed(self, groupbox):
        if groupbox.isChecked() == True:
            children = groupbox.findChildren(QtWidgets.QCheckBox)
            for child in children:
                child.setChecked(True)

def main():
    active_windows = list_active_windows()
    #print(active_windows)
    if active_windows:
        for window in active_windows:
            window.deleteLater()  # Remove the existing window
    new_ui_instance = ui()  # Create a new instance of the UI
    new_ui_instance.show()  # Show the new instance
    