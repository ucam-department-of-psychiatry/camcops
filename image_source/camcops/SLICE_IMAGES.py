#!/usr/bin/env python

"""
===============================================================================
OLD METHOD: PNG export
===============================================================================
from Illustrator:
1. small logo layer:   Save for Web > Image Size > width 1200, height 1200
    > Apply > Save > appicon_source.png
2. splashscreen layer: Save for Web > Image Size > width 1200, height 1200
    > Apply > Save > splashscreen_source.png
(3. PDF icon layer: Save for Web > Image Size > width 1000, height auto >
    Apply > Save > logo_camcops.png ... thence to website)
(4. PDF icon layer: Save for Web > Image Size > width 1000, height auto >
    Apply > Save > logo_local.png ... thence to website)

===============================================================================
OLD: Illustrator slicing technique
===============================================================================

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

===============================================================================
NEW METHOD: slice up PDFs
===============================================================================

For 1024x1024 DefaultIcon.png, which is getting too big for Illustrator's
export when you have it as the centre ninth:
  - Make a 30x30mm new artboard
  - Paste the art in
  - Save it as camcops_appicon.pdf
  - Then run this script.

2015-01-21: If you make DefaultIcon.png, Titanium makes icons of the right
size, but fails to keep the background transparent. So we make them
manually.

===============================================================================
ImageMagick 6.9.7 crash (observed 2019-03-18)
===============================================================================

- "not authorized" error from ImageMagick's ``identify`` tool:

  - edit ``/etc/ImageMagick-6/policy.xml`` and replace

    .. code-block:: xml

        <policy domain="coder" rights="none" pattern="PDF" />

    with

    .. code-block:: xml

        <policy domain="coder" rights="read|write" pattern="PDF" />

    as per
    https://alexvanderbist.com/posts/2018/fixing-imagick-error-unauthorized.

- "cache resources exhausted" error from ImageMagick's ``convert`` tool:

  - edit ``/etc/ImageMagick-6/policy.xml`` and replace

    .. code-block:: xml

        <policy domain="resource" name="memory" value="256MB"/>
        <policy domain="resource" name="area" value="128MB"/>

    with

    .. code-block:: xml

        <policy domain="resource" name="memory" value="1GiB"/>
        <policy domain="resource" name="area" value="1GiB"/>

    or similar (the "area" bit may be unimportant; the "memory" bit mattered),
    as per https://github.com/ImageMagick/ImageMagick/issues/396.

    As of ImageMagick 6.9.11-60, the units for "area" are more clearly pixels,
    not bytes; therefore can e.g. replace "128MP" with "1GP" here; see e.g.
    - https://bugs.launchpad.net/ubuntu/+source/imagemagick/+bug/1910980
    - https://www.imagemagick.org/source/policy-open.xml

"""

import argparse
import logging
import os
from os.path import join
import platform
import shutil
import subprocess

import tempfile
from typing import List, Optional, Tuple

from cardinal_pythonlib.logs import main_only_quicksetup_rootlogger
from rich_argparse import RichHelpFormatter

log = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

WINDOWS = platform.system() == "Windows"

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_BASE_DIR = os.path.abspath(join(THIS_DIR, os.pardir, os.pardir))

APPICON_PDF = join(THIS_DIR, "camcops_appicon.pdf")
SPLASHSCREEN_PDF = join(THIS_DIR, "camcops_splashscreens.pdf")
CAMCOPS_LOGO_PDF = join(THIS_DIR, "camcops_logo.pdf")
BLANK_LOGO_PDF = join(THIS_DIR, "blank_institution_logo.pdf")
TABLET_ICON_PDF = join(THIS_DIR, "camcops_icons.pdf")
SERVER_DIAGRAM_PDF = join(THIS_DIR, "camcops_server_diagram.pdf")
SCALING_LOGOS_PDF = join(THIS_DIR, "camcops_scaling_logos.pdf")

CONVERT = ["magick", "convert"] if WINDOWS else ["convert"]
GHOSTSCRIPT_WINDOWS = "gswin32c.exe"
GREP = ["grep"]
IDENTIFY = ["magick", "identify"] if WINDOWS else ["identify"]


# =============================================================================
# Support functions
# =============================================================================


def require(executable: str) -> None:
    """
    Require than an executable exist on the path, or raise RuntimeError.
    """
    if not shutil.which(executable):
        raise RuntimeError("Missing executable: " + repr(executable))


