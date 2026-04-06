# imexscraper

A simple Python package for downloading images from `imx.to` galleries and packaging them into a ZIP file.

## Installation

```bash
pip install .
```

## Usage

```bash
imexscraper https://imx.to/g/1ktrx
```

or with Python module mode:

```bash
python -m imexscraper https://imx.to/g/1ktrx
```

To specify an output folder:

```bash
imexscraper https://imx.to/g/1ktrx -o my_gallery
```

## Python API

```python
from imexscraper import download_gallery_to_zip
zip_path = download_gallery_to_zip('https://imx.to/g/1ktrx')
```

The package will download images from the gallery and save them in a zip archive named after the output folder.
