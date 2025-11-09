# Hybrid Free Space Manager

An educational operating system project demonstrating efficient disk space allocation using a hybrid approach.

## Overview

This project combines three techniques for optimal disk management:
- **Bitmap**: Fast O(1) block status lookup
- **Linked List**: Efficient extent tracking and automatic merging
- **Grouping**: Real-time fragmentation analysis

## Features

- Interactive GUI with color-coded blocks (green=free, red=allocated)
- Visual arrows showing linked list connections
- Automatic merging of adjacent free blocks
- Real-time statistics and fragmentation metrics
- Allocate/deallocate blocks at any position

Requires Python 3.6+ with Tkinter.

## Author

Hemanth M.P
