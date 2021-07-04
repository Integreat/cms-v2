// import { default as tinymce } from "tinymce";

(function () {
    'use strict'


    tinymce.PluginManager.add('custom_link_input', function (editor, url) {
        
        const open_dialog = function () {
            let old_link_text = "";
            let old_link_url = "";
            
            return editor.windowManager.open({
                title: "Open Link (Translate)",
                body: {
                    type: "panel",
                    items: [
                        {
                            type: "input",
                            name: "url",
                            label: "URL (Translate)"
                        },
                        {
                            type: "input",
                            name: "text",
                            label: "Text to show (Translate)",
                        }
                    ]
                },
                buttons: [
                    {
                        type: "cancel",
                        text: "Close (Translate)"
                    },
                    {
                        type: "submit",
                        name: "submit",
                        text: "Insert (Translate)",
                        primary: true,
                        disabled: true
                    },
                ],
                initialData: {
                    text: editor.selection.getContent()
                },
                onSubmit: function (api) {
                    const data = api.getData();
                    console.log(data);

                    let url = data.url;
                    const text = data.text || url;

                    if (url.toLowerCase().startsWith("www.")) {
                        url = "https://" + url;
                    }
                    
                    if (data.url.trim() == "") {
                        return;
                    }
                    editor.insertContent(`<a href=${url}>${text}</a>`);
                    api.close();
                },
                onChange: function(api) {
                    let data = api.getData();

                    // Automatically update the text button to the url by default
                    if (data.url != data.text && old_link_url == data.text) {
                        api.setData({text: data.url});
                    } 
                    old_link_url = data.url;
                    
                    // Disable the submit button if either of url and text are empty
                    data = api.getData();
                    if (data.url.trim() && data.text.trim()) {
                        api.enable("submit");
                    } else {
                        api.disable("submit");
                    }
                }
            });
        };

        editor.ui.registry.addMenuItem('add_link', {
            text: "Add Link (Translate)",
            onAction: open_dialog,
        });

        return {};
    })
})();