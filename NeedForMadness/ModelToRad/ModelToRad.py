modPrecis = int(2)		# amount of decimals to keep
modScale = 0.4			# model scale

import bpy
from math import *

obj = bpy.context.active_object
mesh = obj.data
polys = mesh.polygons
verts = mesh.vertices

mats = mesh.materials
colors = [[m.name, [], 0, 0] for m in mats]
surfs = [i for i in range(len(mats))]

rad = bpy.data.texts.get(f'{obj.name}.rad')
if rad == None:
	rad = bpy.data.texts.new(f'{obj.name}.rad')
else:
	rad.clear()


def gen(_txt, _n=1):
	rad.write(_txt)
	for i in range(_n):
		rad.write('\n')


def sRGBToLinear(_l):
	if 0 <= _l and _l <= 0.0031308:
		return _l * 12.92
	elif 0.0031308 < _l and _l <= 1:
		return 1.055 * (_l ** (1 / 2.4)) - 0.055
	return _l


def colPicker(_col, _iMat):
	max = 255
	rgb = []
	
	for i in range(3):
		rgb.append(round(sRGBToLinear(_col[i]) * 255))
		if rgb[i] > max:
			max = rgb[i]
	
	if max > 255:
		colors[_iMat][2] = -10
	
	max = ceil(max / 255)
	
	for i in range(3):
		rgb[i] = int(rgb[i] / max)
	
	return rgb


def findMats():
	for i in range(len(mats)):
		rgb = colPicker(mats[i].diffuse_color, i)
		nm = mats[i].name.casefold()
		
		colors[i][0] = f'c({rgb[0]},{rgb[1]},{rgb[2]})'
		
		if nm.find('glass') != -1:
			surfs.pop(surfs.index(i))
			colors[i][0] = None
			colors[i][1].append('glass')
		
		if nm.find('light') != -1:
			if nm.find('b') != -1 or nm.find('rear') != -1: # find back/rear lights
				surfs.pop(surfs.index(i))
				colors[i][1].append('lightB')
			else: # find front lights
				surfs.pop(surfs.index(i))				
				colors[i][1].append('lightF')
		

def generatePoint(_point):
	p = 'p('
	p += f'{round(_point.co[0] * -10 ** modPrecis)},'
	p += f'{round(_point.co[2] * -10 ** modPrecis)},'
	p += f'{round(_point.co[1] * -10 ** modPrecis)})'
	gen(p)


def generatePoly(_poly):
	
	col = colors[_poly.material_index][0]
	efx = colors[_poly.material_index][1].copy()
	gr = colors[_poly.material_index][2]
	fs = colors[_poly.material_index][3]
	
	if _poly.use_smooth:
		efx.append('noOutline()') # remove face's outlines if marked smooth
	if _poly.use_freestyle_mark: # electrify face if marked freestyle
		gr = -18
	if _poly.hide: # hide face if hidden
		gr = -13
	
	rtrn = 2
	if col != None:
		rtrn -= 1
	rtrn -= len(efx)
	if gr != 0:
		rtrn -= 1
	if fs != 0:
		rtrn -= 1
	
	gen('<p>') # open the polygon
	
	if col != None: # generate c(r,g,b) line
		gen(col)
	
	if len(efx) > 0: # generate the first effect
		gen(str(efx[0]))
	
	gen('', rtrn) # generate the return lines
	del rtrn
	
	if len(efx) > 1: # generate the rest of the effects
		for i in range(1, len(efx)):
			gen(str(efx[i]))
	
	if gr != 0: # generate the gr() line
		gen(f'gr({gr})')
	
	if fs != 0: # generate the fs() line
		gen(f'fs({fs})')
	
	for iVtx in _poly.vertices: # generate all the p() lines
		vtx = verts[iVtx]
		generatePoint(vtx)

	gen('</p>',2) # close the polygon
	

def detectVertPair(_vertList):
	for i in range(len(_vertList)):
		for j in range(i + 1, len(_vertList)):
			if _vertList[i].co[1] == _vertList[j].co[1] and _vertList[i].co[2] == _vertList[j].co[2] and _vertList[i].co[0] == -_vertList[j].co[0]:
				vert1 = _vertList[i]
				vert2 = _vertList[j]
				
				_vertList.pop(_vertList.index(vert1))
				_vertList.pop(_vertList.index(vert2))
				return [[ch for ch in vert1.co], [ch for ch in vert2.co]]
	
	return [None, None]


def generateWheels():
	iMeshVerts = [e.vertices[0] for e in mesh.edges] + [e.vertices[1] for e in mesh.edges]
	loneVerts = [v for v in verts if v.index not in iMeshVerts]

	posPairs = [detectVertPair(loneVerts), detectVertPair(loneVerts)]
	
	for pair in posPairs:
		if pair == [None, None]: # as long as there are empty pairs, make a pair from the first lone vertex list (and remove it)
			lonePos = [ch for ch in loneVerts[0].co]
			pair[0] = lonePos
			pair[1] = [-lonePos[0], lonePos[1], lonePos[2]]
			
			loneVerts.pop(0)
	
	for i in range(2):
		gen('gwgr(0)')
		gen('rims(140,140,140,18,10)')
		for j in [1, 0]:
			pos = posPairs[i][1 - j]
			w = 'w('
			w += f'{round(pos[0] * -10 ** modPrecis)},'
			w += f'{round(pos[2] * -10 ** modPrecis)},'
			w += f'{round(pos[1] * -10 ** modPrecis)},'
			w += f'{(1-i)*11},{(j*2-1)*26},20)'
			gen(w, 2-j)
	


def generateCar():
	findMats()
	gen(f'// converted car: {obj.name}')
	gen('---------------------', 2)
	
	gen(f'1stColor{colors[surfs[0]][0].strip("c")}')
	gen(f'2ndColor{colors[surfs[1]][0].strip("c")}', 2)
	
	gen(f'ScaleZ({round(obj.scale[1] * modScale * 100)})')
	gen(f'ScaleY({round(obj.scale[2] * modScale * 100)})')
	gen(f'ScaleX({round(obj.scale[0] * modScale * 100)})', 2)
	
	for poly in polys:
		generatePoly(poly)
	
	generateWheels()
	
	gen('physics(50,50,50,50,50,50,50,50,50,50,50,100,50,50,0,21717)',2)
	
	gen('stat(104,104,104,104,104)',2)

	gen('handling(104)')
	

generateCar()
