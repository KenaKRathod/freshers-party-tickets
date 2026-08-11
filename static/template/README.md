# Pass Template

Place your pass template image here as `pass_template.png`.

The QR code will be pasted at the position defined in `generate.py`:
- **QR_POSITION** = (835, 165) — top-left corner of QR on the pass
- **QR_SIZE** = (180, 180) — width × height in pixels

## How to adjust

1. Run `python generate.py --preview` to generate one sample pass
2. Open `static/passes/pass_001.png` and check QR placement
3. Adjust `QR_POSITION` and `QR_SIZE` in `generate.py`
4. Re-run `--preview` until it looks right
5. Then run `python generate.py` for all 250 passes
