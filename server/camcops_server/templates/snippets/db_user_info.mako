## db_user_info.mako
<%page args="offer_main_menu=False"/>

<div>
    ${request.config.get_database_title_html()}
    %if request.camcops_session.username:
        Logged in as <b>${request.camcops_session.username | h}</b>.
    %endif
    %if offer_main_menu:
        <%include file="to_main_menu.mako"/>
    %endif
</div>
