import argparse

from .scraper import download_gallery_to_zip


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Download images from an imx.to gallery and save them as a zip file.'
    )
    parser.add_argument('gallery_url', help='Gallery URL (e.g. https://imx.to/g/1ktrx)')
    parser.add_argument('-o', '--output', help='Output folder name or path')
    parser.add_argument('--delay', type=float, default=1.0, help='Average delay between downloads in seconds')
    parser.add_argument('--resume', action='store_true', help='Resume an interrupted download')
    args = parser.parse_args(argv)

    zip_path = download_gallery_to_zip(
        args.gallery_url,
        output_dir=args.output,
        delay=args.delay,
        resume=args.resume,
    )
    print(f'Zip archive saved to: {zip_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
