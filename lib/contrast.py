"""
Copyright (c) 2009 Marian Tietz
Copyright (c) 2006-2007  David Trowbridge

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""


import gtk
from math import sqrt, fabs

# actually, this should be an enum but
# there is no need for an enum, i think...
(
	CONTRAST_COLOR_AQUA,
	CONTRAST_COLOR_BLACK,
	CONTRAST_COLOR_BLUE,
	CONTRAST_COLOR_BROWN,
	CONTRAST_COLOR_CYAN,
	CONTRAST_COLOR_DARK_BLUE,
	CONTRAST_COLOR_DARK_GREEN,
	CONTRAST_COLOR_DARK_GREY,
	CONTRAST_COLOR_DARK_RED,
	CONTRAST_COLOR_GREEN,
	CONTRAST_COLOR_GREY,
	CONTRAST_COLOR_LIGHT_BLUE,
	CONTRAST_COLOR_LIGHT_BROWN,
	CONTRAST_COLOR_LIGHT_GREEN,
	CONTRAST_COLOR_LIGHT_GREY,
	CONTRAST_COLOR_LIGHT_RED,
	CONTRAST_COLOR_MAGENTA,
	CONTRAST_COLOR_ORANGE,
	CONTRAST_COLOR_PURPLE,
	CONTRAST_COLOR_RED,
	CONTRAST_COLOR_VIOLET,
	CONTRAST_COLOR_WHITE,
	CONTRAST_COLOR_YELLOW,
	CONTRAST_COLOR_LAST,
) = range(24)

color_regions = [
	[40.0,  60.0, -100.0, -80.0,  -10.0,  20.0], # CONTRAST_COLOR_AQUA
	[ 0.0,  30.0,    0.0,   0.0,    0.0,   0.0], # CONTRAST_COLOR_BLACK
	[25.0,  35.0, -100.0,   0.0, -100.0, -50.0], # CONTRAST_COLOR_BLUE
	[30.0,  60.0,   30.0,  50.0,   70.0, 100.0], # CONTRAST_COLOR_BROWN
	[50.0,  65.0, -100.0, -30.0, -100.0, -50.0], # CONTRAST_COLOR_CYAN
	[ 0.0,  20.0,  -40.0,  50.0, -100.0, -60.0], # CONTRAST_COLOR_DARK_BLUE
	[20.0,  35.0, -100.0, -70.0,   60.0, 100.0], # CONTRAST_COLOR_DARK_GREEN
	[20.0,  40.0,    0.0,   0.0,    0.0,   0.0], # CONTRAST_COLOR_DARK_GREY
	[10.0,  40.0,   90.0, 100.0,   70.0, 100.0], # CONTRAST_COLOR_DARK_RED
	[15.0,  40.0, -100.0, -80.0,   80.0, 100.0], # CONTRAST_COLOR_GREEN
	[35.0,  60.0,    0.0,   0.0,    0.0,   0.0], # CONTRAST_COLOR_GREY
	[40.0,  50.0, -100.0,   0.0, -100.0, -60.0], # CONTRAST_COLOR_LIGHT_BLUE
	[60.0,  75.0,   30.0,  50.0,   80.0, 100.0], # CONTRAST_COLOR_LIGHT_BROWN
	[80.0,  90.0, -100.0, -70.0,   70.0, 100.0], # CONTRAST_COLOR_LIGHT_GREEN
	[50.0,  80.0,    0.0,   0.0,    0.0,   0.0], # CONTRAST_COLOR_LIGHT_GREY
	[55.0,  65.0,   80.0,  90.0,   75.0, 100.0], # CONTRAST_COLOR_LIGHT_RED
	[40.0,  55.0,   90.0, 100.0,  -50.0,   0.0], # CONTRAST_COLOR_MAGENTA
	[65.0,  80.0,   20.0,  65.0,   90.0, 100.0], # CONTRAST_COLOR_ORANGE
	[35.0,  45.0,   85.0, 100.0,  -90.0, -80.0], # CONTRAST_COLOR_PURPLE
	[40.0,  50.0,   80.0, 100.0,   75.0, 100.0], # CONTRAST_COLOR_RED
	[70.0,  95.0,   90.0, 100.0, -100.0,   0.0], # CONTRAST_COLOR_VIOLET
	[75.0, 100.0,    0.0,   0.0,    0.0,   0.0], # CONTRAST_COLOR_WHITE
	[90.0, 100.0,    5.0,  15.0,   92.5, 105.0], # CONTRAST_COLOR_YELLOW
]

def srgb_to_xyz_g (K):
	a = 0.055
	gamma = 2.4
	if K > 0.04045:
		return ((K+a)/(1+a))**gamma
	else:
		return K / 12.92

def xyz_to_lab_f (t):
	if (t > 0.008856):
		return t ** (1/3.0)
	else:
		return 7.787*t + 16/116.0

def rgb_to_lab (R, G, B):
	""" returns (L,a,b) """
	Xn = 0.93819
	Yn = 0.98705
	Zn = 1.07475

	gr = srgb_to_xyz_g(R / 65535.0)
	gg = srgb_to_xyz_g(G / 65535.0)
	gb = srgb_to_xyz_g(B / 65535.0)

	x = 0.412424 * gr + 0.357579 * gg + 0.180464 * gb
	y = 0.212656 * gr + 0.715158 * gg + 0.072186 * gb
	z = 0.019332 * gr + 0.119193 * gg + 0.950444 * gb

	fy = xyz_to_lab_f(y / Yn)

	L = 116 * fy - 16
	a = 500 * (xyz_to_lab_f(x / Xn) - fy)
	b = 200 * (fy - xyz_to_lab_f(z / Zn))
	return (L,a,b)

def xyz_to_srgb_C (K):
	a = 0.055
	gamma = 2.4

	if (K > 0.00304):
		return (1 + a) * (K ** (1.0 / gamma)) - a
	else:
		return K * 12.92

def CLAMP(x, low, high):
	if x > high:
		return high
	elif x < low:
		return low
	else:
		return x

def lab_to_rgb (L, a, b):
	""" returns (R, G, B) """
	Xn = 0.93819
	Yn = 0.98705
	Zn = 1.07475

	fy = (L + 16) / 116
	fx = fy + a / 500
	fz = fy - b / 200
	delta = 6.0 / 29
	delta2 = delta ** 2

	if (fx > delta): x = Xn * fx ** 3
	else:            x = (fx - 16.0/116) * 3 * delta2 * Xn

	if (fy > delta): y = Yn * fy ** 3
	else:            y = (fy - 16.0/116) * 3 * delta2 * Yn

	if (fz > delta): z = Zn * fz ** 3
	else:            z = (fz - 16.0/116) * 3 * delta2 * Zn

	rs =  3.2410 * x - 1.5374 * y - 0.4986 * z
	gs = -0.9692 * x + 1.8760 * y + 0.0416 * z
	bs =  0.0556 * x - 0.2040 * y + 1.0570 * z

	R = CLAMP(int(round(xyz_to_srgb_C(rs) * 65535)), 0, 65535)
	G = CLAMP(int(round(xyz_to_srgb_C(gs) * 65535)), 0, 65535)
	B = CLAMP(int(round(xyz_to_srgb_C(bs) * 65535)), 0, 65535)

	return (R, G, B)

def lab_distance (La, aa, ba, Lb, ab, bb):
	dL = fabs(Lb - La)
	da = fabs(ab - aa)
	db = fabs(bb - ba)
	return sqrt(dL*dL + da*da + db*db)

def contrast_render_foreground_color (background, color):

	"""
	* contrast_render_foreground_color
	* @background: the background color (GdkColor)
	* @color: the desired foreground color (one of those constants on the top)
	*
	* Creates a specific color value for a foreground color, optimizing for
	* maximum readability against the background.
   	"""

	rcolor = gtk.gdk.Color()
	points = [[0 for n in range(3)] for n in range(8)]

	(L, a, b) = rgb_to_lab(background.red, background.green, background.blue)

	points[0][0] = color_regions[color][0]; points[0][1] = color_regions[color][2]; points[0][2] = color_regions[color][4];
	points[1][0] = color_regions[color][0]; points[1][1] = color_regions[color][2]; points[1][2] = color_regions[color][5];
	points[2][0] = color_regions[color][0]; points[2][1] = color_regions[color][3]; points[2][2] = color_regions[color][4];
	points[3][0] = color_regions[color][0]; points[3][1] = color_regions[color][3]; points[3][2] = color_regions[color][5];
	points[4][0] = color_regions[color][1]; points[4][1] = color_regions[color][2]; points[4][2] = color_regions[color][4];
	points[5][0] = color_regions[color][1]; points[5][1] = color_regions[color][2]; points[5][2] = color_regions[color][5];
	points[6][0] = color_regions[color][1]; points[6][1] = color_regions[color][3]; points[6][2] = color_regions[color][4];
	points[7][0] = color_regions[color][1]; points[7][1] = color_regions[color][3]; points[7][2] = color_regions[color][5];

	max_dist = 0
	max_color = 0
	float_dist = 0

	for i in range(8):
		dist = lab_distance(L, a, b, points[i][0], points[i][1], points[i][2])

		if dist > max_dist:
			max_dist = dist
			max_color = i

	"""
	If the luminosity distance is really short, extend the vector further
	out.  This may push it outside the bounds of the region that a color
	is specified in, but it keeps things readable when the background and
	foreground are really close.
	"""
	ld = fabs( L - points[max_color][0] )
	cd = sqrt( fabs(a - points[max_color][1]) ** 2 + fabs(b - points[max_color][2]) ** 2 )

	if (ld < 10.0) and (cd < 60.0):
		dL = points[max_color][0] - L
		da = points[max_color][1] - a
		db = points[max_color][2] - b
		points[max_color][0] = L + (dL * 4.0)
		points[max_color][1] = a + (da * 1.5)
		points[max_color][2] = b + (db * 1.5)

	rcolor.pixel = 0
	rcolor.red, rcolor.green, rcolor.blue = lab_to_rgb(
				points[max_color][0],
				points[max_color][1],
				points[max_color][2])

	return rcolor
