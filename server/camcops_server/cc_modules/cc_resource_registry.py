from deform.widget import ResourceRegistry


class CamcopsResourceRegistry(ResourceRegistry):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_js_resources(
            "jsoneditor", None,
            "camcops_server.static:jsoneditor/jsoneditor.min.js"
        )

        self.set_css_resources(
            "jsoneditor",
            None,
            "camcops_server.static:jsoneditor/jsoneditor.min.css",
            "camcops_server.static:jsoneditor/jsonwidget.css"
        )
