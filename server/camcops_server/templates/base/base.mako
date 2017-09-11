## base.mako

<!DOCTYPE html> <!-- HTML 5 -->
<html>
    <head>
        <%block name="head">
            <%block name="title">
                <title>CamCOPS</title>
            </%block>
            <meta charset="utf-8">
            <%block name="extra_head_start"></%block>
            <link rel="icon" type="image/png" href="${request.url_camcops_favicon}">
            <script>
                /* set "html.svg" if our browser supports SVG */
                if (document.implementation.hasFeature(
                        "http://www.w3.org/TR/SVG11/feature#Image", "1.1")) {
                    document.documentElement.className = "svg";
                }
            </script>
            <style type="text/css">
                <%block name="css"></%block>
            </style>
            <%block name="extra_head_end"></%block>
        </%block>
    </head>
    <body <%block name="body_tags"></%block>>
        <%block name="header_block"></%block>
        <%block name="footer_block"></%block>
        ## ... for CSS paged media
        <%block name="logo"></%block>

        ${next.body()}

        <%block name="body_end"></%block>
    </body>
</html>
