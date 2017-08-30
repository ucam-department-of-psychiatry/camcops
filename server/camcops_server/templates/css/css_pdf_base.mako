## css_pdf_base.mako
<%page args="paged_media: bool"/>

<%doc>

Hard page margins for A4:

- left/right: most printers can cope; hole punches to e.g. 13 mm; so 20mm
  reasonable.
- top: HP Laserjet 1100 e.g. clips at about 17.5mm
- bottom: HP Laserjet 1100 e.g. clips at about 15mm
... so 20mm all round about right

</%doc>

<%namespace file="def_css_constants.mako" import="argstring, pdf_args"/>
<%include
    file="css_base.mako"
    args="${argstring(pdf_args(paged_media=paged_media))}"
    />
