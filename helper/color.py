"""
Copyright (c) 2009 Marian Tietz
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:

1. Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE AUTHORS AND CONTRIBUTORS ``AS IS'' AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHORS OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
SUCH DAMAGE.
"""

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


