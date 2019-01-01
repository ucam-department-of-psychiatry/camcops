## view_user_email_addresses.mako
<%inherit file="base_web.mako"/>
<%namespace file="displayfunc.mako" import="one_per_line"/>

<%!
from markupsafe import escape
from camcops_server.cc_modules.cc_pyramid import Routes, ViewArg, ViewParam
%>

<%include file="db_user_info.mako" args="offer_main_menu=True"/>

<h1>Users’ e-mail addresses</h1>

<h2>Users that you manage who have missing e-mail addresses</h2>
<ul>
    %for user in query:
        %if not user.email:
            <li>${ user.username }</li>
        %endif
    %endfor
</ul>

<h2>E-mail addresses for users that you manage</h2>
<ul>
    <li>Click one to e-mail that user using your computer's e-mail client.</li>
    <li>Copy/paste the whole list into your e-mail client for a bulk e-mail.</li>
</ul>
<p>
%for user in query:
    %if user.email:
        <a href="mailto:${ user.email }">${ (user.fullname or user.username) } &lt;${ user.email }&gt;</a><br>
    %endif
%endfor
</p>

<!-- There is no general way to do a "mailto:" link for multiple recipients;
see https://stackoverflow.com/questions/13765286/send-mail-to-multiple-receiver-with-html-mailto -->
