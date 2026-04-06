import json
import os
import random
import time
from urllib.parse import urljoin, urlparse
from zipfile import ZipFile

import requests
from bs4 import BeautifulSoup

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def get_image_page_links(gallery_url, session, verbose=True):
    """Return a list of image viewer page URLs for a gallery."""
    if verbose:
        print(f"🔍 Fetching gallery page: {gallery_url}")

    parsed = urlparse(gallery_url)
    if parsed.path.startswith('/i/'):
        if verbose:
            print('ℹ️ Detected IMX single-viewer URL; treating as one image page.')
        return [gallery_url]

    res = session.get(gallery_url)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, 'html.parser')

    links = set()
    for tag in soup.select('a[href]'):
        href = tag['href'].strip()
        if href.startswith('/i/') or href.startswith('https://imx.to/i/') or href.startswith('http://imx.to/i/'):
            links.add(urljoin(gallery_url, href))

    if not links:
        for tag in soup.select('.tooltip a[href]'):
            href = tag['href'].strip()
            if href:
                links.add(urljoin(gallery_url, href))

    viewer_links = sorted(links)
    if verbose:
        print(f"✅ Found {len(viewer_links)} image viewer pages.")
    return viewer_links


def get_direct_image_url(viewer_url, session, verbose=True):
    """Extract the direct image URL from a viewer page."""
    if verbose:
        print(f"➡️  Opening viewer page: {viewer_url}")

    res = session.get(viewer_url)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, 'html.parser')

    form = soup.find('form', method=lambda value: value and value.lower() == 'post')
    if form:
        if verbose:
            print('📝 Found a form to submit...')
        post_url = urljoin(viewer_url, form.get('action', ''))
        form_data = {
            inp.get('name'): inp.get('value', '')
            for inp in form.find_all('input')
            if inp.get('name')
        }
        res = session.post(post_url, data=form_data)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')

    img_tag = soup.find('img', {'id': 'image'}) or soup.find('img', {'class': 'centred'})
    if not img_tag:
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if src and ('/i/' in src or 'image' in src.lower()):
                img_tag = img
                break

    if not img_tag:
        og_image = soup.find('meta', {'property': 'og:image'})
        if og_image and og_image.get('content'):
            return og_image['content']

    if img_tag and img_tag.get('src'):
        img_url = img_tag['src']
        if not img_url.startswith(('http:', 'https:')):
            img_url = urljoin(viewer_url, img_url)
        if verbose:
            print(f"✅ Found image URL: {img_url}")
        return img_url

    if verbose:
        print('⚠️ Could not find image URL')
    return None


def download_image(image_url, save_dir, index, total, session, verbose=True):
    basename = os.path.basename(urlparse(image_url).path) or f'image_{index}.jpg'
    if not os.path.splitext(basename)[1]:
        basename += '.jpg'

    filepath = os.path.join(save_dir, basename)
    if os.path.exists(filepath):
        if verbose:
            print(f"⏭️  [{index}/{total}] File already exists: {basename}")
        return filepath

    if verbose:
        print(f"📥 [{index}/{total}] Downloading: {basename}")
    res = session.get(image_url, stream=True)
    res.raise_for_status()
    os.makedirs(save_dir, exist_ok=True)

    with open(filepath, 'wb') as f:
        for chunk in res.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    if verbose:
        print(f"✔️  Saved to {filepath}")
    return filepath


def load_progress(save_dir):
    progress_file = os.path.join(save_dir, 'download_progress.json')
    if os.path.exists(progress_file):
        with open(progress_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def save_progress(save_dir, completed, viewer_links):
    progress_file = os.path.join(save_dir, 'download_progress.json')
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump({
            'completed': completed,
            'viewer_links': viewer_links,
            'timestamp': time.time(),
        }, f, indent=2)


def create_zip(save_dir, verbose=True):
    zip_path = f"{save_dir}.zip"
    if verbose:
        print(f"📦 Creating zip file at {zip_path}...")
    with ZipFile(zip_path, 'w') as zf:
        for root, _, files in os.walk(save_dir):
            for file in files:
                if file == 'download_progress.json':
                    continue
                full_path = os.path.join(root, file)
                arcname = os.path.relpath(full_path, save_dir)
                zf.write(full_path, arcname)
    if verbose:
        print(f"✅ Zip file created: {zip_path}")
    return zip_path


def determine_output_dir(gallery_url, output_dir=None):
    if output_dir:
        return output_dir
    parsed = urlparse(gallery_url)
    name = parsed.path.strip('/').replace('/', '_') or 'imx_gallery'
    return f"downloaded_images_{name}"


def download_gallery(gallery_url, output_dir=None, delay=1.0, resume=False, create_zip_file=True, verbose=True):
    save_dir = determine_output_dir(gallery_url, output_dir)
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    os.makedirs(save_dir, exist_ok=True)

    completed = []
    viewer_links = []
    if resume:
        progress = load_progress(save_dir)
        if progress:
            completed = progress.get('completed', [])
            viewer_links = progress.get('viewer_links', [])
            if verbose:
                print(f"📋 Resuming download: {len(completed)}/{len(viewer_links)} already completed")

    if not viewer_links:
        viewer_links = get_image_page_links(gallery_url, session, verbose=verbose)
        if not viewer_links:
            if verbose:
                print('❌ No image viewer pages found.')
            return save_dir

    total = len(viewer_links)
    start_time = time.time()
    if verbose:
        print(f"🚀 Starting download of {total} images to {save_dir}")

    for idx, viewer_url in enumerate(viewer_links, start=1):
        if viewer_url in completed:
            continue

        try:
            time.sleep(delay * (0.5 + random.random()))
            direct_url = get_direct_image_url(viewer_url, session, verbose=verbose)
            if direct_url:
                if download_image(direct_url, save_dir, idx, total, session, verbose=verbose):
                    completed.append(viewer_url)
                    if idx % 5 == 0:
                        save_progress(save_dir, completed, viewer_links)
        except Exception as exc:
            if verbose:
                print(f"❌ Error processing {viewer_url}: {exc}")

        if verbose:
            elapsed = time.time() - start_time
            remaining = (elapsed / idx) * (total - idx) if idx else 0
            print(f"⏱️  Progress: {idx}/{total} ({idx/total*100:.1f}%) | Elapsed: {elapsed/60:.1f}m | Remaining: {remaining/60:.1f}m")

    if create_zip_file:
        return create_zip(save_dir, verbose=verbose)
    return save_dir


def download_gallery_to_zip(gallery_url, output_dir=None, delay=1.0, resume=False, verbose=True):
    return download_gallery(
        gallery_url,
        output_dir=output_dir,
        delay=delay,
        resume=resume,
        create_zip_file=True,
        verbose=verbose,
    )
