# SegView

visualise the 3D segmentation result

## Install

- The most convenient way would be: `pip3 install segview`
- You can also Include the file `segview.py` in your project directory

(SegView only support Python 3.5+, because it requires `PyQt5`)

## Use SegView

```python
segview.render_label(label, metadata, alpha=1) # see the 3D model of labels

segview.annotate_label(image, label, axis=-1)  # see the 2D slice with labels along different axes

segview.render_image(image, metadata)  # see the 3D render of an image

segview.render_image(image, metadata, feature)  # see the 3D image with features

segview.annotate_feature(image, label)  # see 2D slice with features
```

- `label` is a 3D `numpy` array
    - Usually it is the result of image segmentation, having the same structure
    - Value `0` corresponds to the background
    - Its shape is `(x, y, z)`.
- `feature` is a 2D `numpy` array
    - Usually it is the result of intensity maxima locating
    - It is 3D positions, `[(x1, y1, z1), (x2, y2, z2), ...]`
    - Its shape is `(feature_number, 3)`
- `metadata` is a dictionary containing the voxel size
    - It is only used in 3D visualisation, as many z-stack images have lower resolutions along z-axis
    - `{'voxel_size_x': 1, 'voxel_size_y': 1, 'voxel_size_z': 1}`
- `alpha` adjusts the brightness of the result
