(function () {
    'use strict'

    const tinymceConfig = document.getElementById("tinymce-config-options");

    async function getCompletions(query) {
        return [];
    }

    tinymce.PluginManager.add('custom_link_input', function (editor, url) {

        const open_dialog = function () {
            let old_search_text = "";
            let old_link_url = "";

            // Stores the current request index, so that outdated requests get ignored
            let ajax_request_id = 0;

            let completion_items = [];
            const dialog_config = {
                title: tinymceConfig.getAttribute("data-link-dialog-title-text"),
                body: {
                    type: "panel",
                    items: [
                        {
                            type: "input",
                            name: "url",
                            label: tinymceConfig.getAttribute("data-link-dialog-url-text")
                        },
                        {
                            type: "input",
                            name: "text",
                            label: tinymceConfig.getAttribute("data-link-dialog-text-text")
                        },
                        {
                            type: "label",
                            label: tinymceConfig.getAttribute("data-link-dialog-internal_link-text"),
                            items: [
                                {
                                    type: "input",
                                    name: "search",
                                },
                                {
                                    type: "selectbox",
                                    name: "completions",
                                    items: completion_items
                                }
                            ]
                        }
                    ]
                },
                buttons: [
                    {
                        type: "cancel",
                        text: tinymceConfig.getAttribute("data-dialog-cancel-text")
                    },
                    {
                        type: "submit",
                        name: "submit",
                        text: tinymceConfig.getAttribute("data-dialog-submit-text"),
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

                    // Otherwise tinymce will append the url to the current page url
                    if (url.toLowerCase().startsWith("www.")) {
                        url = "https://" + url;
                    }

                    if (data.url.trim() == "") {
                        return;
                    }
                    editor.insertContent(`<a href=${url}>${text}</a>`);
                    api.close();
                },
                onChange: function (api) {
                    let data = api.getData();
                    // Automatically update the text button to the url by default
                    if (data.url != data.text && old_link_url == data.text) {
                        api.setData({ text: data.url });
                    }
                    old_link_url = data.url;

                    // Disable the submit button if either of url and text are empty
                    data = api.getData();
                    if (data.url.trim() && data.text.trim()) {
                        api.enable("submit");
                    } else {
                        api.disable("submit");
                    }

                    if (data.search != old_search_text) {
                        getCompletions(data.search).then((completions) => {
                            console.log("Got: ", completions);
                            completion_items.push({"text": "text", "value": "value"});

                            // It seems like there is no better way to update the completion list 
                            api.redial(dialog_config);
                            api.setData(data);
                            api.focus("search");
                        });
                    }
                    old_search_text = data.search;
                }
            };

            return editor.windowManager.open(dialog_config);
        };

        editor.ui.registry.addMenuItem('add_link', {
            text: tinymceConfig.getAttribute("data-link-add-text"),
            onAction: open_dialog,
        });

        return {};
    })
})();