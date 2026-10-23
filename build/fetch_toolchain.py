"""Verify a supplied VC7.1/UO SDK installation. No automatic download is provided.

Microsoft binaries, headers and libraries must be supplied under their own
licences. This release requires the SDK mixture described in build/README.md.
"""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify-only', action='store_true')
    parser.add_argument('--dest', type=Path, default=HERE / 'toolchain')
    parser.add_argument('--vc7', type=Path)
    parser.add_argument('--sdk', type=Path)
    # Accepted for compatibility with the driver's optional fetch arguments.
    parser.add_argument('--7z')
    parser.add_argument('--keep', action='store_true')
    args = parser.parse_args(argv)
    if not args.verify_only:
        print('Automatic UO toolchain download is unavailable. Supply VC7.1 and the SDK files described in build/README.md.')
        print('Use --verify-only --vc7 <Vc7> --sdk <uo-sdk> to check the installation.')
        return 1
    vc7 = args.vc7 or args.dest / 'vc7'
    sdk = args.sdk or vc7 / 'PlatformSDK'
    manifest = json.loads((HERE / 'toolchain_manifest.json').read_text(encoding='utf-8'))
    bad = []
    for base, pins in ((vc7, manifest['tools']), (sdk, manifest['sdk'])):
        for name, expected in pins.items():
            path = base / name
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                bad.append(str(path))
    for name in bad:
        print('missing or differing: ' + name)
    print('%d required files checked; %d files missing or differing' %
          (len(manifest['tools']) + len(manifest['sdk']), len(bad)))
    return int(bool(bad))


if __name__ == '__main__':
    raise SystemExit(main())
