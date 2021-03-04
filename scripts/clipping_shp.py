import fiona
import numpy as np
import shapely
from fiona.crs import from_string
from pyproj import CRS, Transformer
from shapely.geometry import asMultiPoint, mapping

# grover  40.868393, -104.226126
# Wellington  40.702324, -105.005497
#
# buffer  64373.76
#
# +proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs
#
# +proj=aea +lat_0=23 +lon_0=-96 +lat_1=29.5 +lat_2=45.5 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs

original = CRS.from_proj4("+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs")
destination = CRS.from_proj4(
    "+proj=aea +lat_0=23 +lon_0=-96 +lat_1=29.5 +lat_2=45.5 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs"
)
transprojr = Transformer.from_proj(original, destination)
ma = asMultiPoint(np.array([[40.868393, -104.226126], [40.702324, -105.005497]]))

out = []
for pt in transprojr.itransform(
    np.array([[-104.226126, 40.868393], [-105.005497, 40.702324]])
):
    print(pt)
    out.append(pt)
print(out)
ma = asMultiPoint(out)
print(ma)
# small_rect = ma.buffer(80467.2).minimum_rotated_rectangle
(minx, miny, maxx, maxy) = ma.buffer(80467.2).bounds
small_rect = shapely.geometry.box(minx, miny, maxx, maxy)
# big_rect = ma.buffer(100000).minimum_rotated_rectangle
(minx, miny, maxx, maxy) = ma.buffer(160000).bounds
big_rect = shapely.geometry.box(minx, miny, maxx, maxy)
print(small_rect)
print(big_rect)

schema = {
    "geometry": "Polygon",
    "properties": {"id": "int"},
}

# Write a small retangle Shapefile
with fiona.open(
    "small_rect.shp",
    "w",
    "ESRI Shapefile",
    schema,
    crs=from_string(
        "+proj=aea +lat_0=23 +lon_0=-96 +lat_1=29.5 +lat_2=45.5 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs"
    ),
) as c:
    c.write(
        {
            "geometry": mapping(small_rect),
            "properties": {"id": 1},
        }
    )

# Write a big retangle Shapefile
with fiona.open(
    "big_rect.shp",
    "w",
    "ESRI Shapefile",
    schema,
    crs=from_string(
        "+proj=aea +lat_0=23 +lon_0=-96 +lat_1=29.5 +lat_2=45.5 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs"
    ),
) as c:
    c.write(
        {
            "geometry": mapping(big_rect),
            "properties": {"id": 1},
        }
    )
