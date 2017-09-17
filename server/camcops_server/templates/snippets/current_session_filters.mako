## current_session_filters.mako

<%
    ccsession = request.camcops_session
    some_filter = False
%>

<div class="filters">
    %if ccsession.filter_surname:
        Surname = <b>${ ccsession.filter_surname | h }</b>.
        <% some_filter = True %>
    %endif
    %if ccsession.filter_forename:
        Forename = <b>${ ccsession.filter_forename | h }</b>.
        <% some_filter = True %>
    %endif
    %if ccsession.filter_dob:
        DOB = <b>${ format_datetime(ccsession.filter_dob, DateFormat.SHORT_DATE )}</b>.
        <% some_filter = True %>
    %endif
    %if ccsession.filter_sex:
        Sex = <b>${ ccsession.filter_sex }</b>.
        <% some_filter = True %>
    %endif
    %if ccsession.filter_task:
        Task = <b>${ ccsession.filter_task }</b>.
        <% some_filter = True %>
    %endif
    %if ccsession.filter_complete:
        <b>Complete tasks only.</b>
        <% some_filter = True %>
    %endif
    %if ccsession.filter_device:
        Device ID = <b>${ ccsession.filter_device.name }</b>.
        <% some_filter = True %>
    %endif
    %if ccsession.filter_user:
        Adding user = <b>${ ccsession.filter_user.username }</b>.
        <% some_filter = True %>
    %endif
    %if ccsession.filter_start_datetime:
        Created <b>&ge; ${ ccsession.filter_start_datetime }</b>.
        <% some_filter = True %>
    %endif
    %if ccsession.filter_end_datetime:
        Created <b>&le; ${ ccsession.filter_end_datetime }</b>.
        <% some_filter = True %>
    %endif
    %if ccsession.filter_text:
        Text contains: <b>${ repr(ccsession.filter_text) | h }</b>.
        <% some_filter = True %>
    %endif
    %if ccsession.filter_idnums:
        ID numbers match one of:
        ${ ("; ".join("{which} = <b>{value}</b>".format(
                which=request.config.get_id_shortdesc(iddef.which_idnum),
                value=iddef.idnum_value,
            ) for iddef in ccsession.filter_idnums) + ".") }
        <% some_filter = True %>
    %endif

    %if not some_filter:
        [No filters.]
    %endif
</div>
