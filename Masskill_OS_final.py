import tkinter as tk
from tkinter import messagebox
from dataclasses import dataclass
from typing import List

DISK_SIZE = 50
GRID_COLS = 10

# Linked list node for free space extents
@dataclass
class FreeExtent:
    start: int
    size: int
    next: 'FreeExtent' = None

class HybridSpaceManager:
    def __init__(self, disk_size):
        self.disk_size = disk_size
        self.bitmap = [0] * disk_size  # 0 = free, 1 = allocated
        self.free_list = FreeExtent(0, disk_size)  # Head of linked list
        self.groups = []  # Groups of free spaces
        self.update_groups()
    
    def allocate(self, start, n):
        """Allocate n blocks at specific start position"""
        if start < 0 or start + n > self.disk_size:
            return False, -1
        
        # Check if all blocks are free
        for i in range(start, start + n):
            if self.bitmap[i] == 1:
                return False, -1
        
        # Allocate blocks
        for i in range(start, start + n):
            self.bitmap[i] = 1
        
        # Remove from linked list
        current = self.free_list
        prev = None
        
        while current:
            if current.start <= start and current.start + current.size >= start + n:
                # This extent covers the allocation
                if current.start == start and current.size == n:
                    # Remove entire extent
                    if prev:
                        prev.next = current.next
                    else:
                        self.free_list = current.next
                elif current.start == start:
                    # Trim from start
                    current.start += n
                    current.size -= n
                elif current.start + current.size == start + n:
                    # Trim from end
                    current.size -= n
                else:
                    # Split extent
                    new_extent = FreeExtent(start + n, current.start + current.size - start - n)
                    new_extent.next = current.next
                    current.size = start - current.start
                    current.next = new_extent
                break
            
            prev = current
            current = current.next
        
        self.update_groups()
        return True, start
    
    def deallocate(self, start, n):
        """Deallocate n blocks and merge with adjacent extents"""
        if start + n > self.disk_size or start < 0:
            return False
        
        # Mark as free in bitmap
        for i in range(start, start + n):
            self.bitmap[i] = 0
        
        # Add to linked list and merge if adjacent
        new_extent = FreeExtent(start, n)
        
        if not self.free_list:
            self.free_list = new_extent
        else:
            # Insert in order and merge
            current = self.free_list
            prev = None
            
            while current and current.start < start:
                prev = current
                current = current.next
            
            # Merge with next if adjacent
            if current and current.start == start + n:
                new_extent.size += current.size
                new_extent.next = current.next
            else:
                new_extent.next = current
            
            # Merge with prev if adjacent
            if prev and prev.start + prev.size == start:
                prev.size += new_extent.size
                prev.next = new_extent.next
            else:
                if prev:
                    prev.next = new_extent
                else:
                    self.free_list = new_extent
        
        self.update_groups()
        return True
    
    def update_groups(self):
        """Group free spaces into contiguous regions"""
        self.groups = []
        in_group = False
        group_start = 0
        
        for i in range(self.disk_size):
            if self.bitmap[i] == 0:  # Free
                if not in_group:
                    group_start = i
                    in_group = True
            else:  # Allocated
                if in_group:
                    self.groups.append((group_start, i - group_start))
                    in_group = False
        
        if in_group:
            self.groups.append((group_start, self.disk_size - group_start))
    
    def get_free_list_info(self):
        """Return linked list as string"""
        extents = []
        current = self.free_list
        while current:
            extents.append(f"[{current.start}:{current.start+current.size}]")
            current = current.next
        return " -> ".join(extents) if extents else "Empty"

# GUI
root = tk.Tk()
root.title("Hybrid Free Space Manager")
root.geometry("900x700")

manager = HybridSpaceManager(DISK_SIZE)

# Canvas for visualization
canvas = tk.Canvas(root, width=550, height=300, bg="white", relief="sunken", bd=2)
canvas.pack(pady=10, padx=10)

rects = []

