"""
IRC color specifications
"""

import lib.contrast

COLOR_PATTERN = "([0-9]{1,2})(,[0-9]{1,2}){0,1}.*"
COLOR_TABLE =  {
			 0: lib.contrast.CONTRAST_COLOR_WHITE,
			 1: lib.contrast.CONTRAST_COLOR_BLACK,
			 2: lib.contrast.CONTRAST_COLOR_BLUE,
			 3: lib.contrast.CONTRAST_COLOR_DARK_GREEN,
			 4: lib.contrast.CONTRAST_COLOR_DARK_RED,
			 5: lib.contrast.CONTRAST_COLOR_LIGHT_BROWN,
			 6: lib.contrast.CONTRAST_COLOR_PURPLE,
			 7: lib.contrast.CONTRAST_COLOR_ORANGE,
			 8: lib.contrast.CONTRAST_COLOR_YELLOW,
			 9: lib.contrast.CONTRAST_COLOR_LIGHT_GREEN,
			10: lib.contrast.CONTRAST_COLOR_CYAN,
			11: lib.contrast.CONTRAST_COLOR_AQUA,
			12: lib.contrast.CONTRAST_COLOR_LIGHT_BLUE,
			13: lib.contrast.CONTRAST_COLOR_MAGENTA,
			14: lib.contrast.CONTRAST_COLOR_GREY,
			15: lib.contrast.CONTRAST_COLOR_LIGHT_GREY
		}


