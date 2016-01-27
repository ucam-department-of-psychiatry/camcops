#!/usr/bin/env python3

"""
=============================================================================
OLD METHOD: PNG export
=============================================================================
from Illustrator:
1. small logo layer:   Save for Web > Image Size > width 1200, height 1200
    > Apply > Save > appicon_source.png
2. splashscreen layer: Save for Web > Image Size > width 1200, height 1200
    > Apply > Save > splashscreen_source.png
(3. PDF icon layer: Save for Web > Image Size > width 1000, height auto >
    Apply > Save > logo_camcops.png ... thence to web site)
(4. PDF icon layer: Save for Web > Image Size > width 1000, height auto >
    Apply > Save > logo_local.png ... thence to web site)

=============================================================================
OLD: Illustrator slicing technique
=============================================================================

- Don't use Illustrator's slices; they're inaccurate once you convert
  rectangles to slices.
- Ensure the whole board is an x-by-y grid.
- Ensure there's actual, coloured content at the edges (or it'll auto-trim and
  we'll slice wrongly).
- HAVE A GAP BETWEEN EACH ICON (the same size as the icons) - otherwise,
  Illustrator bleeds.
- Ensure black background is not visible; we want a transparent background.
- Save for Web; resize to the appropriate size (give or take a few pixels...)
- CURRENTLY: see SLICE_CAMCOPS_ICONS script for pixel sizes
  (each element is 96x96).
- Then run the slice script.

FOR SPLASHSCREEN:
- save the logo layer as logo_camcops.png
  ... e.g. 1000 wide (x approx. 180 high -- leave it at whatever it chooses
      with autoscaling)
  ... goes on the web site
- save all layers as sliceme.png
  ... run the script

=============================================================================
NEW METHOD: slice up PDFs
=============================================================================

For 1024x1024 DefaultIcon.png, which is getting too big for Illustrator's
export when you have it as the centre ninth:
  - Make a 30x30mm new artboard
  - Paste the art in
  - Save it as camcops_appicon.pdf
  - Then run this script.

2015-01-21: If you make DefaultIcon.png, Titanium makes icons of the right
size, but fails to keep the background transparent. So we make them
manually.
"""

import argparse
import logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
import os
from os.path import join
import shutil
import subprocess
import sys
import tempfile


def mkdirp(path):
    os.makedirs(path, exist_ok=True)


def ios(filename):
    return join(IOS_DIR, filename)


