## offer_terms.mako
<%inherit file="base_web.mako"/>

<%include file="db_user_info.mako"/>

<h1>${title}</h1>

<h2>${subtitle}</h2>

<p>${content}</p>

${form}


    html = pls.WEBSTART + """
        {user}
        <h1>{title}</h1>
        <h2>{subtitle}</h2>
        <p>{content}</p>
        <form name="myform" action="{script}" method="POST">
            <input type="hidden" name="{PARAM.ACTION}"
                    value="{ACTION.AGREE_TERMS}">
            <input type="submit" value="{agree}">
        </form>
    """.format(
        user=session.get_current_user_html(),
        title=req.wappstring("disclaimer_title"),
        subtitle=req.wappstring("disclaimer_subtitle"),
        content=req.wappstring("disclaimer_content"),
        script=pls.SCRIPT_NAME,
        PARAM=PARAM,
        ACTION=ACTION,
        agree=req.wappstring("disclaimer_agree"),
    ) + WEBEND
    return html