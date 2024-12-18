import tkinter as tk
from tkinter import simpledialog
import json
import math
import sys
import os

project_root = os.getcwd()
sys.path.append(project_root)

from backend.scripts.SharedCode import sharedCode

dictFolder = sharedCode.loadSettings("globalSettings", "dictionaryFolderPath") 
dictFile = sharedCode.loadSettings("globalSettings", "mainDictionary")
fileName = project_root + dictFolder + dictFile

nodeRadius = 10
ArrowSize = 4
textOffsetY = 2
maxSliderDepth = 7
searchWidth = 5
    
class Node:
    def __init__(self, node_id, x, y, **kwargs):
        self.id = node_id
        self._idName = node_id
        self.x = x
        self.y = y
        tempValues = {
            "otherFields": {
                "genere": "",
                "grado": "",
                "opposto": "",
                "singolare": ""
            },
            "sig_descr": "",
            "signal": "",
            "sinonimi": []
        }
        self.parents = set(kwargs.get("parents", []))
        self.children = set(kwargs.get("children", []))
        self.values = kwargs.get("values", tempValues)

    def add_parent(self, parent_node):
        if parent_node != self:
            self.parents.add(parent_node.id)
            parent_node.children.add(self.id)

    def add_child(self, child_node):
        if child_node != self:
            self.children.add(child_node.id)
            child_node.parents.add(self.id)

    def move(self, nodes, dx, dy):
        self.x += dx
        self.y += dy
        for child_id in self.children.copy():
            child = nodes.get(child_id)
            if child:
                child.move(nodes, dx, dy)

    def is_root(self):
        return not self.parents


class ForestManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Forest Manager")
        self.canvas = tk.Canvas(self.root, width=800, height=600, bg="white")
        self.canvas.pack(expand=tk.YES, fill=tk.BOTH)

        self.nodes = {}
        self.selected_node = None
        self.scale = 1.0       
        self.load_data()                         # Load existing data from JSON file        
        self.prev_scale = 1.0                    # Add a variable to store the previous scale value        
        self.mouse_wheel_pressed = False         # Flag to track mouse wheel dragging        
        self.prev_drag_pos = None                # Add a variable to store the previous drag position
        self.Flaggy = True                   
        self.last_drag_pos = (0, 0)              # Add a variable to store the last drag position relative to the canvas center
        self.first_drag_after_press = True       # Add a flag to check if it's the first drag after the mouse button is pressed     
        # Add a variable to track the state of position_children_button   
        self.position_children_enabled = tk.BooleanVar()        
        self.position_children_enabled.set(False)        
        # Add a variable to track the state of position_children_button for root nodes
        self.position_children_root_enabled = tk.BooleanVar()   
        self.position_children_root_enabled.set(False)
        # Add a variable to track the state of add_alias_button
        self.add_alias_enabled = tk.BooleanVar()
        self.add_alias_enabled.set(False)
        # Bind events
        self.canvas.bind("<Button-1>", self.handle_click)
        self.canvas.bind("<B1-Motion>", self.handle_drag)
        self.canvas.bind("<B3-Motion>", self.handle_pan)
        self.canvas.bind("<Button-3>", self.start_pan)
        self.canvas.bind("<ButtonRelease-3>", self.stop_pan)
        self.canvas.bind("<MouseWheel>", self.handle_zoom)
        # Add a slider to control the maximum depth of the hierarchy to display
        self.max_depth_slider = tk.Scale(self.root, from_=0, to=maxSliderDepth, orient=tk.HORIZONTAL,
                                         label="Max Depth to Display", length=200)
        self.max_depth_slider.pack(side=tk.RIGHT, padx=10)
        self.max_depth_slider.set(maxSliderDepth)  # Default value
        # Add horizontal scrollbar
        self.xscrollbar = tk.Scrollbar(self.root, orient=tk.HORIZONTAL)
        self.xscrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.xscrollbar.config(command=self.canvas.xview)
        self.canvas.config(xscrollcommand=self.xscrollbar.set)
        # Add vertical scrollbar
        self.yscrollbar = tk.Scrollbar(self.root, orient=tk.VERTICAL)
        self.yscrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.yscrollbar.config(command=self.canvas.yview)
        self.canvas.config(yscrollcommand=self.yscrollbar.set)
        # Add buttons
        buttons_frame = tk.Frame(self.root)
        buttons_frame.pack(side=tk.BOTTOM, fill=tk.X)
        add_node_button = tk.Button(buttons_frame, text="Add Node", command=self.add_node)
        add_node_button.pack(side=tk.LEFT, padx=5)
        delete_node_button = tk.Button(buttons_frame, text="Delete Node", command=self.delete_node)
        delete_node_button.pack(side=tk.LEFT, padx=5)   
     
        # Add a button to trigger save_connected_nodes function
        save_connected_nodes_button = tk.Button(buttons_frame, text="Save Connected Nodes", command=self.save_connected_nodes)
        save_connected_nodes_button.pack(side=tk.LEFT, padx=5)
        # Add a button to trigger load_json_file function
        load_json_button = tk.Button(buttons_frame, text="Load JSON File", command=self.load_json_file)
        load_json_button.pack(side=tk.LEFT, padx=5)



        # Add a "Reload" button
        reload_button = tk.Button(buttons_frame, text="Reload", bg="red", command=self.reload_data)
        reload_button.pack(side=tk.LEFT, padx=5) 
        # Add a "Save" button
        reload_button = tk.Button(buttons_frame, text="Save", bg="yellow", command=self.save_data)
        reload_button.pack(side=tk.LEFT, padx=5)
        # Add a text area for displaying the current selected node
        self.output_text = tk.Text(self.root, height=6, width=70, state=tk.DISABLED)
        self.output_text.pack(side=tk.RIGHT, padx=10, pady=10)
        # Add a variable to track the state of connect_nodes_button
        self.connect_nodes_enabled = tk.BooleanVar()
        self.connect_nodes_enabled.set(False)
        # Add a button to toggle position children functionality
        self.position_children_button = tk.Checkbutton(
            buttons_frame, text="Position Children", variable=self.position_children_enabled,
            command=self.toggle_position_children)
        self.position_children_button.pack(side=tk.LEFT, padx=5)        
        # Add a button to toggle add alias functionality
        self.add_alias_button = tk.Button(
            buttons_frame, text="Add Alias", command=self.toggle_add_alias, bg="lightgrey", activebackground="green")
        self.add_alias_button.pack(side=tk.LEFT, padx=5)
        # Add a button to trigger the search function
        search_button = tk.Button(self.root, text="Search", command=self.search_item)
        search_button.pack(side=tk.RIGHT, padx=5)
        # Add an entry widget for the search box
        self.search_entry = tk.Entry(self.root)
        self.search_entry.pack(side=tk.RIGHT, padx=5)      
        # Add a button to connect nodes and change its color when pressed
        self.connect_nodes_button = tk.Button(
            buttons_frame, text="Connect Nodes", command=self.toggle_connect_nodes,
            bg="lightgrey", activebackground="green")
        self.connect_nodes_button.pack(side=tk.LEFT, padx=5)
        edit_node_button = tk.Button(buttons_frame, text="Edit Node", bg="lightgreen", command=self.edit_node)
        edit_node_button.pack(side=tk.LEFT, padx=5)
        remove_connection_button = tk.Button(buttons_frame, text="Remove Connection", bg="lightyellow", command=self.remove_connection)
        remove_connection_button.pack(side=tk.LEFT, padx=5)                     
        self.reload_data() # Initial setup for scale value in output_text


    def save_connected_nodes(self):
        if self.selected_node:
            # Prompt user for new file name
            new_file_name = tk.simpledialog.askstring("Save Connected Nodes", "Enter the new file name:")
            if new_file_name:
                # Construct a dictionary containing connected nodes
                connected_nodes = {"nodes": []}
                visited_nodes = set()
                def traverse(node):                    
                    if node and node.id not in visited_nodes:
                        visited_nodes.add(node.id)
                        valid_parents = ([parent_id for parent_id in node.parents if self.nodes.get(parent_id)])
                        node_data = {
                            "id": node.id,
                            "x": node.x,
                            "y": node.y,
                            "parents": valid_parents,
                            "children": list(node.children),
                            "_idName": node._idName,
                            "values": node.values
                        }
                        connected_nodes["nodes"].append(node_data)
                        
                        for child_id in node.children:
                            traverse(self.nodes.get(child_id))
                traverse(self.selected_node)
                # Save the connected nodes to a new JSON file
                print(connected_nodes)
                json.dump(connected_nodes, open(new_file_name + ".json", 'w', encoding="utf-8"), ensure_ascii=False, sort_keys=True)


    def load_json_file_old(self):        
        # Prompt user to select a JSON file
        file_path = tk.filedialog.askopenfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            # Read the contents of the JSON file
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

            if(data):
                # Dictionary to store created nodes based on their IDs
                created_nodes = {}
                # Create nodes without connecting them
                for node_id, node_data in data.items(): 
                    print("Node Data:", node_data)
                    node = Node(node_id, float(node_data["x"]), float(node_data["y"]), values=node_data.get("values", []))
                    created_nodes[node_id] = node
                # Connect nodes (assuming you have parent-child relationships in your JSON data)
                for node_id, node_data in data.items():
                    node = created_nodes[node_id]
                    for child_id in node_data.get("children", []):
                        child_node = created_nodes[child_id]
                        node.add_child(child_node)
                # Optionally, clear the existing graph before adding nodes from the loaded file
                self.nodes.clear()
                # Add nodes to the graph
                for node_id, node in created_nodes.items():
                    self.add_node(node)
                # Redraw the canvas or perform any necessary actions
                self.redraw_canvas()

    def load_json_file(self):
        # Prompt user to select a JSON file
        file_path = tk.filedialog.askopenfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            # Read the contents of the JSON file
            with open(file_path, 'r', encoding='utf-8') as file:
                loaded_data = json.load(file)
            # Clear existing nodes and canvas
            # Update graph based on loaded data
            for node_data in loaded_data.get("nodes", []):
                # Adjust node id to avoid conflicts
                node_id = f"{node_data['id']}_loaded"
                # Example of creating a Node instance with additional attributes
                node = Node(node_id, node_data["x"], node_data["y"], parents = node_data["parents"] , children = node_data["children"] ,values = node_data["values"])
                #node.id_name = node_data["_idName"]  # Set id_name separately
                self.nodes[node.id] = node
                print("Node Data:", node_data)

    def search_item(self):
        # Get the search text from the entry widget
        search_text = self.search_entry.get().strip() 
        signal_text = ""
        display_text = ""     
        if search_text:
            current_width = root.winfo_width() / 2
            current_height = root.winfo_height() / 2
            for node in self.nodes.values():
                if("?" in search_text):
                    if(node.id.lower().startswith (search_text.replace("?","").lower())):
                        x = node.x * self.scale
                        y = node.y * self.scale
                        radius = nodeRadius * 2 * self.scale  # Double the current radius
                        self.canvas.create_oval(x - 2 * radius, y - 2 * radius, x + 2 * radius, y + 2 * radius, outline="red", width=searchWidth, stipple="gray50", tags="search_circle")
                        signal_text = node.values.get("signal")#self.selected_node.values.get("signal", "No SIGNAL") if self.selected_node else "No SIGNAL"
                        display_text += f"{node.id}  - SIGNAL: {signal_text}\n"   
                        self.draw_arrow(current_width, current_height, x, y, searchWidth, "green")    
                elif("!" in search_text):
                    if((search_text.replace("!","").lower()) in node.id.lower()):
                        x = node.x * self.scale
                        y = node.y * self.scale
                        radius = nodeRadius * 2 * self.scale  # Double the current radius
                        self.canvas.create_oval(x - 2 * radius, y - 2 * radius, x + 2 * radius, y + 2 * radius, outline="red", width=searchWidth, stipple="gray50", tags="search_circle")
                        signal_text = node.values.get("signal")#self.selected_node.values.get("signal", "No SIGNAL") if self.selected_node else "No SIGNAL"
                        display_text += f"{node.id}  - SIGNAL: {signal_text}\n"   
                        self.draw_arrow(current_width, current_height, x, y, searchWidth, "green")    
                else:
                    if search_text == node.id:
                        x = node.x * self.scale
                        y = node.y * self.scale
                        radius = nodeRadius * 2 * self.scale  # Double the current radius
                        self.canvas.create_oval(x - 2 * radius, y - 2 * radius, x + 2 * radius, y + 2 * radius, outline="red", width=searchWidth, stipple="gray50", tags="search_circle")
                        signal_text = node.values.get("signal")#self.selected_node.values.get("signal", "No SIGNAL") if self.selected_node else "No SIGNAL"
                        display_text = f"{node.id} - SIGNAL: {signal_text}\n"     
                        self.draw_arrow(current_width, current_height, x, y, searchWidth, "green")  
                        break  # Stop searching after finding the first match                
            self.output_text.insert(tk.END, display_text)   
            self.output_text.config(state=tk.NORMAL)
            self.output_text.delete(1.0, tk.END) 
            self.output_text.insert(tk.END, display_text)
            self.output_text.config(state=tk.DISABLED)          
        else:
            self.canvas.delete("search_circle")

    def toggle_add_alias(self):
        self.add_alias_enabled = not self.add_alias_enabled
        if self.add_alias_enabled:
            self.add_alias_button.config(bg="green", activebackground="lightgrey")
        else:
            self.add_alias_button.config(bg="lightgrey", activebackground="green")

    def handle_add_alias(self, event):
        if self.selected_node:
            # Get all items within the radius from the event coordinates
            items = self.canvas.find_overlapping(event.x, event.y, event.x, event.y)
            # Filter out non-node items
            node_items = [item for item in items if "node" in self.canvas.gettags(item)]
            if node_items:
                # Select the target node based on the event coordinates
                target_node_item = node_items[0]
                target_node_id = self.canvas.gettags(target_node_item)[0]
                target_node = self.nodes.get(target_node_id)
                if target_node and target_node != self.selected_node:
                    # Add current node's ID as "sinonimi" to the target node
                    target_node.values["sinonimi"].append(self.selected_node.id.lower().strip())
                    # Remove current node
                    del self.nodes[self.selected_node.id]
                    self.selected_node = None
                    self.draw_nodes()

    def reload_data(self):
        self.add_alias_enabled = False
        self.connect_nodes_enabled = False
        # Reload the data from the JSON file
        self.nodes.clear()
        self.load_data()
        self.draw_nodes()
        self.update_scale_output()

    def update_scale_output(self):
        # Display the current scale value in the text area
        scale_value = f"Current Scale: {self.scale:.2f}"
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, scale_value)
        self.output_text.config(state=tk.DISABLED)

    def handle_mouse_wheel(self, event):
        # Adjust the scale based on mouse wheel movement
        factor = 1.1 if event.delta > 0 else 0.9
        self.change_scale(factor)
        self.update_scroll_region()

    def update_scroll_region(self):
        # Update the scroll region based on the canvas content
        self.canvas.update_idletasks()
        bbox = self.canvas.bbox("all")
        self.canvas.config(scrollregion=bbox)

    def start_pan(self, event):
        self.mouse_wheel_pressed = True
        self.first_drag_after_press = True
       
    def move_root_nodes(self, dx, dy):
        for node in self.nodes.values():
            if node.is_root():
                node.move(self.nodes, dx, dy)


    def handle_pan(self, event):
        if self.prev_drag_pos is not None:  
            if (self.first_drag_after_press == True):            
                self.last_drag_pos = (self.prev_drag_pos[0] - current_width, self.prev_drag_pos[1] - current_height)#self.prev_drag_pos
                self.first_drag_after_press = False
                self.prev_drag_pos = (event.x, event.y)
            dx = ((event.x - self.prev_drag_pos[0])) / self.scale
            dy = ((event.y - self.prev_drag_pos[1])) / self.scale       
            self.move_root_nodes(dx, dy)
            self.draw_nodes()
        self.prev_drag_pos = (event.x, event.y)
        # Reset the previous drag position to avoid large coordinate values
        if abs(self.prev_drag_pos[0]) > 1e6 or abs(self.prev_drag_pos[1]) > 1e6:
            self.prev_drag_pos = (event.x, event.y)

    def stop_pan(self, event):
        self.mouse_wheel_pressed = False
        self.first_drag_after_press = False  # Reset the flag on mouse button release

    def toggle_edit_connection(self):
        self.edit_connection_enabled = not self.edit_connection_enabled
        color = "green" if self.edit_connection_enabled else "grey"
        self.edit_connection_button.config(bg=color)

    def handle_click(self, event):
        # Define a radius for node selection
        selection_radius = 20
        # Get all items within the radius from the event coordinates
        items = self.canvas.find_overlapping(event.x - selection_radius, event.y - selection_radius,
                                            event.x + selection_radius, event.y + selection_radius)
        # Filter out non-node items
        node_items = [item for item in items if "node" in self.canvas.gettags(item)]
        if node_items:
            # Select the closest node based on the event coordinates
            closest_node_item = min(node_items, key=lambda item: self.distance_to_event(item, event))
            node_id = self.canvas.gettags(closest_node_item)[0]
            self.selected_node = self.nodes[node_id]
        else:
            self.selected_node = None
        self.draw_nodes()

    def distance_to_event(self, item, event):
        # Calculate the distance between the item's center and the event coordinates
        x, y = self.canvas.coords(item)[:2]  # Take the top-left corner coordinates
        item_center_x = x + 20  # Assuming a fixed radius of 20 for the oval
        item_center_y = y + 20  # Assuming a fixed radius of 20 for the oval
        return ((item_center_x - event.x) ** 2 + (item_center_y - event.y) ** 2) ** 0.5


    def handle_drag(self, event):
        if self.selected_node:
            dx = (event.x - self.selected_node.x * self.scale) / self.scale
            dy = (event.y - self.selected_node.y * self.scale) / self.scale
            self.selected_node.move(self.nodes, dx, dy)            
            # Check if add alias functionality is enabled
            if self.add_alias_enabled:
                self.handle_add_alias(event)
            elif self.connect_nodes_enabled:
                self.handle_connect_nodes(event)                
            self.draw_nodes()
        elif event.x_root != self.root.winfo_pointerx() or event.y_root != self.root.winfo_pointery():
            # Click and drag on empty space to move all items/canvas
            dx = (event.x - self.root.winfo_pointerx()) / self.scale
            dy = (event.y - self.root.winfo_pointery()) / self.scale
            self.draw_nodes()


    def handle_connect_nodes(self, event):
        if self.selected_node:
            # If both nodes have no children or parents, create a connection
            if not self.selected_node.parents and not self.selected_node.children:
                for node in self.nodes.values():
                    if node != self.selected_node:
                        distance = ((node.x * self.scale - event.x) / self.scale) ** 2 + (
                                (node.y * self.scale - event.y) / self.scale) ** 2
                        if distance < 20 ** 2:
                            node.add_child(self.selected_node)
                            # Set the signal of the target node as the signal for the selected node
                            if not self.selected_node.values.get("signal") and self.selected_node.values.get("sig_descr"):
                                self.selected_node.values["signal"] = node.id.replace("_Collection","").upper()
                                self.save_data()                                 
                            self.draw_nodes()
                            return
            else:
                # If the selected node has no parent or child, it becomes the child of the node dragged onto
                for node in self.nodes.values():
                    if node != self.selected_node:
                        distance = ((node.x * self.scale - event.x) / self.scale) ** 2 + (
                                (node.y * self.scale - event.y) / self.scale) ** 2
                        if distance < 20 ** 2:
                            self.selected_node.add_parent(node)
                            # Set the signal of the target node as the signal for the selected node
                            if not self.selected_node.values.get("signal") and self.selected_node.values.get("sig_descr"):
                                #self.selected_node.values["signal"] = self.id.replace("_Collection","").upper()
                                self.selected_node.values["signal"] = node.id.replace("_Collection","").upper()
                                self.save_data()                                   
                            self.draw_nodes()
                            return

    def handle_zoom(self, event):
        factor = 1.1 if event.delta > 0 else 0.9
        self.change_scale(factor)

    def add_node(self):
        node_id = tk.simpledialog.askstring("Add Node", "Enter Node ID:")
        if node_id and node_id not in self.nodes:
            new_node = Node(node_id, 100, 100)
            self.nodes[node_id] = new_node
            self.nodes_idName = self.nodes[node_id]
            self.draw_nodes()

    def edit_node(self):
        if self.selected_node:
            self.show_edit_node_dialog()

    def show_edit_node_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Node")
        # Create entry widgets for each field including id and _idName
        self.create_entry_widgets(dialog, self.selected_node.values, [])
        self.create_entry_widgets(dialog, {"id": self.selected_node.id, "_idName": self.selected_node._idName}, [])
        # Save button
        save_button = tk.Button(dialog, text="Save", command=lambda: self.save_edit_node(dialog))
        save_button.pack()

    def create_entry_widgets(self, parent, values, path):
        for key, value in values.items():
            if isinstance(value, dict):
                self.create_entry_widgets(parent, value, path + [key])
            else:
                frame = tk.Frame(parent)
                frame.pack(fill=tk.X)
                label = tk.Label(frame, text=".".join(path + [key]).capitalize())
                label.pack(side=tk.LEFT)
                entry = tk.Entry(frame)
                entry.pack(side=tk.LEFT)
                setattr(self, f"{key}_entry", entry)
                # Populate array fields with comma-separated values
                if isinstance(value, list):
                    entry.insert(0, ",".join(map(str, (item for item in value))))
                else:
                    entry.insert(0, str(value))

    def save_edit_node(self, dialog):
        self.update_values_from_entries(self.selected_node.values)
        self.selected_node.id = self.id_entry.get()  # Update the id field
        self.selected_node._idName = self._idName_entry.get()  # Update the _idName field
        dialog.destroy()
        self.draw_nodes()
        self.save_data()
      
    def update_values_from_entries(self, values):
        for key, value in values.items():     
            if isinstance(value, dict):
                self.update_values_from_entries(value)
            else:
                entry = getattr(self, f"{key}_entry", None)
                if entry:   
                    entryValue = entry.get()                             
                    if(key=="signal"):
                        entryValue = entryValue.upper()                  
                    if(key=="sinonimi"):  
                        entryValue = list(set([x.strip().lower() for x in entryValue.split(",")]))
                    values[key] = entryValue
        # Remove empty elements from array fields
        for key, value in values.items():
            if isinstance(value, list):
                values[key] = [item for item in value if item]

    def toggle_connect_nodes(self):
        self.connect_nodes_enabled = not self.connect_nodes_enabled
        # Adjust the color based on the state
        if self.connect_nodes_enabled:
            self.connect_nodes_button.config(bg="green", activebackground="lightgrey")
        else:
            self.connect_nodes_button.config(bg="lightgrey", activebackground="green")

    def remove_connection(self):
        if self.selected_node:
            target_id = tk.simpledialog.askstring("Remove Connection", "Enter Target Node ID:")
            if target_id in self.selected_node.children:
                target_node = self.nodes.get(target_id)
                if target_node:
                    self.selected_node.children.remove(target_id)
                    target_node.parents.remove(self.selected_node.id)
                    self.draw_nodes()
                    self.save_data()

    def delete_node(self):
        if self.selected_node:
            del self.nodes[self.selected_node.id]
            for node in self.nodes.values():
                if self.selected_node.id in node.children:
                    node.children.remove(self.selected_node.id)
                if self.selected_node.id in node.parents:
                    node.parents.remove(self.selected_node.id)
            self.selected_node = None
            self.draw_nodes()
            self.save_data()

    def change_scale(self, factor):
        self.scale *= factor
        self.draw_nodes()

    def toggle_position_children(self):
        # Toggle the state of position_children_enabled
        self.position_children_enabled.set(not self.position_children_enabled.get())
        self.draw_nodes()  # Redraw nodes after toggling

    def position_children(self, parent, node, num_children):
        # Calculate positions around the parent at a constant distance
        radius = 100 * self.scale  # You can adjust the radius as needed
        angle_increment = 360 / num_children
        positions = []
        for i in range(num_children):
            angle = i * angle_increment
            x = parent.x * self.scale + radius * math.cos(math.radians(angle))
            y = parent.y * self.scale + radius * math.sin(math.radians(angle))
            positions.append((x, y))
        return positions

    def draw_nodes(self):     
        self.canvas.delete("all")
        # Calculate the depth of each node's relationship
        depths = {node_id: self.calculate_depth(node_id) for node_id in self.nodes}
        # Determine the maximum depth based on the slider value
        max_depth = int(self.max_depth_slider.get())
        # Draw connections first
        for node in self.nodes.values():
            current_depth = depths[node.id]
            # Check if the current depth exceeds the maximum depth
            if current_depth <= max_depth:
                for parent_id in node.parents:
                    parent = self.nodes[parent_id]
                    parent_depth = depths[parent_id]
                    # Check if the parent depth exceeds the maximum depth
                    if parent_depth <= max_depth:
                        x1, y1 = parent.x * self.scale, parent.y * self.scale
                        x2, y2 = node.x * self.scale, node.y * self.scale
                        thickness = ArrowSize / (depths[parent.id] + 1)  # Adjust thickness based on depth
                        color = self.get_color_based_on_depth(depths[parent.id])
                        self.draw_arrow(x1, y1, x2, y2, thickness, color)
                        # Position children around parents if enabled
                        if self.position_children_enabled.get() and not self.position_children_root_enabled.get():
                            child_positions = self.position_children(parent, node, len(node.children))
                            for i, child_id in enumerate(node.children):
                                child = self.nodes[child_id]
                                child.x, child.y = child_positions[i]
                        elif self.position_children_root_enabled.get() and node.is_root():
                            # Distribute children around root node at a constant distance
                            child_positions = self.position_children_root(node, len(node.children))
                            for i, child_id in enumerate(node.children):
                                child = self.nodes[child_id]
                                child.x, child.y = child_positions[i]            
        # Draw semi-transparent circle around the selected node
        if self.selected_node:
            x = self.selected_node.x * self.scale
            y = self.selected_node.y * self.scale
            radius = nodeRadius * self.scale
            self.canvas.create_oval(x - 2 * radius, y - 2 * radius, x + 2 * radius, y + 2 * radius, outline="blue", width=2, stipple="gray50")
        # Draw nodes and text
        for node in self.nodes.values():
            current_depth = depths[node.id]
            # Check if the current depth exceeds the maximum depth
            if current_depth <= max_depth:
                x = node.x * self.scale
                y = node.y * self.scale
                radius = nodeRadius * self.scale
                # Draw the node
                self.canvas.create_oval(x - radius, y - radius, x + radius, y + radius, tags=(node.id, "node"))
                #self.canvas.create_oval(x - radius /(2*current_depth+1), y - radius /(2*current_depth+1), x + radius /(2*current_depth+1), y + radius /(2*current_depth+1), tags=(node.id, "node"))
                # Draw text above the node
                self.canvas.create_text(x, y - (radius + textOffsetY) / 1, text=node.id, tags=(node.id, "node"))        
        # Display the current selected node in the text area
        selected_node_id = self.selected_node.id if self.selected_node else "None"
        #if not search_text:
        signal_text = self.selected_node.values.get("signal", "No Signal!") if self.selected_node else ""
        signalDescr_text = self.selected_node.values.get("sig_descr", "No Descr") if self.selected_node else ""
        sinonimi_text = self.selected_node.values.get("sinonimi", "No sinonimi") if self.selected_node else ""
        if(len(sinonimi_text) != 0):
            sinonimi_text = ",".join(map(str, (item for item in sinonimi_text)))
        display_text = f"Selected Node: {selected_node_id}\nSegnale: {signal_text}\nDescrizione: {signalDescr_text}\nSinonimi: {sinonimi_text}\n\nCurrent Scale: {self.scale}"
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END) 
        self.output_text.insert(tk.END, display_text)
        self.output_text.config(state=tk.DISABLED)    

    def toggle_position_children_root(self):
        # Toggle the state of position_children_root_enabled
        self.position_children_root_enabled.set(not self.position_children_root_enabled.get())
        self.draw_nodes()

    def position_children_root(self, root, num_children):
        # Calculate positions around the root in a circular manner at a constant distance
        radius = nodeRadius*2 * self.scale  # You can adjust the radius as needed
        angle_increment = 360 / num_children
        positions = []
        for i in range(num_children):
            angle = i * angle_increment
            x = root.x * self.scale + radius * math.cos(math.radians(angle))
            y = root.y * self.scale + radius * math.sin(math.radians(angle))
            positions.append((x, y))
        return positions
    
    def draw_arrow(self, x1, y1, x2, y2, thickness, color):
        self.canvas.create_line(x1, y1, x2, y2, width=thickness, arrow=tk.LAST, fill=color)

    def get_color_based_on_depth(self, depth):
        colors = ["red", "orange", "blue", "green", "yellow", "grey"]
        index = min(depth, len(colors) - 1)
        return colors[index]

    def calculate_depth(self, node_id):
        # Calculate the depth of a node's relationship
        node = self.nodes[node_id]
        if not node.parents:
            return 0
        else:
            parent_depths = [self.calculate_depth(parent_id) for parent_id in node.parents]
            return max(parent_depths) + 1


    def load_data(self):
        try:               
            data = json.load( open( fileName, encoding="utf-8" ))
            tempParent = []
            tempChild = []
            if "nodes" in data:                
                for node_data in data["nodes"]:
                    if(node_data["id"] and node_data["id"] not in tempParent):
                        tempParent.append(node_data["id"])
                        
                for node_data in data["nodes"]:
                    for parent in node_data["parents"]:
                        if(parent not in tempParent):
                            node_data["parents"].remove(parent)
                            #print("P:", (parent))         

                for node_data in data["nodes"]:
                    if(node_data["id"] and node_data["id"] not in tempChild):
                        tempChild.append(node_data["id"])
                
                for node_data in data["nodes"]:
                    for child in node_data["children"]:
                        if(child not in tempChild):
                            node_data["children"].remove(child)
                            #print("C:", (child))

                for node_data in data["nodes"]:
                    #print("P:", (node_data["parents"]))  
                    node = Node(node_data["id"], node_data["x"], node_data["y"])                    
                    # Filter existing parents before assigning                       
                    node.parents = set(node_data["parents"])
                    node.children = set(node_data["children"])
                    node._idName = node_data["_idName"]
                    if(node_data["values"]["sinonimi"]):
                        node_data["values"]["sinonimi"] = list(set([x.strip().lower() for x in node_data["values"]["sinonimi"]]))
                    if(node_data["values"]["signal"]):
                        node_data["values"]["signal"] = node_data["values"]["signal"].upper()
                    node.values = node_data["values"]
                    self.nodes[node.id] = node
                
        except FileNotFoundError:
            pass

    def save_data(self):
        data = {"nodes": []}
        for node in self.nodes.values():
            node_data = {
                "id": node.id,
                "x": node.x,
                "y": node.y,
                "parents": list(node.parents),
                "children": list(node.children),
                "_idName": node._idName,
                "values": node.values
            }
            data["nodes"].append(node_data)
        # Sort the nodes list by the "id" key
        data["nodes"] = sorted(data["nodes"], key=lambda x: x["id"])
        json.dump( data, open( fileName, 'w', encoding="utf-8" ), ensure_ascii = False, sort_keys = True )


if __name__ == "__main__":
    root = tk.Tk()
    current_width = root.winfo_width() / 2            
    current_height = root.winfo_height() / 2 
    app = ForestManagerApp(root)
    root.mainloop()
            