def get_pdf_print_size_inches(filename, autocrop=False):
    if autocrop:
        # Create a temporary, trimmed, PDF, and measure that instead.
        fd, tmpfname = tempfile.mkstemp('.pdf')
        os.close(fd)
        try:
            logger.debug("Measuring autocropped PDF")
            args = [
                'convert',
                # '-verbose',
                '-trim',
                filename,
                '+repage',
                tmpfname
            ]
            # Note that the output PDF is rasterized, not vector
            logger.debug(args)
            subprocess.check_call(args)
            return get_pdf_print_size_inches(tmpfname, autocrop=False)
        except:
            raise
        finally:
            os.remove(tmpfname)
    p1 = subprocess.Popen(['identify', '-verbose', filename],
                          stdout=subprocess.PIPE)
    p2 = subprocess.Popen(['grep', 'Print size: '],
                          stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    output = p2.communicate()[0].decode("utf-8").strip()
    # ... looks like "Print size: 1.18056x1.18056"
    info = output.split()[2]
    width, height = info.split('x')
    return float(width), float(height)


class ProportionPair(object):
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def __repr__(self):
        return "<ProportionPair({a}, {b})>".format(a=self.a, b=self.b)

    def is_valid(self):
        return 0 <= self.a <= 1 and 0 <= self.b <= 1 and self.a < self.b

    def validate(self):
        if not self.is_valid():
            raise AssertionError(
                "ProportionPair failed validation: {}".format(self))

    @property
    def span(self):
        return self.b - self.a

    def __mul__(self, other):
        w = self.span
        return ProportionPair(self.a + other.a * w,
                              self.a + other.b * w)


def crop_pdf(src_filename, dest_filename,
             dest_width_px=None, dest_height_px=None, autocrop=False,
             active_lr=None, active_tb=None,
             img_lr=None, img_tb=None,
             density_dpi=None, density_default_multiplier=2,
             transparent=None):
    """
    Takes a chunk out of a PDF.
    Source:
        src_filename
    Image transformation:
        transparent: colour to change to transparent, as per
            http://www.imagemagick.org/script/command-line-options.php#fill
        img_lr } describe the image to be taken; e.g. (1/3, 2/3)
        img_tb }
    Destination:
        dest_filename
        dest_width_px
        dest_height_px
    """
    # Input validation as early as possible
    if dest_width_px is None and dest_height_px is None:
        raise AssertionError("Must specify width/height/both")

    # What chunk will we take?
    active_lr = active_lr or ProportionPair(0, 1)
    active_tb = active_tb or ProportionPair(0, 1)
    img_lr = img_lr or ProportionPair(0, 1)
    img_tb = img_tb or ProportionPair(0, 1)
    active_lr.validate()
    active_tb.validate()
    img_lr.validate()
    img_tb.validate()
    final_img_lr = active_lr * img_lr
    final_img_tb = active_tb * img_tb
    logger.debug("Starting point: left=0, right=1; top=0, bottom=1")
    logger.debug("After removing margins: left={l}, right={r}; top={t}, "
                 "bottom={b}".format(l=active_lr.a,
                                     r=active_lr.b,
                                     t=active_tb.a,
                                     b=active_tb.b))
    logger.debug(
        "With what's left, take image: left={l}, right={r}; top={t}, "
        "bottom={b}".format(l=img_lr.a,
                            r=img_lr.b,
                            t=img_tb.a,
                            b=img_tb.b))
    logger.debug("Final image to be taken: left={l}, right={r}; top={t}, "
                 "bottom={b}".format(l=final_img_lr.a,
                                     r=final_img_lr.b,
                                     t=final_img_tb.a,
                                     b=final_img_tb.b))

    # The PDF knows its physical size (and notional density, which we
    # don't care about). ImageMagick will convert it to a different
    # density for us, at which point we can refer to it in terms of pixels.
    # First, we get its size.
    (src_width_inches,
     src_height_inches) = get_pdf_print_size_inches(src_filename, autocrop)
    logger.debug("Source PDF size: {} inches W x {} inches H".format(
        src_width_inches, src_height_inches))

    img_aspect_ratio = (
        (final_img_lr.span * src_width_inches) /
        (final_img_tb.span * src_height_inches)
    )

    # Infer width or height from aspect ratio?
    if dest_width_px is None:
        dest_width_px = round(img_aspect_ratio * dest_height_px)
        logger.debug(
            "Autocalculating: dest_width_px = img_aspect_ratio * "
            "dest_height_px = {} * {} = {}".format(
                img_aspect_ratio, dest_height_px, dest_width_px))
    elif dest_height_px is None:
        dest_height_px = round(dest_width_px / img_aspect_ratio)
        logger.debug(
            "Autocalculating: dest_height_px = dest_width_px / "
            "img_aspect_ratio = {} / {} = {}".format(
                dest_width_px, img_aspect_ratio, dest_height_px))

    # Calculate working density, if not specified (in dpi)
    if density_dpi is None:
        # Same number of pixels as output, or a multiple
        # x direction:
        img_width_inches = final_img_lr.span * src_width_inches
        density_dpi_x = dest_width_px / img_width_inches
        # Now the y direction
        img_height_inches = final_img_tb.span * src_height_inches
        density_dpi_y = dest_height_px / img_height_inches
        # We want the maximum of these, and perhaps a multiple
        density_dpi = round(density_default_multiplier *
                            max(density_dpi_x, density_dpi_y))

    src_width_px = density_dpi * src_width_inches
    src_height_px = density_dpi * src_height_inches

    # 2. We're taking a chunk out of the middle of the PDF
    img_left_px = round(final_img_lr.a * src_width_px)
    img_right_px = round(final_img_lr.b * src_width_px)
    img_width_px = img_right_px - img_left_px
    img_top_px = round(final_img_tb.a * src_height_px)
    img_bottom_px = round(final_img_tb.b * src_height_px)
    img_height_px = img_bottom_px - img_top_px

    logger.info("Making {f} at {w}x{h}".format(
        f=dest_filename, w=dest_width_px, h=dest_height_px))
    directory = os.path.dirname(dest_filename)
    if directory:
        mkdirp(directory)
    args = [
        'convert',
        # '-verbose',
    ]
    if autocrop:
        args.append('-trim')
    args.extend([
        '-density', str(density_dpi),
        src_filename,
    ])
    if autocrop:
        args.append('+repage')
    if transparent:
        args.extend(['-transparent', transparent])
    args.extend([
        '-crop', '{w}x{h}+{l}+{t}'.format(w=img_width_px,
                                          h=img_height_px,
                                          l=img_left_px,
                                          t=img_top_px),
        '+repage',
        '-resize', '{w}x{h}'.format(w=dest_width_px, h=dest_height_px),
        dest_filename
    ])
    logger.debug(args)
    subprocess.check_call(args)


def tile_pdf(src_filename, dest_filename_format, n_wide, n_high,
             tile_width_px=None, tile_height_px=None, autocrop=True,
             density_multiplier=4, transparent=None):
    logger.debug("Tiling {} -> {}".format(src_filename, dest_filename_format))
    if tile_width_px is None and tile_height_px is None:
        raise AssertionError("Must specify width/height/both")

    # Get source size
    (src_width_inches,
     src_height_inches) = get_pdf_print_size_inches(src_filename, autocrop)
    logger.debug("Source PDF size: {} inches W x {} inches H".format(
        src_width_inches, src_height_inches))

    src_tile_width_inches = src_width_inches / n_wide
    src_tile_height_inches = src_height_inches / n_high
    src_tile_aspect_ratio = src_tile_width_inches / src_tile_height_inches
    logger.debug(
        "Source PDF tile size: {} inches W x {} inches H "
        "(aspect ratio {})".format(
            src_tile_width_inches, src_tile_height_inches,
            src_tile_aspect_ratio))

    if tile_width_px is None:
        tile_width_px = round(src_tile_aspect_ratio * tile_height_px)
        logger.debug(
            "Autocalculating: tile_width_px = src_tile_aspect_ratio * "
            "tile_height_px = {} * {} = {}".format(
                src_tile_aspect_ratio, tile_height_px, tile_width_px))
    elif tile_height_px is None:
        tile_height_px = round(tile_width_px / src_tile_aspect_ratio)
        logger.debug(
            "Autocalculating: tile_height_px = tile_width_px / "
            "src_tile_aspect_ratio = {} / {} = {}".format(
                tile_width_px, src_tile_aspect_ratio, tile_height_px))

    intermediate_tile_width_px = density_multiplier * tile_width_px
    intermediate_tile_height_px = density_multiplier * tile_height_px

    # Calculate density. No distortion is possible, so this is simple.
    src_width_px = intermediate_tile_width_px * n_wide
    density_dpi = round(src_width_px / src_width_inches)

    # Off we go
    args = [
        'convert',
        # '-verbose',
    ]
    if autocrop:
        args.append('-trim')
    args.extend([
        '-density', str(density_dpi),
        src_filename,
    ])
    if autocrop:
        args.append('+repage')
    if transparent:
        args.extend(['-transparent', transparent])
    args.extend([
        '-crop', '{w}x{h}'.format(w=intermediate_tile_width_px,
                                  h=intermediate_tile_height_px),
        '+repage',
        '-resize', '{w}x{h}'.format(w=tile_width_px, h=tile_height_px),
        dest_filename_format
    ])
    logger.debug(args)
    subprocess.check_call(args)


def make_appicon(filename, side_px):
    # Imagine the source PDF as a 3x3 grid; we want the middle square.
    # Appicons are square.
    crop_pdf(
        src_filename=APPICON_PDF,
        img_lr=ProportionPair(1/3, 2/3),
        img_tb=ProportionPair(1/3, 2/3),
        dest_filename=filename,
        dest_width_px=side_px,
        dest_height_px=side_px
    )


def make_splashscreen(filename, width_px, height_px, trim_margin_frac=0.05):
    src_width_in, src_height_in = get_pdf_print_size_inches(SPLASHSCREEN_PDF)
    src_aspect_ratio = src_width_in / src_height_in
    dest_aspect_ratio = width_px / height_px
    logger.debug("source aspect ratio: {}".format(src_aspect_ratio))
    logger.debug("destination aspect ratio: {}".format(dest_aspect_ratio))
    if dest_aspect_ratio == src_aspect_ratio:
        img_lr = ProportionPair(0, 1)
        img_tb = ProportionPair(0, 1)
    elif dest_aspect_ratio > src_aspect_ratio:
        # wider than source, less tall
        img_lr = ProportionPair(0, 1)
        edge = (1 - src_aspect_ratio / dest_aspect_ratio) / 2
        img_tb = ProportionPair(edge, 1 - edge)
    else:
        # taller than source, less wide
        edge = (1 - dest_aspect_ratio / src_aspect_ratio) / 2
        img_lr = ProportionPair(edge, 1 - edge)
        img_tb = ProportionPair(0, 1)
    crop_pdf(
        src_filename=SPLASHSCREEN_PDF,
        active_lr=ProportionPair(trim_margin_frac, 1 - trim_margin_frac),
        active_tb=ProportionPair(trim_margin_frac, 1 - trim_margin_frac),
        img_lr=img_lr,
        img_tb=img_tb,
        dest_filename=filename,
        dest_width_px=width_px,
        dest_height_px=height_px
    )


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_BASE_DIR = os.path.abspath(join(
    THIS_DIR, os.pardir, os.pardir, os.pardir))

APPICON_PDF = join(THIS_DIR, "camcops_appicon.pdf")
SPLASHSCREEN_PDF = join(THIS_DIR, "camcops_splashscreens.pdf")
CAMCOPS_LOGO_PDF = join(THIS_DIR, "camcops_logo.pdf")
BLANK_LOGO_PDF = join(THIS_DIR, "blank_institution_logo.pdf")
TABLET_ICON_PDF = join(THIS_DIR, "camcops_icons.pdf")
SERVER_DIAGRAM_PDF = join(THIS_DIR, "camcops_server_diagram.pdf")
SCALING_LOGOS_PDF = join(THIS_DIR, "camcops_scaling_logos.pdf")

# http://docs.appcelerator.com/platform/latest/#!/guide/Icons_and_Splash_Screens

parser = argparse.ArgumentParser()
parser.add_argument("--base_dir", default=PROJECT_BASE_DIR,
                    help="Base directory (default: {})".format(
                        PROJECT_BASE_DIR))
parser.add_argument("--ios", action='store_true',
                    help="Process iOS icons/splashscreens")
parser.add_argument("--android", action='store_true',
                    help="Process Android icons/splashscreens")
parser.add_argument("--windows", action='store_true',
                    help="Process Windows icons/splashscreens")
parser.add_argument("--tablet", action='store_true',
                    help="Process tablet in-app icons")
parser.add_argument("--server", action='store_true',
                    help="Process server logos")
parser.add_argument("--all", action='store_true', help="Process everything")
parser.add_argument("-v", "--verbose", action='store_true', help="Verbose")
args = parser.parse_args()
logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
if args.all:
    args.android = True
    args.ios = True
    args.server = True
    args.tablet = True
    args.windows = True
logger.info("Using base directory: {}".format(args.base_dir))
if not any([args.ios, args.android, args.tablet, args.server]):
    logger.info("Nothing to do. Missing flags? Try --help for help.")
    sys.exit(0)

IOS_DIR = join(args.base_dir, "tablet", "Resources", "iphone")
ANDROID_PLT_RES = join(args.base_dir, "tablet", "platform", "android", "res")
ANDROID_RES_DIR = join(args.base_dir, "tablet", "Resources", "android")
SERVER_STATIC_DIR = join(args.base_dir, "server", "static")
TABLET_ICON_DIR = join(args.base_dir, "tablet", "Resources",
                       "images", "camcops")
WINDOWS_DIR = join(args.base_dir, "tablet", "Resources", "windows")
WEB_IMAGE_DIR = join(args.base_dir, "website", "images")

# =============================================================================
# iOS
# =============================================================================

if args.ios:
    logger.info("--- iOS")
    make_appicon(ios("appicon.png"), 57)
    make_appicon(ios("appicon@2x.png"), 114)
    make_appicon(ios("appicon-72.png"), 72)
    make_appicon(ios("appicon-72@2x.png"), 144)
    make_appicon(ios("appicon-Small-50.png"), 50)
    make_appicon(ios("appicon-Small-50@2x.png"), 100)
    make_appicon(ios("appicon-60@2x.png"), 120)
    make_appicon(ios("appicon-60@3x.png"), 180)
    make_appicon(ios("appicon-76.png"), 76)
    make_appicon(ios("appicon-76@2x.png"), 152)
    make_appicon(ios("appicon-Small-40.png"), 40)
    make_appicon(ios("appicon-Small-40@2x.png"), 80)
    make_appicon(ios("appicon-Small-40@3x.png"), 120)
    make_appicon(ios("appicon-Small.png"), 29)
    make_appicon(ios("appicon-Small@2x.png"), 58)
    make_appicon(ios("appicon-Small@3x.png"), 87)

    make_splashscreen(ios("Default.png"), 320, 480)
    make_splashscreen(ios("Default@2x.png"), 640, 690)
    make_splashscreen(ios("Default-568h@2x.png"), 640, 1136)
    make_splashscreen(ios("Default-667h@2x.png"), 750, 1334)
    make_splashscreen(ios("Default-Landscape-736h@3x.png"), 2208, 1242)
    make_splashscreen(ios("Default-Portrait-736h@3x.png"), 1242, 2208)
    make_splashscreen(ios("Default-Landscape.png"), 1024, 768)
    make_splashscreen(ios("Default-Portrait.png"), 768, 1024)
    make_splashscreen(ios("Default-Landscape@2x.png"), 2048, 1536)
    make_splashscreen(ios("Default-Portrait@2x.png"), 1536, 2048)

    # Artwork for app list in iTunes:
    # iTunesArtwork (no extension), 512 x 512
    # iTunesArtwork@2x (no extension), 1024 x 1024

# =============================================================================
# Android
# =============================================================================

if args.android:
    logger.info("--- Android")
    make_appicon(join(ANDROID_RES_DIR, "appicon.png"), 128)
    make_appicon(join(ANDROID_PLT_RES, "drawable-ldpi", "appicon.png"), 36)
    make_appicon(join(ANDROID_PLT_RES, "drawable-mdpi", "appicon.png"), 48)
    make_appicon(join(ANDROID_PLT_RES, "drawable-hdpi", "appicon.png"), 72)
    make_appicon(join(ANDROID_PLT_RES, "drawable-xhdpi", "appicon.png"), 96)
    make_appicon(join(ANDROID_PLT_RES, "drawable-xxhdpi", "appicon.png"), 144)

    # There might be better ways. But as a start:
    make_splashscreen(
        join(ANDROID_RES_DIR, "images", "res-land", "default.png"), 800, 480)
    make_splashscreen(
        join(ANDROID_RES_DIR, "images", "res-port", "default.png"), 480, 800)

# =============================================================================
# Windows
# =============================================================================

if args.windows:
    logger.info("--- Windows")
    make_appicon(join(WINDOWS_DIR, "Logo.png"), 150)
    make_appicon(join(WINDOWS_DIR, "SmallLogo.png"), 30)
    make_appicon(join(WINDOWS_DIR, "StoreLogo.png"), 50)
    make_appicon(join(WINDOWS_DIR, "Square150x150Logo.png"), 150)
    make_appicon(join(WINDOWS_DIR, "Square71x71Logo.png"), 71)
    make_appicon(join(WINDOWS_DIR, "Square44x44Logo.png"), 44)

    make_splashscreen(join(WINDOWS_DIR, "SplashScreen.png"), 620, 300)
    make_splashscreen(join(WINDOWS_DIR, "SplashScreen480x800.png"), 480, 800)
    make_splashscreen(join(WINDOWS_DIR, "SplashScreen480x800.scale-240.png"),
                      1152, 1920)

# =============================================================================
# Web site, CamCOPS server
# =============================================================================

if args.server:
    logger.info("--- Server")
    make_appicon(join(SERVER_STATIC_DIR, "favicon_camcops.png"), 32)
    make_appicon(join(WEB_IMAGE_DIR, "camcops.png"), 96)
    make_appicon(join(WEB_IMAGE_DIR, "favicon.png"), 32)
    crop_pdf(CAMCOPS_LOGO_PDF, join(SERVER_STATIC_DIR, "logo_camcops.png"),
             dest_width_px=1000, autocrop=True)
    crop_pdf(BLANK_LOGO_PDF, join(SERVER_STATIC_DIR, "logo_local.png"),
             dest_width_px=1000, autocrop=True)
    crop_pdf(BLANK_LOGO_PDF, join(SERVER_STATIC_DIR, "logo_local.png"),
             dest_width_px=1000, autocrop=True)
    crop_pdf(SERVER_DIAGRAM_PDF, join(WEB_IMAGE_DIR, "server_diagram.png"),
             dest_width_px=600, autocrop=True)
    crop_pdf(SCALING_LOGOS_PDF, join(WEB_IMAGE_DIR, "scaling_logos.png"),
             dest_width_px=600, autocrop=True)


# =============================================================================
# Tablet
# =============================================================================

"""
If transparency is not working, try:

    identify -verbose FILE.pdf
        # ... is there an alpha channel at all?
    convert FILE.pdf -alpha extract TEMP.png
        # ... does the alpha channel have something in it?

It proves hard to have my version of Illustrator export a bunch of images with
transparency in/between them. Not yet achieved. (The edges of the page, if any,
are transparent, but that's it.)

Therefore, simpler to get ImageMagick to replace a particular colour with
transparency. Add a background of an unused colour. Check with:

    convert FILE.pdf -transparent "rgb(240,240,200)" -alpha extract TEMP.png
"""


def row(a, b, c, d, e, f):
    temp = [None, None, a, None, b, None, c, None, d, None, e, None, f, None]
    return [x + '.png' if x is not None else None for x in temp]


NCOL = 14
NROW = 34
NONE_ROW = [None] * NCOL
ICONMAP = [
    NONE_ROW,
    NONE_ROW,
    row('finishflag', 'finishflag_T', 'camcops',
        'executive', 'locked', 'locked_T'),
    NONE_ROW,
    row('speaker', 'speaker_T', 'choose_patient',
        'research', 'unlocked', 'unlocked_T'),
    NONE_ROW,
    row('speaker_playing', 'speaker_playing_T', 'upload',
        'info', 'back', 'back_T'),
    NONE_ROW,
    row(None,  # OLD RELOAD
        None,  # OLD RELOAD_T
        'settings',
        None,  # OLD INFO
        'next', 'next_T'),
    NONE_ROW,
    row('camera', 'camera_T', 'global', 'patient_summary', 'add', 'add_T'),
    NONE_ROW,
    row('radio_selected', 'radio_selected_T', 'cognitive',
        'hasChild', 'cancel', 'cancel_T'),
    NONE_ROW,
    row('radio_unselected', 'radio_unselected_T', 'affective',
        'clinical', 'edit', 'edit_T'),
    NONE_ROW,
    row('check_true_red', 'check_true_red_T', 'addiction',
        'anonymous', 'delete', 'delete_T'),
    NONE_ROW,
    row('check_unselected', 'check_unselected_T', 'psychosis',
        'check_unselected_required', 'ok', 'ok_T'),
    NONE_ROW,
    row('check_true_black', 'check_true_black_T', 'catatonia',
        'radio_unselected_required', 'finish', 'finish_T'),
    NONE_ROW,
    row('check_false_black', 'check_false_black_T', 'personality',
        'stop', 'zoom', 'zoom_T'),
    NONE_ROW,
    row('check_false_red', 'check_false_red_T', 'field_incomplete_mandatory',
        'field_problem', 'privileged', 'privileged_T'),
    NONE_ROW,
    row('sets_research', 'sets_clinical', 'alltasks',
        'warning', 'time_now', 'time_now_T'),
    NONE_ROW,
    row('reload', 'reload_T',
        'rotate_clockwise', 'rotate_clockwise_T',
        'rotate_anticlockwise', 'rotate_anticlockwise_T'),
    NONE_ROW,
    row('choose_page', 'choose_page_T', 'read_only',
        'field_incomplete_optional', 'chain', 'whisker'),
    NONE_ROW,
    row('fast_forward', 'fast_forward_T', 'check_disabled',
        'radio_disabled', None, None),
    NONE_ROW,
]

if args.tablet:
    logger.info("--- Tablet")
    logger.info("Slicing icons...")
    mkdirp(TABLET_ICON_DIR)
    with tempfile.TemporaryDirectory() as tmpdir:
        tile_pdf(TABLET_ICON_PDF, join(tmpdir, "tile-%d.png"),
                 n_wide=NCOL, n_high=NROW, tile_width_px=96, tile_height_px=96,
                 autocrop=False, transparent="rgb(240,240,200)")
        tilenum = 0
        for r in range(NROW):
            for c in range(NCOL):
                tilename = join(tmpdir, "tile-{}.png".format(tilenum))
                propername = ICONMAP[r][c]
                if propername is not None:
                    fullpath = join(TABLET_ICON_DIR, propername)
                    logger.info("Creating {}".format(fullpath))
                    shutil.move(tilename, fullpath)
                tilenum += 1

    # Special: resize hasChild
    hasChild = join(TABLET_ICON_DIR, 'hasChild.png')
    logger.info("Resizing " + hasChild)
    args = ['convert', hasChild, '-resize', '24x24', hasChild]
    logger.debug(args)
    subprocess.check_call(args)

    # Special: make hasParent
    hasParent = join(TABLET_ICON_DIR, 'hasParent.png')
    logger.info("Making " + hasParent)
    args = ['convert', hasChild, '-flop', hasParent]
    logger.debug(args)
    subprocess.check_call(args)
