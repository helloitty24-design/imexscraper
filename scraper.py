from imexscraper.cli import main


if __name__ == '__main__':
    raise SystemExit(main())


    save_progress(save_dir, completed, viewer_links)

    zip_path = None
    if create_zip_file and completed:
        zip_path = create_zip(save_dir)

    print(f"🎉 Finished downloading {len(completed)}/{total} images.")
    print(f"📁 Output directory: {os.path.abspath(save_dir)}")
    if zip_path:
        print(f"📦 Zip file available at: {os.path.abspath(zip_path)}")

    return save_dir


def parse_args():
    parser = argparse.ArgumentParser(description='Download images from an imx.to gallery')
    parser.add_argument('url', help='IMX gallery URL or single viewer URL')
    parser.add_argument('-o', '--output-dir', help='Directory to save downloaded images')
    parser.add_argument('-d', '--delay', type=float, default=1.0, help='Average delay between requests in seconds')
    parser.add_argument('-r', '--resume', action='store_true', help='Resume from an existing progress file')
    parser.add_argument('--no-zip', action='store_true', help='Do not create a zip archive after downloading')
    return parser.parse_args()


def main():
    args = parse_args()
    download_gallery(
        gallery_url=args.url,
        output_dir=args.output_dir,
        delay=args.delay,
        resume=args.resume,
        create_zip_file=not args.no_zip,
    )


if __name__ == '__main__':
    main()