def draw_disk():
    canvas.delete("all")
    rects.clear()
    
    block_width = 50
    block_height = 50
    padding = 2
    
    # Draw blocks
    for i in range(DISK_SIZE):
        row = i // GRID_COLS
        col = i % GRID_COLS
        
        x1 = 10 + col * (block_width + padding)
        y1 = 10 + row * (block_height + padding)
        x2 = x1 + block_width
        y2 = y1 + block_height
        
        color = "lightgreen" if manager.bitmap[i] == 0 else "salmon"
        rect = canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="gray")
        canvas.create_text(x1 + block_width//2, y1 + block_height//2, 
                          text=str(i), font=("Arial", 7), fill="black")
        rects.append(rect)
    
    # Draw arrows between free extents in linked list
    current = manager.free_list
    prev_extent = None
    
    while current:
        if prev_extent:
            # Calculate center of last block of previous extent
            prev_last_block = prev_extent.start + prev_extent.size - 1
            prev_row = prev_last_block // GRID_COLS
            prev_col = prev_last_block % GRID_COLS
            prev_x = 10 + prev_col * (block_width + padding) + block_width
            prev_y = 10 + prev_row * (block_height + padding) + block_height // 2
            
            # Calculate center of first block of current extent
            curr_first_block = current.start
            curr_row = curr_first_block // GRID_COLS
            curr_col = curr_first_block % GRID_COLS
            curr_x = 10 + curr_col * (block_width + padding)
            curr_y = 10 + curr_row * (block_height + padding) + block_height // 2
            
            # Draw curved arrow
            if prev_row == curr_row:
                # Same row - straight arrow
                canvas.create_line(prev_x, prev_y, curr_x, curr_y, 
                                 arrow=tk.LAST, width=3, fill="blue", 
                                 smooth=True, arrowshape=(10, 12, 5))
            else:
                # Different rows - curved arrow
                mid_x = (prev_x + curr_x) / 2
                mid_y = min(prev_y, curr_y) - 20
                canvas.create_line(prev_x, prev_y, mid_x, mid_y, curr_x, curr_y,
                                 arrow=tk.LAST, width=3, fill="blue",
                                 smooth=True, arrowshape=(10, 12, 5))
        
        prev_extent = current
        current = current.next

draw_disk()

# Info frame
info_frame = tk.Frame(root, relief="sunken", bd=2)
info_frame.pack(fill="both", expand=True, padx=10, pady=10)

info_text = tk.Text(info_frame, height=12, width=100, wrap="word", font=("Courier", 9))
info_text.pack(fill="both", expand=True, padx=5, pady=5)

def update_info():
    info_text.config(state="normal")
    info_text.delete("1.0", "end")
    
    free_count = manager.bitmap.count(0)
    allocated_count = manager.bitmap.count(1)
    
    info_text.insert("end", "=== HYBRID FREE SPACE MANAGER INFO ===\n\n")
    info_text.insert("end", f"Total Disk Size: {DISK_SIZE} blocks\n")
    info_text.insert("end", f"Allocated: {allocated_count} blocks | Free: {free_count} blocks\n")
    info_text.insert("end", f"Fragmentation: {len(manager.groups)} free groups\n\n")
    
    info_text.insert("end", "📋 LINKED LIST (Free Extents):\n")
    info_text.insert("end", manager.get_free_list_info() + "\n\n")
    
    info_text.insert("end", "📊 FREE SPACE GROUPS:\n")
    if manager.groups:
        for idx, (start, size) in enumerate(manager.groups, 1):
            info_text.insert("end", f"  Group {idx}: Start={start}, Size={size} blocks\n")
    else:
        info_text.insert("end", "  No free space available\n")
    
    info_text.config(state="disabled")

# Control frame
control_frame = tk.Frame(root)
control_frame.pack(fill="x", padx=10, pady=10)

tk.Label(control_frame, text="Allocate (start, count):", font=("Arial", 10)).grid(row=0, column=0, sticky="w")
entry_alloc_start = tk.Entry(control_frame, width=8, font=("Arial", 10))
entry_alloc_start.grid(row=0, column=1, padx=5)
entry_alloc_count = tk.Entry(control_frame, width=8, font=("Arial", 10))
entry_alloc_count.grid(row=0, column=2, padx=5)

def on_allocate():
    try:
        start = int(entry_alloc_start.get())
        n = int(entry_alloc_count.get())
        success, result = manager.allocate(start, n)
        if success:
            draw_disk()
            update_info()
            messagebox.showinfo("Success", f"Allocated {n} blocks starting at {start}")
        else:
            messagebox.showerror("Error", f"Cannot allocate {n} blocks at position {start}")
    except ValueError:
        messagebox.showerror("Error", "Enter valid numbers")

tk.Button(control_frame, text="Allocate", command=on_allocate, bg="lightblue").grid(row=0, column=3, padx=5)

tk.Label(control_frame, text="Deallocate (start, count):", font=("Arial", 10)).grid(row=1, column=0, sticky="w", pady=5)
entry_dealloc_start = tk.Entry(control_frame, width=8, font=("Arial", 10))
entry_dealloc_start.grid(row=1, column=1, padx=5)
entry_dealloc_count = tk.Entry(control_frame, width=8, font=("Arial", 10))
entry_dealloc_count.grid(row=1, column=2, padx=5)

def on_deallocate():
    try:
        start = int(entry_dealloc_start.get())
        count = int(entry_dealloc_count.get())
        if manager.deallocate(start, count):
            draw_disk()
            update_info()
            messagebox.showinfo("Success", f"Deallocated {count} blocks from {start}")
        else:
            messagebox.showerror("Error", "Invalid deallocation parameters")
    except ValueError:
        messagebox.showerror("Error", "Enter valid numbers")

tk.Button(control_frame, text="Deallocate", command=on_deallocate, bg="lightcoral").grid(row=1, column=3, padx=5)

tk.Button(control_frame, text="Reset", command=lambda: [
    manager.__init__(DISK_SIZE),
    draw_disk(),
    update_info()
], bg="lightyellow").grid(row=1, column=4, padx=5)

update_info()
root.mainloop()
