## def_pdf_constants.mako

<%!

def argstring(d):
    return ", ".join("{k}={v}".format(k=k, v=repr(v)) for k, v in d.items())

def web_args():
    return dict(
        MAINFONTSIZE='medium',
        SMALLGAP='2px',
        ELEMENTGAP='5px',
        NORMALPAD='2px',
        TABLEPAD='2px',
        INDENT_NORMAL='20px',
        INDENT_LARGE='75px',
        THINLINE='1px',
        ZERO='0px',
        PDFEXTRA='',
        MAINMARGIN='10px',
        BODYPADDING='5px',
        BANNER_PADDING='25px',
    )


def pdf_args(paged_media=False):
    return dict(
        MAINFONTSIZE='10pt',
        SMALLGAP='0.2mm',
        ELEMENTGAP='1mm',
        NORMALPAD='0.5mm',
        TABLEPAD='0.5mm',
        INDENT_NORMAL='5mm',
        INDENT_LARGE='10mm',
        THINLINE='0.2mm',
        ZERO='0mm',
        MAINMARGIN='2cm',
        BODYPADDING='0mm',
        BANNER_PADDING='0.5cm',

        PDF_LOGO_HEIGHT='20mm',
        paged_media=paged_media,
    )


%>


</%def>
