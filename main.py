# Import libraries
import numpy as np
import matplotlib as plt
from skimage import color, exposure, io, viewer

# Open folder in this same direction
filepath = "images/i.jpg"

image = io.imread(filepath)