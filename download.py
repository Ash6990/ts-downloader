"""Download TS (Transport Stream) video file from a website.

To use it:

- find the url of one of the TS file (for example, using the developer tools
  from Firefox or Chromium/Chrome)
- identify the counter in the url, and replace it with `{counter}` (this can be
  formatted if the counter must have a specific format, for example:
  `{counter:05d}`
- run the script: `python3 ts_downloader.py -o FILE.mp4 "URL_WITH_COUNTER"`

Bruno Oberle - 2002
Updated with User-Agent spoofing and empty-file checks.
"""

import argparse
import os
import subprocess
import tempfile
from urllib.error import URLError
from urllib.request import Request, urlopen


def download(template_url):
    """Download the TS chunks and concatenate them in the returned string.

    `template_url` is a string containing the `{counter}` placeholder, which
    may contain formatting option (eg `{counter:05d}`).

    The urls are formed by incrementing the counter. When an error is
    encountered (eg a 404), the loop stops.

    The returned value is binary string.
    """
    binary_content = b""
    counter = 1
    
    # Masquerade as a normal web browser to avoid getting blocked by the CDN
    # Masquerade as a normal web browser and provide the Origin
    headers = {
        'User-Agent': 'type whatever agent you want to use',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Origin': 'link of the origin ',
        'Referer': 'link of the referer'
    }

    while True:
        url = template_url.format(counter=counter)
        print(f"Reading {url}")
        try:
            req = Request(url, headers=headers)
            u = urlopen(req)
        except URLError as e:
            # e.reason is sometimes absent, so we use getattr as a safe fallback
            reason = getattr(e, 'reason', e)
            print(f"Stop condition met (or error): {reason}. Quitting downloading.")
            break
        except Exception as e:
            print(f"Unexpected error: {e}. Quitting downloading.")
            break
        else:
            binary_content += u.read()
            counter += 1
            
    return binary_content


def convert_ts_to_mp4(ts_path, mp4_path):
    """Convert the TS chunks to mp4 using ffmpeg.

    `ts_path` is a file containing the concatenated TS chunks.

    `mp4_path` is the output path.
    """
    print(f"Converting to mp4 using ffmpeg, output is {mp4_path}")
    subprocess.check_call(['ffmpeg', '-i', ts_path, mp4_path])


def parse_args():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "url_template",
        help="url template, must include {counter}"
    )
    parser.add_argument(
        "-o", dest="outfpath", required=True,
        help="output file"
    )
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    template_url = args.url_template
    
    # Check if {counter} is actually in the URL
    if "{counter" not in template_url:
        print("\nERROR: Your URL must contain the '{counter}' placeholder.")
        return

    content = download(template_url)
    
    # Prevent ffmpeg from crashing on an empty file
    if not content:
        print("\nERROR: No data was downloaded. Check your URL or network connection.\n")
        return

    with tempfile.TemporaryDirectory() as tempdir:
        ts_path = os.path.join(tempdir, "concat.ts")
        with open(ts_path, 'wb') as fh:
            fh.write(content)
        convert_ts_to_mp4(ts_path, args.outfpath)


if __name__ == "__main__":
    main()