def run(args: List[str]) -> None:
    """
    Run an external command and raise CalledProcessError if it fails.
    """
    log.debug(f"Running command: {args!r}")
    try:
        subprocess.check_call(args)
    except subprocess.CalledProcessError:
        log.critical(f"Command failed: {args!r}")
        raise


def mkdirp(path: str) -> None:
    """
    Create a directory without complaining.
    """
    os.makedirs(path, exist_ok=True)


def get_pdf_print_size_inches(
    filename: str, autocrop: bool = False, verbose: bool = False
) -> Tuple[float, float]:
    """
    Return the print size of a PDF in inches.

    Args:
        filename:
            Filename of the PDF.
        autocrop:
            Remove borders?
        verbose:
            Be verbose?

    Returns:
        width, height
    """
    if autocrop:
        # Create a temporary, trimmed, PDF, and measure that instead.
        fd, tmpfname = tempfile.mkstemp(".pdf")
        os.close(fd)
        # noinspection PyPep8
        try:
            log.debug("Measuring autocropped PDF")
            args = CONVERT.copy()
            if verbose:
                args += ["-verbose"]
            args += ["-trim", filename, "+repage", tmpfname]
            # Note that the output PDF is rasterized, not vector
            run(args)
            return get_pdf_print_size_inches(
                tmpfname, autocrop=False, verbose=verbose
            )
        except Exception:
            raise
        finally:
            os.remove(tmpfname)
    p1args = IDENTIFY + ["-verbose", filename]
    p1 = subprocess.Popen(p1args, stdout=subprocess.PIPE)
    p2args = GREP + ["Print size: "]
    p2 = subprocess.Popen(p2args, stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    output = p2.communicate()[0].decode("utf-8").strip()
    # ... looks like "Print size: 1.18056x1.18056"
    try:
        info = output.split()[2]
    except Exception:
        log.critical(f"p1args: {p1args!r}")
        log.critical(f"p2args: {p2args!r}")
        log.critical(f"output: {output!r}")
        log.warning(
            "If the error is 'not authorized' from ImageMagick's "
            "identify tool, see source code"
        )
        raise
    width, height = info.split("x")
    return float(width), float(height)


class ProportionPair(object):
    """
    Represents a pair of proportions (a, b), such that both are in the range
    [0, 1] and a < b.
    """

    def __init__(self, a: float, b: float) -> None:
        self.a = a
        self.b = b

    def __repr__(self) -> str:
        return f"<ProportionPair({self.a}, {self.b})>"

    def is_valid(self) -> bool:
        return (
            0.0 <= self.a <= 1.0 and 0.0 <= self.b <= 1.0 and self.a < self.b
        )

    def validate(self) -> None:
        if not self.is_valid():
            raise AssertionError(f"ProportionPair failed validation: {self}")

    @property
    def span(self) -> float:
        """
        Returns the fraction between a and b.
        """
        return self.b - self.a

    def __mul__(self, other: "ProportionPair") -> "ProportionPair":
        """
        Returns the ProportionPair of "other" within "self".

        The resulting span is commutative, but the starting point is not;
        consider e.g.

        .. code-block:: python
            x = ProportionPair(0.1, 0.5)
            y = ProportionPair(0.6, 0.9)
            x * y  # span 0.12 but approx. (0.34, 0.46)
            y * x  # span 0.12 but approx. (0.63, 0.75)
        """
        w = self.span
        return ProportionPair(self.a + other.a * w, self.a + other.b * w)


def crop_pdf(
    src_filename: str,
    dest_filename: str,
    dest_width_px: int = None,
    dest_height_px: int = None,
    autocrop: bool = False,
    active_lr: ProportionPair = None,
    active_tb: ProportionPair = None,
    img_lr: ProportionPair = None,
    img_tb: ProportionPair = None,
    density_dpi: int = None,
    density_default_multiplier: int = 2,
    transparent: str = None,
    windows_multires_icon: bool = False,
    verbose: bool = False,
) -> None:
    """
    Takes a chunk out of a PDF, and saves it as an image.

    Args:
        src_filename:
            The filename of the source PDF.
        dest_filename:
            The filename of the destination image.
        dest_width_px:
            The width of the destination image.
        dest_height_px:
            The height of the destination image.
        autocrop:
            Automatically remove blank borders.
        active_lr:
            Left/right fraction pair describing active region within source
            image, e.g. (0, 1). Typically used to remove margins.
        active_tb:
            Top/bottom fraction pair describing active region within source
            image, e.g. (0, 1). Typically used to remove margins.
        img_lr:
            Left/right fraction pair describing source image within source
            active region, e.g. (1/3, 2/3).
        img_tb:
            Top/bottom fraction pair describing source image within source
            active region, e.g. (1/3, 2/3).
        density_dpi:
            Working density (dots per inch). Will be autocalculated if not
            specified.
        density_default_multiplier:
            When autocalculating density, multiply up by around this amount,
            to avoid loss of detail.
        transparent:
            Colour to change to transparent, as per
            https://www.imagemagick.org/script/command-line-options.php#fill.
        windows_multires_icon:
            Create an icon for Windows that has multiple resolutions embedded
            in one file?
        verbose:
            Be verbose?
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
    log.debug("Starting point: left=0, right=1; top=0, bottom=1")
    log.debug(
        f"After removing margins: left={active_lr.a}, right={active_lr.b}; "
        f"top={active_tb.a}, bottom={active_tb.b}"
    )
    log.debug(
        f"With what's left, take image: left={img_lr.a}, right={img_lr.b}; "
        f"top={img_tb.a}, bottom={img_tb.b}"
    )
    log.debug(
        f"Final image to be taken: "
        f"left={final_img_lr.a}, right={final_img_lr.b}; "
        f"top={final_img_tb.a}, bottom={final_img_tb.b}"
    )

    # The PDF knows its physical size (and notional density, which we
    # don't care about). ImageMagick will convert it to a different
    # density for us, at which point we can refer to it in terms of pixels.
    # First, we get its size.
    (src_width_inches, src_height_inches) = get_pdf_print_size_inches(
        src_filename, autocrop, verbose=verbose
    )
    log.debug(
        f"Source PDF size: {src_width_inches} inches W x "
        f"{src_height_inches} inches H"
    )

    img_aspect_ratio = (final_img_lr.span * src_width_inches) / (
        final_img_tb.span * src_height_inches
    )

    # Infer width or height from aspect ratio?
    if dest_width_px is None:
        dest_width_px = round(img_aspect_ratio * dest_height_px)
        log.debug(
            f"Autocalculating: dest_width_px"
            f" = img_aspect_ratio * dest_height_px"
            f" = {img_aspect_ratio} * {dest_height_px}"
            f" = {dest_width_px}"
        )
    elif dest_height_px is None:
        dest_height_px = round(dest_width_px / img_aspect_ratio)
        log.debug(
            f"Autocalculating: dest_height_px"
            f" = dest_width_px / img_aspect_ratio"
            f" = {dest_width_px} / {img_aspect_ratio} = {dest_height_px}"
        )

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
        density_dpi = round(
            density_default_multiplier * max(density_dpi_x, density_dpi_y)
        )

    src_width_px = density_dpi * src_width_inches
    src_height_px = density_dpi * src_height_inches

    # 2. We're taking a chunk out of the middle of the PDF
    img_left_px = round(final_img_lr.a * src_width_px)
    img_right_px = round(final_img_lr.b * src_width_px)
    img_width_px = img_right_px - img_left_px
    img_top_px = round(final_img_tb.a * src_height_px)
    img_bottom_px = round(final_img_tb.b * src_height_px)
    img_height_px = img_bottom_px - img_top_px

    log.info(f"Making {dest_filename} at {dest_width_px} x {dest_height_px}")
    directory = os.path.dirname(dest_filename)
    if directory:
        mkdirp(directory)
    args = CONVERT.copy()
    if verbose:
        args += ["-verbose"]
    if autocrop:
        args.append("-trim")
    args.extend(["-density", str(density_dpi), src_filename])
    if autocrop:
        args.append("+repage")
    if transparent:
        args.extend(["-transparent", transparent])
    args.extend(
        [
            "-crop",
            f"{img_width_px}x{img_height_px}+{img_left_px}+{img_top_px}",
            "+repage",
        ]
    )
    if windows_multires_icon:
        # https://www.imagemagick.org/discourse-server/viewtopic.php?t=26252
        args.extend(["-define", "icon:auto-resize=256,64,48,32,16"])
        # Note that 256x256 icons are stored as PNG (and smaller ones as BMP)
        # within the multi-resolution .ICO file. This seems to be correct; see
        # https://en.wikipedia.org/wiki/ICO_(file_format).
        # (The simplest way to know what's happened is to have Qt Creator build
        # a .RES file, from the .ICO file and a .RC file, and view the .RES
        # [resource] file with Visual Studio.)
        #
        # Can inspect resources in an .EXE file with Resource Hacker;
        # http://www.angusj.com/resourcehacker/#download
        #
        # It all looks fine, and yet the largest icon isn't displayed for the
        # final camcops.exe in Windows. Not sure why.
    else:
        args.extend(
            [
                "-resize",
                f"{dest_width_px}x{dest_height_px}!",
                # ... the ! forces it to ignore aspect ratio:
                #     http://www.imagemagick.org/Usage/resize/
            ]
        )
    args.append(dest_filename)
    run(args)


def tile_pdf(
    src_filename: str,
    dest_filename_format: str,
    n_wide: int,
    n_high: int,
    tile_width_px: int = None,
    tile_height_px: int = None,
    autocrop: bool = True,
    density_multiplier: int = 4,
    transparent: str = None,
    verbose: bool = False,
) -> None:
    """
    Split a PDF into multiple images.

    Args:
        src_filename:
            Source PDF filename.
        dest_filename_format:
            Destination filename format, using "%d" for the file number,
            e.g. "somedir/tile-%d.png".
        n_wide:
            Number of images to slice into, in the width (x) direction.
        n_high:
            Number of images to slice into, in the height (y) direction.
        tile_width_px:
            Width of each tile, in pixels.
        tile_height_px:
            Height of each tile, in pixels.
        autocrop:
            Trim whitespace off the edges first?
        density_multiplier:
            Intermediate filenames have a density that is this factor greater
            than the final image.
        transparent:
            Colour to change to transparent, as per
            https://www.imagemagick.org/script/command-line-options.php#fill.
        verbose:
            Be verbose?
    """
    log.debug(f"Tiling {src_filename} -> {dest_filename_format}")
    if tile_width_px is None and tile_height_px is None:
        raise AssertionError("Must specify width/height/both")

    # Get source size
    (src_width_inches, src_height_inches) = get_pdf_print_size_inches(
        src_filename, autocrop, verbose=verbose
    )
    log.debug(
        f"Source PDF size: {src_width_inches} inches W x "
        f"{src_height_inches} inches H"
    )

    src_tile_width_inches = src_width_inches / n_wide
    src_tile_height_inches = src_height_inches / n_high
    src_tile_aspect_ratio = src_tile_width_inches / src_tile_height_inches
    log.debug(
        f"Source PDF tile size: {src_tile_width_inches} inches W x "
        f"{src_tile_height_inches} inches H "
        f"(aspect ratio {src_tile_aspect_ratio})"
    )

    if tile_width_px is None:
        tile_width_px = round(src_tile_aspect_ratio * tile_height_px)
        log.debug(
            f"Autocalculating: tile_width_px"
            f" = src_tile_aspect_ratio * tile_height_px"
            f" = {src_tile_aspect_ratio} * {tile_height_px}"
            f" = {tile_width_px}"
        )
    elif tile_height_px is None:
        tile_height_px = round(tile_width_px / src_tile_aspect_ratio)
        log.debug(
            f"Autocalculating: tile_height_px"
            f" = tile_width_px / src_tile_aspect_ratio"
            f" = {tile_width_px} / {src_tile_aspect_ratio}"
            f" = {tile_height_px}"
        )

    intermediate_tile_width_px = density_multiplier * tile_width_px
    intermediate_tile_height_px = density_multiplier * tile_height_px

    # Calculate density. No distortion is possible, so this is simple.
    src_width_px = intermediate_tile_width_px * n_wide
    density_dpi = round(src_width_px / src_width_inches)

    # Off we go
    args = CONVERT.copy()
    if verbose:
        args += ["-verbose"]
    if autocrop:
        args.append("-trim")
    args.extend(["-density", str(density_dpi), src_filename])
    if autocrop:
        args.append("+repage")
    if transparent:
        args.extend(["-transparent", transparent])

    # 2017-06-20: getting the error in CamCOPS (Qt):
    #     libpng warning: iCCP: profile 'icc': 0h: PCS illuminant is not D50
    # - https://en.wikipedia.org/wiki/ICC_profile
    # Using "identify -verbose X.png" shows the profile being used by default
    #       icc:copyright: Copyright Artifex Software 2011
    #       icc:description: Artifex Software sRGB ICC Profile
    #       icc:manufacturer: Artifex Software sRGB ICC Profile
    #       icc:model: Artifex Software sRGB ICC Profile
    # Address this with the "-profile" option?
    # Or "-colorspace RGB"?
    # - https://www.imagemagick.org/script/color-management.php
    # - https://www.imagemagick.org/script/command-line-options.php
    args.extend(
        [
            "-set",
            "colorspace",
            "RGB",  # linear RGB, not default sRGB
            "-profile",
            "AdobeRGB1998.icc",
        ]
    )
    # ... works, but must come AFTER the "-transparent" command

    args.extend(
        [
            "-crop",
            f"{intermediate_tile_width_px}x{intermediate_tile_height_px}",
            "+repage",
            "-resize",
            f"{tile_width_px}x{tile_height_px}",
            dest_filename_format,
        ]
    )
    run(args)


def make_appicon(
    filename: str,
    side_px: int,
    windows_multires_icon: bool = False,
    verbose: bool = False,
) -> None:
    # Imagine the source PDF as a 3x3 grid; we want the middle square.
    # Appicons are square.
    crop_pdf(
        src_filename=APPICON_PDF,
        img_lr=ProportionPair(1 / 3, 2 / 3),
        img_tb=ProportionPair(1 / 3, 2 / 3),
        dest_filename=filename,
        dest_width_px=side_px,
        dest_height_px=side_px,
        windows_multires_icon=windows_multires_icon,
        verbose=verbose,
    )


def make_feature_graphic(
    filename: str, width_px: int, height_px: int, verbose: bool = False
) -> None:
    crop_pdf(
        src_filename=SPLASHSCREEN_PDF,
        img_lr=ProportionPair(0.26, 0.74),
        img_tb=ProportionPair(0.4, 0.6),
        dest_filename=filename,
        dest_width_px=width_px,
        dest_height_px=height_px,
        verbose=verbose,
    )


def make_splashscreen(
    filename: str,
    width_px: int,
    height_px: int,
    trim_margin_frac: float = 0.05,
    verbose: bool = False,
) -> None:
    src_width_in, src_height_in = get_pdf_print_size_inches(
        SPLASHSCREEN_PDF, verbose=verbose
    )
    src_aspect_ratio = src_width_in / src_height_in
    dest_aspect_ratio = width_px / height_px
    log.debug(f"source aspect ratio: {src_aspect_ratio}")
    log.debug(f"destination aspect ratio: {dest_aspect_ratio}")
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
        dest_height_px=height_px,
        verbose=verbose,
    )


def main() -> None:
    # http://docs.appcelerator.com/platform/latest/#!/guide/Icons_and_Splash_Screens

    parser = argparse.ArgumentParser(formatter_class=RichHelpFormatter)
    parser.add_argument(
        "--base_dir",
        default=PROJECT_BASE_DIR,
        help=f"Base directory (default: {PROJECT_BASE_DIR})",
    )
    parser.add_argument(
        "--ios", action="store_true", help="Process iOS icons/splashscreens"
    )
    parser.add_argument(
        "--android",
        action="store_true",
        help="Process Android icons/splashscreens",
    )
    parser.add_argument(
        "--googleplay",
        action="store_true",
        help="Process Google Play Store icons/splashscreens",
    )
    parser.add_argument(
        "--windows",
        action="store_true",
        help="Process Windows icons/splashscreens",
    )
    parser.add_argument(
        "--tablet", action="store_true", help="Process tablet in-app icons"
    )
    parser.add_argument(
        "--server", action="store_true", help="Process server logos"
    )
    parser.add_argument(
        "--all", action="store_true", help="Process everything"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose")
    args = parser.parse_args()
    main_only_quicksetup_rootlogger(
        level=logging.DEBUG if args.verbose else logging.INFO
    )

    require(CONVERT[0])
    require(GREP[0])
    require(IDENTIFY[0])
    if WINDOWS:
        require(GHOSTSCRIPT_WINDOWS)

    if args.all:
        args.android = True
        args.googleplay = True
        args.ios = True
        args.server = True
        args.tablet = True
        args.windows = True
    if not any(
        [
            args.android,
            args.googleplay,
            args.ios,
            args.server,
            args.tablet,
            args.windows,
        ]
    ):
        log.warning("No options specified!")
    log.info(f"Using base directory: {args.base_dir}")

    google_play_dir = join(args.base_dir, "working", "google_play_images")

    tablet_icon_dir = join(
        args.base_dir, "tablet_qt", "resources", "camcops", "images"
    )
    android_res_dir = join(
        args.base_dir, "working", "dummy_image_android_res_dir"
    )  # !!!
    android_plt_res = join(args.base_dir, "tablet_qt", "android", "res")
    ios_dir = join(args.base_dir, "working", "dummy_image_ios_dir")  # !!!
    windows_dir = join(args.base_dir, "tablet_qt", "windows")

    server_static_dir = join(args.base_dir, "server", "static")
    web_image_dir = join(args.base_dir, "website", "images")
    docs_image_dir = join(args.base_dir, "docs", "source", "images")
    docs_appicon_image_dir = join(
        args.base_dir, "docs", "source", "_app_icons"
    )
    all_tablet_icon_dirs = [tablet_icon_dir, docs_appicon_image_dir]

    def mk_appicon(
        filename: str, side_px: int, windows_multires_icon: bool = False
    ) -> None:
        make_appicon(
            filename,
            side_px,
            verbose=args.verbose,
            windows_multires_icon=windows_multires_icon,
        )

    def mk_splashscreen(filename: str, width_px: int, height_px: int) -> None:
        make_splashscreen(filename, width_px, height_px, verbose=args.verbose)

    def mk_feature_graphic(
        filename: str, width_px: int, height_px: int
    ) -> None:
        make_feature_graphic(
            filename, width_px, height_px, verbose=args.verbose
        )

    def servercrop(source: str, dest: str, dest_width_px: int) -> None:
        crop_pdf(
            source,
            dest,
            dest_width_px=dest_width_px,
            autocrop=True,
            verbose=args.verbose,
        )

    # =========================================================================
    # iOS
    # =========================================================================

    def ios(filename: str) -> str:
        return join(ios_dir, filename)

    if args.ios:
        log.info("--- iOS")
        mk_appicon(ios("appicon.png"), 57)
        mk_appicon(ios("appicon@2x.png"), 114)
        mk_appicon(ios("appicon-72.png"), 72)
        mk_appicon(ios("appicon-72@2x.png"), 144)
        mk_appicon(ios("appicon-Small-50.png"), 50)
        mk_appicon(ios("appicon-Small-50@2x.png"), 100)
        mk_appicon(ios("appicon-60@2x.png"), 120)
        mk_appicon(ios("appicon-60@3x.png"), 180)
        mk_appicon(ios("appicon-76.png"), 76)
        mk_appicon(ios("appicon-76@2x.png"), 152)
        mk_appicon(ios("appicon-Small-40.png"), 40)
        mk_appicon(ios("appicon-Small-40@2x.png"), 80)
        mk_appicon(ios("appicon-Small-40@3x.png"), 120)
        mk_appicon(ios("appicon-Small.png"), 29)
        mk_appicon(ios("appicon-Small@2x.png"), 58)
        mk_appicon(ios("appicon-Small@3x.png"), 87)

        mk_splashscreen(ios("Default.png"), 320, 480)
        mk_splashscreen(ios("Default@2x.png"), 640, 690)
        mk_splashscreen(ios("Default-568h@2x.png"), 640, 1136)
        mk_splashscreen(ios("Default-667h@2x.png"), 750, 1334)
        mk_splashscreen(ios("Default-Landscape-736h@3x.png"), 2208, 1242)
        mk_splashscreen(ios("Default-Portrait-736h@3x.png"), 1242, 2208)
        mk_splashscreen(ios("Default-Landscape.png"), 1024, 768)
        mk_splashscreen(ios("Default-Portrait.png"), 768, 1024)
        mk_splashscreen(ios("Default-Landscape@2x.png"), 2048, 1536)
        mk_splashscreen(ios("Default-Portrait@2x.png"), 1536, 2048)

        # Artwork for app list in iTunes:
        # iTunesArtwork (no extension), 512 x 512
        # iTunesArtwork@2x (no extension), 1024 x 1024

    # =========================================================================
    # Android
    # =========================================================================

    if args.android:
        log.info("--- Android")
        mk_appicon(join(android_res_dir, "appicon.png"), 128)
        mk_appicon(join(android_plt_res, "drawable-ldpi", "appicon.png"), 36)
        mk_appicon(join(android_plt_res, "drawable-mdpi", "appicon.png"), 48)
        mk_appicon(join(android_plt_res, "drawable-hdpi", "appicon.png"), 72)
        mk_appicon(join(android_plt_res, "drawable-xhdpi", "appicon.png"), 96)
        mk_appicon(
            join(android_plt_res, "drawable-xxhdpi", "appicon.png"), 144
        )

        # There might be better ways. But as a start:
        mk_splashscreen(
            join(android_res_dir, "images", "res-land", "default.png"),
            800,
            480,
        )
        mk_splashscreen(
            join(android_res_dir, "images", "res-port", "default.png"),
            480,
            800,
        )

    if args.googleplay:
        log.info("--- Google Play Store")
        mk_appicon(join(google_play_dir, "hi_res_icon.png"), 512)
        mk_feature_graphic(
            join(google_play_dir, "feature_graphic.png"), 1024, 500
        )
        # ALSO NEED:
        # - 7" tablet screenshot, meaning 1024x600
        # - 10" tablet screenshot, meaning 1280x800
        # Use:
        # - wmctrl -l
        # - wmctrl -i -r ID_FROM_LIST -e 0,100,100,1024,600

    # =========================================================================
    # Windows
    # =========================================================================

    if args.windows:
        log.info("--- Windows")

        # For embedding icons into our .EXE and for all the InnoSetup icons:

        # https://docs.microsoft.com/en-gb/windows/desktop/uxguide/vis-icons
        mk_appicon(
            join(windows_dir, "camcops.ico"), 256, windows_multires_icon=True
        )

        # Potential other things for Windows Store work:

        # mk_appicon(join(windows_dir, "Logo.png"), 150)
        # mk_appicon(join(windows_dir, "SmallLogo.png"), 30)
        # mk_appicon(join(windows_dir, "StoreLogo.png"), 50)
        # mk_appicon(join(windows_dir, "Square150x150Logo.png"), 150)
        # mk_appicon(join(windows_dir, "Square71x71Logo.png"), 71)
        # mk_appicon(join(windows_dir, "Square44x44Logo.png"), 44)

        # mk_splashscreen(join(windows_dir, "SplashScreen.png"), 620, 300)
        # mk_splashscreen(
        #     join(windows_dir, "SplashScreen480x800.png"), 480, 800)
        # mk_splashscreen(
        #     join(windows_dir, "SplashScreen480x800.scale-240.png"),
        #     1152, 1920)

    # =========================================================================
    # Web site, CamCOPS server
    # =========================================================================

    if args.server:
        log.info("--- Server")
        mk_appicon(join(server_static_dir, "favicon_camcops.png"), 32)
        mk_appicon(join(web_image_dir, "camcops.png"), 96)
        mk_appicon(join(web_image_dir, "favicon.png"), 32)
        mk_appicon(join(web_image_dir, "camcops_icon_500.png"), 500)
        mk_appicon(join(docs_image_dir, "camcops_icon_500.png"), 500)
        servercrop(
            CAMCOPS_LOGO_PDF,
            join(server_static_dir, "logo_camcops.png"),
            dest_width_px=1000,
        )
        servercrop(
            BLANK_LOGO_PDF,
            join(server_static_dir, "logo_local.png"),
            dest_width_px=1000,
        )
        servercrop(
            BLANK_LOGO_PDF,
            join(server_static_dir, "logo_local.png"),
            dest_width_px=1000,
        )
        servercrop(
            SERVER_DIAGRAM_PDF,
            join(web_image_dir, "server_diagram.png"),
            dest_width_px=600,
        )
        servercrop(
            SCALING_LOGOS_PDF,
            join(web_image_dir, "scaling_logos.png"),
            dest_width_px=600,
        )

    # =========================================================================
    # Tablet
    # =========================================================================

    """
    If transparency is not working, try:

        identify -verbose FILE.pdf
            # ... is there an alpha channel at all?
        convert FILE.pdf -alpha extract TEMP.png
            # ... does the alpha channel have something in it?

    It proves hard to have my version of Illustrator export a bunch of images
    with transparency in/between them. Not yet achieved. (The edges of the
    page, if any, are transparent, but that's it.)

    Therefore, simpler to get ImageMagick to replace a particular colour with
    transparency. Add a background of an unused colour. Check with:

        convert FILE.pdf -transparent "rgb(240,240,200)" -alpha extract TEMP.png
    """  # noqa

    def row(
        a: Optional[str],
        b: Optional[str],
        c_: Optional[str],
        d: Optional[str],
        e: Optional[str],
        f: Optional[str],
    ) -> list[str]:
        temp = [
            None,
            None,
            a,
            None,
            b,
            None,
            c_,
            None,
            d,
            None,
            e,
            None,
            f,
            None,
        ]
        return [x + ".png" if x is not None else None for x in temp]

    ncol = 14
    nrow = 34
    none_row: list[Optional[str]] = [None] * ncol
    iconmap: list[list[Optional[str]]] = [
        none_row,
        none_row,
        row("finishflag", "spanner", "camcops", "executive", "locked", None),
        none_row,
        row(
            "speaker",
            "treeview",
            "choose_patient",
            "research",
            "unlocked",
            None,
        ),
        none_row,
        row(
            "speaker_playing",
            "service_evaluation",
            "upload",
            "info",
            "back",
            None,
        ),
        none_row,
        row(None, "language", "settings", None, "next", None),
        # ... first column: old "reload"
        # ... fourth column: old "info"
        none_row,
        row("camera", "physical", "global", "patient_summary", "add", None),
        none_row,
        row(
            "radio_selected",
            "dolphin",
            "cognitive",
            "hasChild",
            "cancel",
            None,
        ),
        none_row,
        row(
            "radio_unselected",
            "neurodiversity",
            "affective",
            "clinical",
            "edit",
            None,
        ),
        none_row,
        row("check_true_red", None, "addiction", "anonymous", "delete", None),
        none_row,
        row(
            "check_unselected",
            None,
            "psychosis",
            "check_unselected_required",
            "ok",
            None,
        ),
        none_row,
        row(
            "check_true_black",
            None,
            "catatonia",
            "radio_unselected_required",
            "finish",
            None,
        ),
        none_row,
        row(
            "check_false_black", None, "personality", "stop", "zoom", "magnify"
        ),
        none_row,
        row(
            "check_false_red",
            None,
            "field_incomplete_mandatory",
            "field_problem",
            "privileged",
            None,
        ),
        none_row,
        row(
            "sets_research",
            "sets_clinical",
            None,  # was "alltasks", but neurodiversity symbol too similar
            "warning",
            "time_now",
            "alltasks",  # as of 2024-06-25
        ),
        none_row,
        row(
            "reload",
            None,
            "rotate_clockwise",
            None,
            "rotate_anticlockwise",
            None,
        ),
        none_row,
        row(
            "choose_page",
            None,
            "read_only",
            "field_incomplete_optional",
            "chain",
            "whisker",
        ),
        none_row,
        row(
            "fast_forward",
            None,
            "check_disabled",
            "radio_disabled",
            None,
            None,
        ),
        none_row,
    ]

    if args.tablet:
        log.info("--- Tablet")
        log.info("Slicing icons...")
        for icondir in all_tablet_icon_dirs:
            mkdirp(icondir)
        with tempfile.TemporaryDirectory() as tmpdir:
            tile_pdf(
                TABLET_ICON_PDF,
                join(tmpdir, "tile-%d.png"),
                n_wide=ncol,
                n_high=nrow,
                tile_width_px=96,
                tile_height_px=96,
                autocrop=False,
                transparent="rgb(240,240,200)",
                verbose=args.verbose,
            )
            tilenum = 0
            for r in range(nrow):
                for c in range(ncol):
                    tilename = join(tmpdir, f"tile-{tilenum}.png")
                    propername = iconmap[r][c]
                    if propername is not None:
                        for destdir in all_tablet_icon_dirs:
                            fullpath = join(destdir, propername)
                            log.info(f"Creating {fullpath}")
                            shutil.copy(tilename, fullpath)
                        os.remove(tilename)
                    tilenum += 1

        for destdir in all_tablet_icon_dirs:
            # Special: resize hasChild
            has_child = join(destdir, "hasChild.png")
            log.info("Resizing " + has_child)
            cmdargs = CONVERT + [has_child, "-resize", "24x24", has_child]
            run(cmdargs)

            # Special: make hasParent
            has_parent = join(destdir, "hasParent.png")
            log.info("Making " + has_parent)
            cmdargs = CONVERT + [has_child, "-flop", has_parent]
            run(cmdargs)


if __name__ == "__main__":
    main()
