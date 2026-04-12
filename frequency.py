import pandas as pd
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "cell-count.db")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "outputs")
 
POPULATIONS = ["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]
 