#!/usr/bin/env python3
"""
Freshers' ZENITH -- Pass Generator

Generates tokens, QR codes, pass images, and a printable PDF.

Usage:
    python generate.py                  # Full pipeline: tokens -> QR -> passes -> PDF
    python generate.py --preview        # Generate 1 sample pass to verify QR placement
    python generate.py --qr-only        # Only regenerate QR codes
    python generate.py --pdf-only       # Only rebuild PDF from existing pass images
    python generate.py --count 50       # Generate 50 tickets instead of 250
"""

import os
import sys
import argparse
import secrets
from glob import glob

import qrcode
from PIL import Image
import img2pdf

from config import Config
from database import init_db, get_db


# ============================================================================
#  QR PLACEMENT CONFIG -- adjust these to match your pass template
# ============================================================================
QR_SIZE = (160, 160)        # Width x height of the QR code on the pass (px)
QR_POSITION = (1320, 520)    # Top-left corner (x, y) where QR is pasted
# ============================================================================


def generate_tokens(count=None):
    """Generate unique URL-safe tokens and insert them into the database."""
    if count is None:
        count = Config.NUM_TICKETS

    init_db()
    conn = get_db()

    existing = conn.execute('SELECT COUNT(*) FROM tickets').fetchone()[0]
    if existing >= count:
        print(f"  [OK] Already have {existing} tokens in database -- skipping.")
        conn.close()
        return

    to_generate = count - existing
    print(f"  [TOKENS] Generating {to_generate} new tokens ...")

    generated = 0
    while generated < to_generate:
        token = secrets.token_urlsafe(16)           # 16 bytes -> 22-char string
        try:
            conn.execute('INSERT INTO tickets (token) VALUES (?)', (token,))
            generated += 1
        except Exception:
            continue                                 # duplicate -- retry

    conn.commit()
    conn.close()
    print(f"  [OK] {generated} tokens created  (total: {count})")


def generate_qr_codes():
    """Create a QR-code PNG for every token in the database."""
    os.makedirs('static/qr_codes', exist_ok=True)

    conn = get_db()
    tickets = conn.execute('SELECT token FROM tickets ORDER BY id').fetchall()
    conn.close()

    total = len(tickets)
    print(f"  [QR] Generating {total} QR codes ...")
    created = 0

    for i, row in enumerate(tickets, 1):
        token = row['token']
        filepath = f'static/qr_codes/{token}.png'

        if os.path.exists(filepath):
            continue

        url = f"{Config.BASE_URL}/t/{token}"

        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_H,   # 30 % recovery
            box_size=10,
            border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)

        img = qr.make_image(fill_color='black', back_color='white')
        img.save(filepath)
        created += 1

        if i % 50 == 0 or i == total:
            print(f"      ... {i}/{total}")

    print(f"  [OK] {created} new QR codes saved to static/qr_codes/")


def build_passes(preview=False):
    """Paste each QR code onto the pass template and save individual PNGs."""
    template_path = os.path.join('static', 'template', 'pass_template.png')

    if not os.path.exists(template_path):
        print(f"\n  [ERROR] Template not found: {template_path}")
        print(f"         Place your pass image there and re-run.\n")
        sys.exit(1)

    os.makedirs('static/passes', exist_ok=True)

    template = Image.open(template_path).convert('RGBA')
    tw, th = template.size
    print(f"  [TEMPLATE] Size: {tw} x {th} px")

    conn = get_db()
    tickets = conn.execute('SELECT id, token FROM tickets ORDER BY id').fetchall()
    conn.close()

    if preview:
        tickets = tickets[:1]
        print("  [PREVIEW] Building 1 sample pass ...")
    else:
        print(f"  [PASSES] Building {len(tickets)} passes ...")

    for i, row in enumerate(tickets, 1):
        token = row['token']
        ticket_id = row['id']

        qr_path = f'static/qr_codes/{token}.png'
        if not os.path.exists(qr_path):
            print(f"      [WARN] QR missing for ticket #{ticket_id} -- skipping")
            continue

        # Resize QR and paste onto a copy of the template
        qr_img = Image.open(qr_path).convert('RGBA')
        qr_img = qr_img.resize(QR_SIZE, Image.LANCZOS)

        pass_img = template.copy()
        pass_img.paste(qr_img, QR_POSITION, mask=qr_img)

        # Save as RGB (needed for img2pdf later)
        pass_rgb = pass_img.convert('RGB')
        output_path = f'static/passes/pass_{ticket_id:03d}.png'
        pass_rgb.save(output_path, quality=95)

        if preview:
            print(f"\n  [OK] Preview saved -> {output_path}")
            print(f"       QR position : {QR_POSITION}")
            print(f"       QR size     : {QR_SIZE}")
            print(f"       Open the file and verify placement.")
            print(f"       Adjust QR_POSITION / QR_SIZE in generate.py if needed.\n")
            return

        if i % 50 == 0 or i == len(tickets):
            print(f"      ... {i}/{len(tickets)}")

    print(f"  [OK] All passes saved to static/passes/")


def build_pdf():
    """Combine all individual pass PNGs into one printable PDF."""
    os.makedirs('output', exist_ok=True)

    image_files = sorted(glob('static/passes/pass_*.png'))

    if not image_files:
        print("\n  [ERROR] No pass images found in static/passes/")
        sys.exit(1)

    print(f"  [PDF] Combining {len(image_files)} passes into PDF ...")

    pdf_path = os.path.join('output', 'all_passes.pdf')
    with open(pdf_path, 'wb') as f:
        f.write(img2pdf.convert(image_files))

    size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
    print(f"  [OK] PDF created -> {pdf_path}  ({size_mb:.1f} MB)")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Freshers' ZENITH -- Pass Generator"
    )
    parser.add_argument(
        '--preview', action='store_true',
        help='Generate 1 sample pass to verify QR placement'
    )
    parser.add_argument(
        '--qr-only', action='store_true',
        help='Only regenerate QR codes (skip passes & PDF)'
    )
    parser.add_argument(
        '--pdf-only', action='store_true',
        help='Only rebuild the PDF from existing pass images'
    )
    parser.add_argument(
        '--count', type=int, default=None,
        help=f'Number of tickets (default: {Config.NUM_TICKETS})'
    )

    args = parser.parse_args()

    print()
    print("  +==========================================+")
    print("  |   Freshers' ZENITH -- Pass Generator     |")
    print("  +==========================================+")
    print()

    if args.pdf_only:
        build_pdf()
        return

    if args.qr_only:
        generate_qr_codes()
        return

    # Full pipeline
    generate_tokens(args.count)
    generate_qr_codes()
    build_passes(preview=args.preview)

    if not args.preview:
        build_pdf()
        print()
        print("  Done! Your passes are ready.")
        print(f"      PDF            -> output/all_passes.pdf")
        print(f"      Individual     -> static/passes/")
        print(f"      QR codes       -> static/qr_codes/")
        print()


if __name__ == '__main__':
    main()
