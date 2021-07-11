import { getCsrfToken } from "../../utils/csrf-token";

(function () {
    'use strict'

    const tinymceConfig = document.getElementById("tinymce-config-options");

    async function getCompletions(query, id) {
        const url = tinymceConfig.getAttribute("data-link-ajax-url");
        const response = await fetch(url, {
            method: "POST",
            headers: {
                "X-CSRFToken": getCsrfToken(),
            },
            body: JSON.stringify({
                query_string: query
            })
        });
        if (response.status != 200) {
            return [];
        }

        const data = await response.json();
        return [data.data, id];
    }

    // Ask if the user wants to append https if that prefix is likely missing
    function checkUrlHttps(editor, url, handler) {
        if (url.toLowerCase().startsWith("www.")) {
            editor.windowManager.confirm(tinymceConfig.getAttribute("data-link-dialog-confirm_https-text"), function (s) {
                if (s)
                    handler("https://" + url);
                else {
                    handler(url);
                }
            });
        } else {
            handler(url);
        }
    }

    function updateLink(editor, anchorElm, text, linkAttrs) {
        anchorElm.textContent = text;

        editor.dom.setAttribs(anchorElm, linkAttrs);
        editor.selection.select(anchorElm);
    };


    tinymce.PluginManager.add('custom_link_input', function (editor, _url) {
        function isAnchor(node) {
            return node.nodeName.toLowerCase() === 'a' && node.href;
        }
        function getAnchor() {
            var node = editor.selection.getNode();
            return isAnchor(node) ? node : null;
        };

        const openDialog = function () {
            let prev_search_text = "";
            let prev_link_url = "";
            let prev_selected_completion = "";

            // Store the custom user url separately, so that it can be restored when required
            let user_url = "";

            // Stores the current request id, so that outdated requests get ignored
            let ajax_request_id = 0;
            let completion_items = [];

            function updateDialog(api) {
                let data = api.getData();

                // Set the url either to the selected internal link or to the user link
                if (prev_selected_completion != data.completions) {
                    if (data.completions != "") {
                        api.setData({ url: data.completions });
                    } else {
                        // restore the original user url
                        api.setData({ url: user_url });
                    }
                }
                prev_selected_completion = data.completions;

                // Automatically update the text input to the url by default
                data = api.getData();
                if (data.url != data.text && prev_link_url == data.text) {
                    api.setData({ text: data.url });
                }
                prev_link_url = data.url;

                // Update the user link
                if (data.url != data.completions) {
                    user_url = data.url;
                }

                // Disable the submit button if either of url and text are empty
                data = api.getData();
                if (data.url.trim() && data.text.trim()) {
                    api.enable("submit");
                } else {
                    api.disable("submit");
                }

                // make ajax new ajax request on user input
                if (data.search != prev_search_text && data.search != "") {
                    ajax_request_id += 1;
                    getCompletions(data.search, ajax_request_id).then(([new_completions, request_id]) => {
                        if (request_id != ajax_request_id) return;

                        completion_items.length = 0;
                        for (const completion of new_completions) {
                            completion_items.push({
                                text: completion.title,
                                value: completion.url,
                            });
                        }

                        // It seems like there is no better way to update the completion list 
                        api.redial(dialog_config);
                        api.setData(data);
                        api.focus("search");
                        prev_search_text = data.search;
                        updateDialog(api);
                    });
                } else if (data.search == "" && prev_search_text != "") {
                    // force an update so that the original user url can get restored
                    completion_items.length = 0;
                    api.redial(dialog_config);
                    api.setData(data);
                    api.focus("search");
                    prev_search_text = data.search;
                    updateDialog(api);
                }
            }

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
                    text: getAnchor() ? getAnchor().innerText : editor.selection.getContent({ format: "text" }),
                    url: editor.selection.getStart().getAttribute("href") || ""
                },
                onSubmit: function (api) {
                    const data = api.getData();

                    let url = data.url;
                    const text = data.text || url;

                    if (data.url.trim() == "") {
                        return;
                    }
                    api.close();

                    checkUrlHttps(editor, url, (real_url) => {
                        // Either insert a new link or update the existing one
                        let anchor = getAnchor();
                        if (!anchor) {
                            editor.insertContent(`<a href=${real_url}>${text}</a>`)
                        } else {
                            updateLink(editor, anchor, text, {'href': real_url});
                            anchor.textContent = text;
                            // anchor.setAttribute('href', real_url);
                            // // I am not sure why the editor uses this data-mce-href attribute, but it seems to be
                            // // required.
                            // anchor.setAttribute('data-mce-href', real_url);

                        }
                    });
                },
                onChange: updateDialog
            };

            return editor.windowManager.open(dialog_config);
        };

        editor.addShortcut("Meta+K", tinymceConfig.getAttribute("data-link-menu-text"), openDialog);

        editor.ui.registry.addMenuItem('add_link', {
            text: tinymceConfig.getAttribute("data-link-menu-text"),
            icon: "link",
            shortcut: "Meta+K",
            onAction: openDialog,
        });

        // This form opens when a link is current selected with the cursor
        editor.ui.registry.addContextForm("link_context_form", {
            predicate: isAnchor,
            initValue: function () {
                var elm = getAnchor();
                return !!elm ? elm.href : '';
            },
            position: "node",
            commands: [
                {
                    type: 'contextformbutton',
                    icon: "link",
                    tooltip: tinymceConfig.getAttribute("data-update-text"),
                    primary: true,
                    onSetup: function (buttonApi) {
                        let nodeChangeHandler = function () {
                            buttonApi.setDisabled(editor.readonly);
                        };
                        editor.on('nodechange', nodeChangeHandler);
                        return function () {
                            editor.off('nodechange', nodeChangeHandler);
                        }
                    },
                    onAction: (formApi) => {
                        let url = formApi.getValue();
                        checkUrlHttps(editor, url, (real_url) => {
                            let anchor = getAnchor();
                            updateLink(editor, anchor, anchor.innerText, {'href': real_url});
                            formApi.hide();
                        });

                    }
                },
                {
                    type: 'contextformbutton',
                    icon: 'unlink',
                    tooltip: tinymceConfig.getAttribute("data-link-remove-text"),
                    active: false,
                    onAction: (formApi) => {
                        let elm = getAnchor();
                        if (!!elm) {
                            elm.replaceWith(elm.innerHTML)
                        }
                        formApi.hide();
                    }
                },
                {
                    type: 'contextformbutton',
                    icon: 'new-tab',
                    tooltip: tinymceConfig.getAttribute("data-link-open-text"),
                    active: false,
                    onAction: (formApi) => {
                        let elm = getAnchor();
                        if (!!elm) {
                            window.open(elm.getAttribute('href'), '_blank');
                        }
                    }
                }
            ]
        });

        return {};
    })
})();